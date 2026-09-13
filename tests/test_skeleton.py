"""Tests for skeleton context provider in x-connector-extension."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from imperal_sdk.testing import MockContext
from imperal_sdk.testing.mock_secrets import MockSecretStore

import skeleton


def _ctx(jwt: str = "test-jwt") -> MockContext:
    ctx = MockContext(user_id="imp_u_test123")
    ctx.secrets = MockSecretStore({"backend_jwt": jwt} if jwt else {})
    return ctx


@pytest.mark.asyncio
async def test_skeleton_x_config_no_jwt():
    res = await skeleton.skeleton_x_config(_ctx(jwt=""))
    assert res["response"]["configured"] is False
    assert res["response"]["connected"] is False


@pytest.mark.asyncio
async def test_skeleton_x_config_backend_error(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"error": "Backend unreachable"}

    monkeypatch.setattr(skeleton, "call_backend", fake_call)
    res = await skeleton.skeleton_x_config(_ctx())
    assert res["response"]["configured"] is True
    assert res["response"]["connected"] is False


@pytest.mark.asyncio
async def test_skeleton_x_config_connected(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {
            "accounts": [
                {"id": "acc-1", "x_username": "webbee_cloud", "x_display_name": "Webbee"}
            ]
        }

    monkeypatch.setattr(skeleton, "call_backend", fake_call)
    res = await skeleton.skeleton_x_config(_ctx())
    assert res["response"]["configured"] is True
    assert res["response"]["connected"] is True
    assert res["response"]["accounts_count"] == 1
    assert res["response"]["active_username"] == "webbee_cloud"
