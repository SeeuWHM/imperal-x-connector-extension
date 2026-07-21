"""Tests for the X Connector sidebar panel — disconnected/connected/error
states. Mirrors gsc-connector's tests/test_panels.py pattern.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

import panels


def _find(node_dict: dict, node_type: str) -> list[dict]:
    """Depth-first search for all nodes of a given type in a to_dict() tree."""
    found = []
    if node_dict.get("type") == node_type:
        found.append(node_dict)
    props = node_dict.get("props", {})
    children = props.get("children") or props.get("items") or []
    if isinstance(children, dict):
        children = [children]
    for child in children:
        if isinstance(child, dict) and "type" in child:
            found.extend(_find(child, node_type))
    return found


@pytest.mark.asyncio
async def test_sidebar_disconnected_shows_signin_button(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"accounts": []}

    monkeypatch.setattr(panels, "call_backend", fake_call)
    result = await panels.sidebar_panel(object())
    tree = result.to_dict()

    buttons = _find(tree, "Button")
    assert any(b["props"]["label"] == "Sign in with X" for b in buttons)
    signin = next(b for b in buttons if b["props"]["label"] == "Sign in with X")
    assert signin["props"]["on_click"]["function"] == "connect_x_account"


@pytest.mark.asyncio
async def test_sidebar_backend_error_shows_alert_and_signin(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"error": "X Connector backend is not configured on our side yet."}

    monkeypatch.setattr(panels, "call_backend", fake_call)
    result = await panels.sidebar_panel(object())
    tree = result.to_dict()

    alerts = _find(tree, "Alert")
    assert any("not configured" in a["props"]["message"] for a in alerts)
    buttons = _find(tree, "Button")
    assert any(b["props"]["label"] == "Sign in with X" for b in buttons)


@pytest.mark.asyncio
async def test_sidebar_connected_shows_accounts_list(monkeypatch):
    async def fake_call(ctx, method, path, **kw):
        return {"accounts": [
            {"id": "acc-1", "x_user_id": "999", "x_username": "notVallium",
             "x_display_name": "Valentin Scerbacov"},
            {"id": "acc-2", "x_user_id": "111", "x_username": "secondacc",
             "x_display_name": None},
        ]}

    monkeypatch.setattr(panels, "call_backend", fake_call)
    result = await panels.sidebar_panel(object())
    tree = result.to_dict()

    list_items = _find(tree, "ListItem")
    assert len(list_items) == 2
    titles = {li["props"]["title"] for li in list_items}
    assert titles == {"@notVallium", "@secondacc"}

    # Disconnect action wired to disconnect_x_account with the right account_id
    disconnect_targets = {
        li["props"]["actions"][0]["on_click"]["params"]["account_id"]
        for li in list_items
    }
    assert disconnect_targets == {"acc-1", "acc-2"}

    # "Add another account" button always present when connected
    buttons = _find(tree, "Button")
    assert any(b["props"]["label"] == "Add another X account" for b in buttons)


@pytest.mark.asyncio
async def test_sidebar_connected_marks_active_account():
    accounts = [
        {"id": "acc-1", "x_user_id": "999", "x_username": "first"},
        {"id": "acc-2", "x_user_id": "111", "x_username": "second"},
    ]
    items = panels._account_items(accounts, active_id="acc-2")
    badges = {item.props["id"]: item.props.get("badge") for item in items}
    assert badges["acc-2"] is not None
    assert badges["acc-1"] is None
