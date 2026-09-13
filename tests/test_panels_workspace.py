"""Tests for the X Connector center workspace panel — Overview, Feed,
Compose, and Trends views.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

import panels_workspace
import panels_feed


def _find(node_dict: dict, node_type: str) -> list[dict]:
    """Depth-first search for all nodes of a given type in a to_dict() tree."""
    found = []
    if node_dict.get("type") == node_type:
        found.append(node_dict)
    props = node_dict.get("props", {})
    candidates = []
    for key in ("children", "items"):
        val = props.get(key)
        if isinstance(val, list):
            candidates.extend(val)
        elif isinstance(val, dict):
            candidates.append(val)
    for key in ("content", "footer", "body"):
        val = props.get(key)
        if isinstance(val, dict):
            candidates.append(val)

    for child in candidates:
        if isinstance(child, dict) and "type" in child:
            found.extend(_find(child, node_type))
    return found


@pytest.mark.asyncio
async def test_workspace_disconnected_shows_empty_state(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"accounts": []}

    monkeypatch.setattr(panels_workspace, "call_backend", fake_call)
    result = await panels_workspace.workspace_panel(object(), view="overview")
    tree = result.to_dict()

    empty_nodes = _find(tree, "Empty")
    assert len(empty_nodes) >= 1
    assert "Connect your X account" in empty_nodes[0]["props"]["message"]


@pytest.mark.asyncio
async def test_workspace_overview_shows_stats_and_profile(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        if "/v1/oauth/accounts" in path:
            return {"accounts": [{"id": "acc-1", "x_username": "elonmusk", "x_display_name": "Elon Musk"}]}
        if "/v1/reads/users/" in path:
            return {
                "user": {
                    "username": "elonmusk",
                    "name": "Elon Musk",
                    "public_metrics": {
                        "followers_count": 150000000,
                        "following_count": 500,
                        "tweet_count": 30000,
                        "listed_count": 120000,
                    },
                }
            }
        return {}

    monkeypatch.setattr(panels_workspace, "call_backend", fake_call)
    result = await panels_workspace.workspace_panel(object(), view="overview")
    tree = result.to_dict()

    stats = _find(tree, "Stat")
    assert len(stats) >= 3
    stat_labels = {s["props"]["label"] for s in stats}
    assert "Followers" in stat_labels
    assert "Following" in stat_labels
    assert "Posts" in stat_labels


@pytest.mark.asyncio
async def test_workspace_feed_renders_posts_and_actions(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        if "/v1/oauth/accounts" in path:
            return {"accounts": [{"id": "acc-1", "x_username": "testuser"}]}
        if "/v1/reads/home-timeline" in path:
            return {
                "posts": [
                    {
                        "id": "123456789",
                        "text": "Hello world from Imperal Cloud!",
                        "author_id": "999",
                        "created_at": "2026-09-13T12:00:00Z",
                        "public_metrics": {
                            "like_count": 42,
                            "retweet_count": 10,
                            "reply_count": 5,
                        },
                    }
                ]
            }
        return {}

    monkeypatch.setattr(panels_workspace, "call_backend", fake_call)
    monkeypatch.setattr(panels_feed, "call_backend", fake_call)
    result = await panels_workspace.workspace_panel(object(), view="feed", subview="home")
    tree = result.to_dict()

    items = _find(tree, "ListItem")
    assert len(items) >= 1
    assert "Hello world" in items[0]["props"]["title"]
    actions = items[0]["props"].get("actions", [])
    labels = {a["label"] for a in actions}
    assert "Like" in labels
    assert "Repost" in labels
    assert "Save" in labels


@pytest.mark.asyncio
async def test_workspace_compose_renders_form(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"accounts": [{"id": "acc-1", "x_username": "testuser"}]}

    monkeypatch.setattr(panels_workspace, "call_backend", fake_call)
    result = await panels_workspace.workspace_panel(object(), view="compose")
    tree = result.to_dict()

    forms = _find(tree, "Form")
    assert len(forms) >= 1
    assert forms[0]["props"]["action"] == "post_tweet"
    textareas = _find(tree, "TextArea")
    assert len(textareas) >= 1
    assert textareas[0]["props"]["param_name"] == "text"


@pytest.mark.asyncio
async def test_workspace_trends_renders_table(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        if "/v1/oauth/accounts" in path:
            return {"accounts": [{"id": "acc-1", "x_username": "testuser"}]}
        if "/v1/trends" in path:
            return {
                "trends": [
                    {"name": "#AI", "tweet_volume": 125000, "url": "https://x.com/search?q=%23AI"},
                    {"name": "#Imperal", "tweet_volume": 45000, "url": "https://x.com/search?q=%23Imperal"},
                ]
            }
        return {}

    monkeypatch.setattr(panels_workspace, "call_backend", fake_call)
    monkeypatch.setattr(panels_feed, "call_backend", fake_call)
    result = await panels_workspace.workspace_panel(object(), view="trends")
    tree = result.to_dict()

    tables = _find(tree, "DataTable")
    assert len(tables) >= 1
    rows = tables[0]["props"]["rows"]
    assert len(rows) == 2
    assert rows[0]["name"] == "#AI"
