"""X Connector sidebar panel — connect prompt when disconnected; connected
X accounts (with switch/disconnect) when connected. Mirrors gsc-connector's
panels.py pattern exactly: same "Add another account" flow via ui.Call on
the OAuth chat function, same account ListItem shape.

X's OAuth is hand-built (not one of the SDK's built-in providers), so
connect_x_account returns {authorize_url, state} instead of the SDK's
{auth_url, instruction} shape used by google/microsoft/yahoo — the platform
still opens whatever URL field the ActionResult carries in a popup, same
UX as every other "Sign in with X" flow on this platform.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
from api_client import call_backend


def _account_items(accounts: list[dict], active_id: str) -> list[ui.UINode]:
    items = []
    for acc in accounts:
        account_id = acc.get("id", "")
        username = acc.get("x_username") or acc.get("x_user_id", "")
        display_name = acc.get("x_display_name") or ""
        is_active = account_id == active_id
        items.append(ui.ListItem(
            id=account_id,
            title=f"@{username}" if username else account_id,
            subtitle=(display_name or ("Active" if is_active else "Connected")),
            avatar=ui.Avatar(fallback=(username[0].upper() if username else "X"), size="sm"),
            badge=ui.Badge("✓", color="green") if is_active else None,
            actions=[{"label": "Disconnect", "icon": "Trash2",
                      "on_click": ui.Call("disconnect_x_account", account_id=account_id)}],
        ))
    return items


def _connect_panel(error: str = "") -> ui.UINode:
    children = [
        ui.Header(text="X Connector", level=4),
        ui.Badge(label="○ not connected", color="gray"),
        ui.Divider(),
        ui.Text(content=(
            "Connect your X (Twitter) account so Webbee can post, reply, like, "
            "retweet, follow and read your timeline on your behalf."
        ), variant="body"),
    ]
    if error:
        children.append(ui.Alert(message=error, type="error"))
    children.append(ui.Stack(direction="h", gap=2, wrap=True, children=[
        ui.Button(label="Sign in with X", icon="Plus", variant="primary",
                  on_click=ui.Call("connect_x_account")),
    ]))
    children.append(ui.Text(
        content="You never see or pay for an X API key — one shared Imperal-owned "
                "X app handles the sign-in, you just authorize it. You can connect "
                "more than one X account and switch between them below.",
        variant="caption",
    ))
    return ui.Stack(children=children)


@ext.panel("sidebar", slot="left", title="X Connector", icon="Twitter",
           refresh="on_event:x-connector.disconnect_x_account")
async def sidebar_panel(ctx):
    data = await call_backend(ctx, "GET", "/v1/oauth/accounts")
    if "error" in data:
        return _connect_panel(error=str(data.get("error", "")))

    accounts = data.get("accounts", [])
    if not accounts:
        return _connect_panel()

    # No separate "active account" concept surfaced by the backend today —
    # every connected account is usable; the most recently connected one
    # (first in the list, backend orders newest-first) is shown as current.
    active_id = accounts[0].get("id", "") if accounts else ""
    account_items = _account_items(accounts, active_id)

    add_account_btn = ui.Button(label="Add another X account", icon="Plus", variant="outline",
                                 on_click=ui.Call("connect_x_account"))

    return ui.Stack(children=[
        ui.Header(text="X Connector", level=4),
        ui.Badge(label="● connected", color="green"),
        ui.Divider(),
        ui.Text(content=f"Accounts ({len(accounts)})", variant="caption"),
        ui.List(items=account_items) if account_items else ui.Empty(message="No accounts"),
        ui.Stack(direction="h", gap=2, wrap=True, children=[add_account_btn]),
        ui.Divider(),
        ui.Text(
            content="Ask Webbee to post, reply, like, retweet, follow or read your "
                    "timeline — no extra setup needed once connected.",
            variant="caption",
        ),
    ])
