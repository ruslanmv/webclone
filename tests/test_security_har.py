"""Tests for HAR-based security audit checks."""

import json
from pathlib import Path

from webclone.security.har import audit_har_file


def test_har_audit_flags_free_user_sensitive_api_payload(tmp_path: Path) -> None:
    """A free-user HAR containing answer keys from an API is reported as a failure."""
    har_file = tmp_path / "session.har"
    har_file.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        {
                            "request": {
                                "url": "https://fictional-audit.invalid/api/lunar-vault/MOON-PORTAL-7/manifest"
                            },
                            "response": {
                                "status": 200,
                                "headers": [
                                    {"name": "Cache-Control", "value": "public, max-age=3600"}
                                ],
                                "content": {
                                    "mimeType": "application/json",
                                    "text": '{"answerKey":["A"]}',
                                },
                                "bodySize": 128,
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    report = audit_har_file(har_file, "free_user")

    assert report.passed is False
    assert report.findings[0].role == "free"
    assert report.findings[0].evidence["matched_patterns"] == ["answerKey"]
