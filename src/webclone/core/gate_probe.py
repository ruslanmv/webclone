"""Detect soft JavaScript-cookie interstitials and recover the required cookie.

Some sites front their public HTML with a tiny stub page that runs JS to set a
static cookie and reload. A non-browser client that does not run JS sees only
the stub. When the cookie value is a literal string constant in the stub, we
can extract it without executing any code and replay it on the next request.

This module is deliberately narrow: anything that branches, computes a value,
calls another endpoint, or otherwise requires real JS execution is rejected.
The caller is expected to fall back to a real browser in those cases.
"""

import re
from dataclasses import dataclass

import aiohttp

from webclone.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_GATE_BODY_BYTES = 4096

# JavaScript allows `var a='x',b='y',c='z';` — three declarations sharing one
# `var` keyword. Match any `identifier='literal'` so comma-lists work too.
_LITERAL_ASSIGN = re.compile(r"""(?:^|[\s,;({])(\w+)\s*=\s*['"]([^'"]+)['"]""")
_COOKIE_ASSIGN = re.compile(
    r"""document\.cookie\s*=\s*(\w+)\s*\+\s*['"]=['"]\s*\+\s*(\w+)"""
)


@dataclass(frozen=True)
class GateProbeResult:
    """Outcome of probing a URL for a static-cookie interstitial."""

    cookies: dict[str, str]
    status_code: int
    evidence: str


def extract_gate_cookies(body: str) -> dict[str, str] | None:
    """Return cookies to set if `body` is a static-cookie JS interstitial.

    Pure-text extraction, no network. Returns None when the body does not
    match the narrow pattern this module supports.
    """
    if len(body) > _MAX_GATE_BODY_BYTES:
        return None
    if "location.reload" not in body or "document.cookie" not in body:
        return None

    constants = dict(_LITERAL_ASSIGN.findall(body))
    cookie_match = _COOKIE_ASSIGN.search(body)
    if not cookie_match:
        return None

    name_var, value_var = cookie_match.group(1), cookie_match.group(2)
    name = constants.get(name_var)
    value = constants.get(value_var)
    if not name or not value:
        return None
    return {name: value}


async def probe_for_gate(
    session: aiohttp.ClientSession,
    url: str,
) -> GateProbeResult | None:
    """Issue one GET and decide whether the response is a static-cookie gate.

    Returns the cookies to set on the session if a gate is found, or None if
    the response looks like real content or like a challenge we cannot solve
    statically.
    """
    try:
        async with session.get(url, allow_redirects=True) as response:
            status = response.status
            body = await response.text(errors="replace")
    except aiohttp.ClientError as exc:
        logger.debug("Gate probe network error for %s: %s", url, exc)
        return None

    if status not in (200, 403, 429):
        return None
    cookies = extract_gate_cookies(body)
    if cookies is None:
        return None

    evidence = body.strip().replace("\n", " ")[:200]
    logger.warning(
        "Static-cookie gate detected on %s (HTTP %s); applying cookies %s",
        url,
        status,
        sorted(cookies),
    )
    return GateProbeResult(
        cookies=cookies,
        status_code=status,
        evidence=evidence,
    )
