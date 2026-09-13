"""Unit tests for handlers_social (follow, unfollow, block, unblock, mute, unmute).

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

import handlers_social
from params import UsernameParams


def _ctx() -> MockContext:
    ctx = MockContext(user_id="tenant-abc-123")
    ctx.secrets = MockSecretStore({"backend_jwt": "test-jwt"})
    return ctx


@pytest.mark.asyncio
async def test_follow_unfollow_block_mute(monkeypatch):
    calls = []

    async def fake_call(ctx, method, path, **kw):
        calls.append((method, path))
        return {"ok": True, "post_id": "target-1", "x_cost_usd": 0.015}

    monkeypatch.setattr(handlers_social, "call_backend", fake_call)
    await handlers_social.fn_follow_user(_ctx(), UsernameParams(username="someone"))
    await handlers_social.fn_unfollow_user(_ctx(), UsernameParams(username="someone"))
    await handlers_social.fn_block_user(_ctx(), UsernameParams(username="someone"))
    await handlers_social.fn_mute_user(_ctx(), UsernameParams(username="someone"))
    assert calls == [
        ("POST", "/v1/users/someone/follow"),
        ("DELETE", "/v1/users/someone/follow"),
        ("POST", "/v1/users/someone/block"),
        ("POST", "/v1/users/someone/mute"),
    ]


@pytest.mark.asyncio
async def test_unblock_and_unmute(monkeypatch):
    calls = []

    async def fake_call(ctx, method, path, **kw):
        calls.append((method, path))
        return {"ok": True, "post_id": "target-1", "x_cost_usd": 0.005}

    monkeypatch.setattr(handlers_social, "call_backend", fake_call)
    r1 = await handlers_social.fn_unblock_user(_ctx(), UsernameParams(username="someone"))
    r2 = await handlers_social.fn_unmute_user(_ctx(), UsernameParams(username="someone"))
    assert calls == [("DELETE", "/v1/users/someone/block"), ("DELETE", "/v1/users/someone/mute")]
    assert r1.status == "success" and r2.status == "success"
