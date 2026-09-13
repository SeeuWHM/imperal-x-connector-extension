"""Unit tests for handlers_trends.

MockContext + monkeypatched call_backend.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from imperal_sdk.testing import MockContext
from imperal_sdk.testing.mock_secrets import MockSecretStore

import handlers_trends
from params import TrendsParams


def _ctx() -> MockContext:
    ctx = MockContext(user_id="tenant-abc-123")
    ctx.secrets = MockSecretStore({"backend_jwt": "test-jwt"})
    return ctx


@pytest.mark.asyncio
async def test_get_trends_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/trends"
        assert kw["params"] == {"woeid": 1}
        return {
            "woeid": 1,
            "trends": [{"name": "#Webbee", "post_count": 12345}],
            "cached_at": "2026-07-21T00:00:00Z",
            "x_cost_usd": 0.0,
        }

    monkeypatch.setattr(handlers_trends, "call_backend", fake_call)
    result = await handlers_trends.fn_get_trends(_ctx(), TrendsParams())
    assert result.status == "success"
    assert result.data.x_cost_usd == 0.0


@pytest.mark.asyncio
async def test_get_trends_not_cached_yet(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"error": "Trends for this location not found.", "error_code": "NOT_FOUND"}

    monkeypatch.setattr(handlers_trends, "call_backend", fake_call)
    result = await handlers_trends.fn_get_trends(_ctx(), TrendsParams())
    assert result.status == "error"
