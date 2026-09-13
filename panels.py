"""X Connector sidebar panel — connect prompt when disconnected; connected
X accounts (with switch/disconnect) and navigation to the workspace dashboard.

Mirrors canonical Imperal extension layout:
- Fast account status and multi-account switcher
- Quick navigation buttons to open center workspace views (Feed, Compose, Trends)
- Clean responsive layout respecting all SDK conventions.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
from api_client import call_backend


def _account_items(accounts: list[dict], active_id: str) -> list[ui.UINode]:
    items = []
    for acc in accounts:
        connection_id = acc.get("id", "")
        username = acc.get("x_username") or acc.get("x_user_id", "")
        display_name = acc.get("x_display_name") or ""
        is_active = connection_id == active_id
        items.append(ui.ListItem(
            id=connection_id,
            title=f"@{username}" if username else connection_id,
            subtitle=(display_name or ("Active" if is_active else "Connected")),
            avatar=ui.Avatar(fallback=(username[0].upper() if username else "X"), size="sm"),
            badge=ui.Badge("✓", color="green") if is_active else None,
            on_click=ui.Call("__panel__workspace", view="overview"),
            actions=[{"label": "Disconnect", "icon": "Trash2",
                      "on_click": ui.Call("disconnect_x_account", connection_id=connection_id)}],
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

    active_id = accounts[0].get("id", "") if accounts else ""
    account_items = _account_items(accounts, active_id)

    # Quick workspace launchers in sidebar
    workspace_nav = ui.Stack(direction="v", gap=2, children=[
        ui.Button(
            label="Open Dashboard",
            icon="LayoutDashboard",
            variant="primary",
            full_width=True,
            on_click=ui.Call("__panel__workspace", view="overview"),
        ),
        ui.Stack(direction="h", gap=2, wrap=True, children=[
            ui.Button(
                label="Feed",
                icon="MessageSquare",
                variant="secondary",
                size="sm",
                on_click=ui.Call("__panel__workspace", view="feed", subview="home"),
            ),
            ui.Button(
                label="Compose",
                icon="PenTool",
                variant="secondary",
                size="sm",
                on_click=ui.Call("__panel__workspace", view="compose"),
            ),
            ui.Button(
                label="Trends",
                icon="TrendingUp",
                variant="secondary",
                size="sm",
                on_click=ui.Call("__panel__workspace", view="trends"),
            ),
        ]),
    ])

    add_account_btn = ui.Button(label="Add another X account", icon="Plus", variant="outline",
                                 size="sm", on_click=ui.Call("connect_x_account"))

    return ui.Stack(gap=3, children=[
        ui.Header(text="X Connector", level=4),
        ui.Badge(label="● connected", color="green"),
        workspace_nav,
        ui.Divider(),
        ui.Text(content=f"Connected Accounts ({len(accounts)})", variant="caption"),
        ui.List(items=account_items) if account_items else ui.Empty(message="No accounts"),
        ui.Stack(direction="h", gap=2, wrap=True, children=[add_account_btn]),
        ui.Divider(),
        ui.Text(
            content="Manage posts, explore trends and monitor interactions directly from the workspace or via chat.",
            variant="caption",
        ),
    ])
