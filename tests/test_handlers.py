"""Unit tests — no network. MockContext + monkeypatched call_backend.

Patches `call_backend` on the HANDLER module (where it's imported and used),
never on api_client (where it's merely defined) — patching the wrong one
lets the real function run and hit the network during tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from imperal_sdk.testing import MockContext
from imperal_sdk.testing.mock_secrets import MockSecretStore

import handlers_oauth
import handlers_posts
import handlers_reads
import handlers_trends
from params import (
    AccountIdParams, FollowListParams, ImageUrlParams, ListReadParams, NoParams,
    PostIdParams, PostTweetParams, QuoteParams, ReplyParams, SearchParams,
    ThreadParams, TrendsParams, UsernameParams,
)


def _ctx(configured: bool = True) -> MockContext:
    ctx = MockContext(user_id="tenant-abc-123")
    ctx.secrets = MockSecretStore({"backend_jwt": "test-jwt"} if configured else {})
    return ctx


# ─── oauth ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_connect_x_account_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "GET" and path == "/v1/oauth/authorize"
        return {"authorize_url": "https://x.com/i/oauth2/authorize?...", "state": "signed-state"}

    monkeypatch.setattr(handlers_oauth, "call_backend", fake_call)
    result = await handlers_oauth.fn_connect_x_account(_ctx(), NoParams())
    assert result.status == "success"
    # Response field is auth_url (not authorize_url) — the platform detects
    # this exact name and opens it in a popup, same as Gmail/GSC.
    assert result.data.auth_url.startswith("https://x.com")
    assert result.data.instruction


@pytest.mark.asyncio
async def test_connect_x_account_backend_not_configured(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"error": "X Connector backend is not configured on our side yet — this has been logged.", "_config": True}

    monkeypatch.setattr(handlers_oauth, "call_backend", fake_call)
    result = await handlers_oauth.fn_connect_x_account(_ctx(configured=False), NoParams())
    assert result.status == "error"


@pytest.mark.asyncio
async def test_list_x_accounts_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "GET" and path == "/v1/oauth/accounts"
        return {"accounts": [{"id": "acct-1", "x_user_id": "999", "x_username": "myhandle"}]}

    monkeypatch.setattr(handlers_oauth, "call_backend", fake_call)
    result = await handlers_oauth.fn_list_x_accounts(_ctx(), NoParams())
    assert result.status == "success"
    assert result.data.accounts[0].x_username == "myhandle"


@pytest.mark.asyncio
async def test_disconnect_x_account_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "DELETE" and path == "/v1/oauth/accounts/acct-1"
        return {"disconnected": True, "account_id": "acct-1"}

    monkeypatch.setattr(handlers_oauth, "call_backend", fake_call)
    result = await handlers_oauth.fn_disconnect_x_account(_ctx(), AccountIdParams(account_id="acct-1"))
    assert result.status == "success"
    assert result.data.disconnected is True


# ─── posts (write) ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_tweet_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "POST" and path == "/v1/posts"
        assert kw["json"]["text"] == "hello world"
        return {"id": "tw-1", "text": "hello world", "contains_url": False, "x_cost_usd": 0.015}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    result = await handlers_posts.fn_post_tweet(_ctx(), PostTweetParams(text="hello world"))
    assert result.status == "success"
    assert result.data.id == "tw-1"


@pytest.mark.asyncio
async def test_post_thread_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "POST" and path == "/v1/posts/thread"
        return {"post_ids": ["tw-1", "tw-2"], "count": 2, "x_cost_usd": 0.03}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    result = await handlers_posts.fn_post_thread(_ctx(), ThreadParams(texts=["one", "two"]))
    assert result.status == "success"
    assert result.data.count == 2


@pytest.mark.asyncio
async def test_reply_to_post_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "POST" and path == "/v1/posts/reply"
        return {"id": "tw-2", "text": "reply text", "x_cost_usd": 0.010}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    result = await handlers_posts.fn_reply_to_post(_ctx(), ReplyParams(post_id="tw-1", text="reply text"))
    assert result.status == "success"


@pytest.mark.asyncio
async def test_quote_post_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "POST" and path == "/v1/posts/quote"
        return {"id": "tw-3", "text": "quote text", "contains_url": False, "x_cost_usd": 0.015}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    result = await handlers_posts.fn_quote_post(_ctx(), QuoteParams(post_id="tw-1", text="quote text"))
    assert result.status == "success"


@pytest.mark.asyncio
async def test_delete_post_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "DELETE" and path == "/v1/posts/tw-1"
        return {"ok": True, "post_id": "tw-1", "x_cost_usd": 0.005}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    result = await handlers_posts.fn_delete_post(_ctx(), PostIdParams(post_id="tw-1"))
    assert result.status == "success"


@pytest.mark.asyncio
async def test_like_and_unlike_post(monkeypatch):
    calls = []

    async def fake_call(ctx, method, path, **kw):
        calls.append((method, path))
        return {"ok": True, "post_id": "tw-1", "x_cost_usd": 0.015}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    await handlers_posts.fn_like_post(_ctx(), PostIdParams(post_id="tw-1"))
    await handlers_posts.fn_unlike_post(_ctx(), PostIdParams(post_id="tw-1"))
    assert calls == [("POST", "/v1/posts/tw-1/like"), ("DELETE", "/v1/posts/tw-1/like")]


@pytest.mark.asyncio
async def test_retweet_and_undo(monkeypatch):
    calls = []

    async def fake_call(ctx, method, path, **kw):
        calls.append((method, path))
        return {"ok": True, "post_id": "tw-1", "x_cost_usd": 0.015}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    await handlers_posts.fn_retweet_post(_ctx(), PostIdParams(post_id="tw-1"))
    await handlers_posts.fn_undo_retweet(_ctx(), PostIdParams(post_id="tw-1"))
    assert calls == [("POST", "/v1/posts/tw-1/retweet"), ("DELETE", "/v1/posts/tw-1/retweet")]


@pytest.mark.asyncio
async def test_bookmark_and_remove(monkeypatch):
    calls = []

    async def fake_call(ctx, method, path, **kw):
        calls.append((method, path))
        return {"ok": True, "post_id": "tw-1", "x_cost_usd": 0.015}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    await handlers_posts.fn_bookmark_post(_ctx(), PostIdParams(post_id="tw-1"))
    await handlers_posts.fn_remove_bookmark(_ctx(), PostIdParams(post_id="tw-1"))
    assert calls == [("POST", "/v1/posts/tw-1/bookmark"), ("DELETE", "/v1/posts/tw-1/bookmark")]


@pytest.mark.asyncio
async def test_follow_unfollow_block_mute(monkeypatch):
    calls = []

    async def fake_call(ctx, method, path, **kw):
        calls.append((method, path))
        return {"ok": True, "post_id": "target-1", "x_cost_usd": 0.015}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    await handlers_posts.fn_follow_user(_ctx(), UsernameParams(username="someone"))
    await handlers_posts.fn_unfollow_user(_ctx(), UsernameParams(username="someone"))
    await handlers_posts.fn_block_user(_ctx(), UsernameParams(username="someone"))
    await handlers_posts.fn_mute_user(_ctx(), UsernameParams(username="someone"))
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

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    r1 = await handlers_posts.fn_unblock_user(_ctx(), UsernameParams(username="someone"))
    r2 = await handlers_posts.fn_unmute_user(_ctx(), UsernameParams(username="someone"))
    assert calls == [("DELETE", "/v1/users/someone/block"), ("DELETE", "/v1/users/someone/mute")]
    assert r1.status == "success" and r2.status == "success"


@pytest.mark.asyncio
async def test_upload_image_for_post_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "POST" and path == "/v1/media/upload"
        assert kw["json"]["image_url"] == "https://example.com/pic.png"
        return {"media_id": "media-123", "x_cost_usd": 0.005}

    monkeypatch.setattr(handlers_posts, "call_backend", fake_call)
    result = await handlers_posts.fn_upload_image_for_post(
        _ctx(), ImageUrlParams(image_url="https://example.com/pic.png"))
    assert result.status == "success"
    assert result.data.media_id == "media-123"


# ─── reads ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_home_timeline_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert method == "GET" and path == "/v1/reads/home-timeline"
        assert kw["params"] == {"limit": 20}
        return {"posts": [], "count": 0, "x_cost_usd": 0.0}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    result = await handlers_reads.fn_get_home_timeline(_ctx(), ListReadParams())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_get_mentions_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/reads/mentions"
        return {"posts": [], "count": 0, "x_cost_usd": 0.0}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    result = await handlers_reads.fn_get_mentions(_ctx(), ListReadParams())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_get_my_posts_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/reads/my-posts"
        return {"posts": [], "count": 0, "x_cost_usd": 0.0}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    result = await handlers_reads.fn_get_my_posts(_ctx(), ListReadParams())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_get_bookmarks_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/reads/bookmarks"
        return {"posts": [], "count": 0, "x_cost_usd": 0.0}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    result = await handlers_reads.fn_get_bookmarks(_ctx(), ListReadParams())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_search_posts_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/reads/search"
        assert kw["params"]["query"] == "webbee"
        return {"posts": [], "count": 0, "x_cost_usd": 0.0}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    result = await handlers_reads.fn_search_posts(_ctx(), SearchParams(query="webbee", limit=20))
    assert result.status == "success"


@pytest.mark.asyncio
async def test_get_post_metrics_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/reads/posts/tw-1/metrics"
        return {"id": "tw-1", "like_count": 5, "retweet_count": 1, "reply_count": 0,
                "quote_count": 0, "impression_count": 100, "x_cost_usd": 0.005}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    result = await handlers_reads.fn_get_post_metrics(_ctx(), PostIdParams(post_id="tw-1"))
    assert result.status == "success"
    assert result.data.like_count == 5


@pytest.mark.asyncio
async def test_get_user_profile_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/reads/users/someone"
        return {"id": "u1", "username": "someone", "name": "Someone", "followers_count": 10,
                "following_count": 5, "tweet_count": 20, "verified": False, "x_cost_usd": 0.010}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    result = await handlers_reads.fn_get_user_profile(_ctx(), UsernameParams(username="someone"))
    assert result.status == "success"
    assert result.data.username == "someone"


@pytest.mark.asyncio
async def test_get_followers_and_following(monkeypatch):
    calls = []

    async def fake_call(ctx, method, path, **kw):
        calls.append(path)
        return {"users": [], "count": 0, "x_cost_usd": 0.0}

    monkeypatch.setattr(handlers_reads, "call_backend", fake_call)
    await handlers_reads.fn_get_followers(_ctx(), FollowListParams())
    await handlers_reads.fn_get_following(_ctx(), FollowListParams())
    assert calls == ["/v1/reads/followers", "/v1/reads/following"]


# ─── trends ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_trends_success(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        assert path == "/v1/trends"
        assert kw["params"] == {"woeid": 1}
        return {"woeid": 1, "trends": [{"name": "#Webbee", "post_count": 12345}],
                "cached_at": "2026-07-21T00:00:00Z", "x_cost_usd": 0.0}

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
