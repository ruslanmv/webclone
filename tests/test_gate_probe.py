"""Tests for the static-cookie gate detector."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from webclone.core.gate_probe import probe_for_gate


ACTUAL4TEST_STUB = (
    "<div id='status' style='text-align:center;margin-top:100px;'>Loading...</div>"
    "<script type='text/javascript'>(function(){"
    "var a='891nN82JiKYXG7hx70Pecf9xtsH7RFnM',b='path=/;',c='__ckreal';"
    "setTimeout(function(){"
    "if(navigator.webdriver||window.callPhantom||window._phantom||window.__find){"
    "document.getElementById('status').innerHTML='Please contact the website administrator';return}"
    "document.cookie=c+'='+a+';'+b;location.reload()},600)})();</script>"
)


def _mock_session(status: int, body: str) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.text = AsyncMock(return_value=body)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock()
    session.get = MagicMock(return_value=response)
    return session


@pytest.mark.asyncio
async def test_probe_extracts_static_cookie_from_actual4test_style_stub() -> None:
    session = _mock_session(429, ACTUAL4TEST_STUB)
    result = await probe_for_gate(session, "https://example.invalid/page")
    assert result is not None
    assert result.cookies == {"__ckreal": "891nN82JiKYXG7hx70Pecf9xtsH7RFnM"}
    assert result.status_code == 429


@pytest.mark.asyncio
async def test_probe_ignores_real_content() -> None:
    session = _mock_session(200, "<html><body>" + "x" * 8000 + "</body></html>")
    assert await probe_for_gate(session, "https://example.invalid/page") is None


@pytest.mark.asyncio
async def test_probe_ignores_gate_without_static_constants() -> None:
    dynamic_stub = (
        "<script>setTimeout(function(){"
        "var v=Math.random().toString(36);"
        "document.cookie='token='+v+';path=/';"
        "location.reload()},600);</script>"
    )
    session = _mock_session(429, dynamic_stub)
    assert await probe_for_gate(session, "https://example.invalid/page") is None


@pytest.mark.asyncio
async def test_probe_ignores_non_gate_status_codes() -> None:
    session = _mock_session(500, ACTUAL4TEST_STUB)
    assert await probe_for_gate(session, "https://example.invalid/page") is None
