"""HAR-based API overexposure audit for owned applications."""

import json
from pathlib import Path

from webclone.security.pentest import (
    SENSITIVE_PATTERNS,
    SecurityFinding,
    SecurityReport,
    _json_collection_size,
    normalize_role_name,
)

SENSITIVE_ENDPOINT_HINTS = (
    "/api/",
    "/questions",
    "/answers",
    "/explanations",
    "/export",
    "/print",
    "/download",
    "/view-all",
)


def audit_har_file(har_file: Path, expected_role: str) -> SecurityReport:
    """Inspect an exported DevTools HAR file for API/content overexposure.

    The report records endpoint metadata, matched sensitive marker names, counts,
    and cacheability signals without copying response bodies into the report.
    """
    role = normalize_role_name(expected_role)
    with har_file.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    entries = payload.get("log", {}).get("entries", [])
    report = SecurityReport(base_url="har://local", exam_id=har_file.stem)
    if not isinstance(entries, list):
        report.add(
            SecurityFinding(
                mode="har",
                role=role,
                route=str(har_file),
                passed=False,
                severity="high",
                reason="HAR file does not contain log.entries",
            )
        )
        return report

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {}) if isinstance(entry.get("request"), dict) else {}
        response = entry.get("response", {}) if isinstance(entry.get("response"), dict) else {}
        url = str(request.get("url") or "")
        if not _looks_sensitive_endpoint(url):
            continue

        status = int(response.get("status") or 0)
        content = response.get("content", {}) if isinstance(response.get("content"), dict) else {}
        text = str(content.get("text") or "")
        matched = [pattern for pattern in SENSITIVE_PATTERNS if pattern.lower() in text.lower()]
        collection_size = _json_collection_size(text)
        cache_findings = _cache_findings_from_har(response)
        unauthorized_role = role in {"anonymous", "free", "expired", "suspended"}
        leaked = unauthorized_role and status == 200 and bool(matched)
        overexposed = unauthorized_role and collection_size is not None and collection_size > 50
        passed = not leaked and not overexposed and not cache_findings

        report.add(
            SecurityFinding(
                mode="har",
                role=role,
                route=url,
                status_code=status or None,
                passed=passed,
                severity="critical" if leaked or overexposed else "high",
                reason=(
                    "HAR response contains no unauthorized sensitive markers or risky caching"
                    if passed
                    else "HAR response indicates sensitive data, overlarge payload, or cache risk"
                ),
                evidence={
                    "matched_patterns": matched,
                    "json_collection_size": collection_size,
                    "cache_header_findings": cache_findings,
                    "mime_type": content.get("mimeType"),
                    "encoded_body_size": response.get("bodySize"),
                },
            )
        )

    if not report.findings:
        report.add(
            SecurityFinding(
                mode="har",
                role=role,
                route=str(har_file),
                passed=True,
                severity="info",
                reason="No sensitive API/export/print endpoints were found in HAR",
            )
        )
    return report


def _looks_sensitive_endpoint(url: str) -> bool:
    lowered = url.lower()
    return any(hint in lowered for hint in SENSITIVE_ENDPOINT_HINTS)


def _cache_findings_from_har(response: dict[str, object]) -> list[str]:
    headers = response.get("headers", [])
    normalized: dict[str, str] = {}
    if isinstance(headers, list):
        for header in headers:
            if isinstance(header, dict):
                normalized[str(header.get("name", "")).lower()] = str(
                    header.get("value", "")
                ).lower()

    findings: list[str] = []
    cache_control = normalized.get("cache-control", "")
    if "public" in cache_control:
        findings.append("Cache-Control includes public")
    if "no-store" not in cache_control and "private" not in cache_control:
        findings.append("Cache-Control missing no-store/private")
    if "nosniff" not in normalized.get("x-content-type-options", ""):
        findings.append("X-Content-Type-Options missing nosniff")
    return findings
