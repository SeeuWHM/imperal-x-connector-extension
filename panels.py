"""Panels for X Connector.

Clean, minimal UI adhering to Imperal standards:
- Sidebar: Account connection status, avatar, connection actions (slot='left')
- Center: Overview with key free metrics & engagement activity chart.
"""
from __future__ import annotations

import logging
from imperal_sdk import ui

from app import ext
from api_client import call_backend

log = logging.getLogger("x_connector")


def _account_items(accounts: list[dict], active_id: str = "") -> list:
    items = []
    for acc in accounts:
        connection_id = acc.get("id", "")
        username = acc.get("x_username") or acc.get("x_user_id", "")
        display_name = acc.get("x_display_name") or ""
        is_active = connection_id == active_id if active_id else False
        items.append(
            ui.ListItem(
                id=connection_id,
                title=f"@{username}" if username else connection_id,
                subtitle=display_name or ("Active" if is_active else "Connected"),
                avatar=ui.Avatar(fallback=(username[0].upper() if username else "X"), size="sm"),
                badge=ui.Badge("Active", color="green") if is_active else None,
                actions=[
                    {
                        "label": "Disconnect",
                        "icon": "Trash2",
                        "on_click": ui.Call("disconnect_x_account", connection_id=connection_id),
                    }
                ],
            )
        )
    return items


@ext.panel("sidebar", slot="left")
async def sidebar_panel(ctx):
    """Sidebar: account status and connect/disconnect controls."""
    error = ""
    accounts = []
    try:
        resp = await call_backend(ctx, "GET", "/v1/oauth/accounts")
        if isinstance(resp, dict) and "error" in resp:
            error = str(resp["error"])
        elif isinstance(resp, dict):
            accounts = resp.get("accounts", [])
    except Exception as exc:
        log.warning("Failed to fetch X accounts for sidebar: %s", exc)
        error = str(exc)

    if not accounts:
        children = [
            ui.Header(text="X", level=4),
            ui.Badge(label="○ not connected", color="gray"),
            ui.Divider(),
            ui.Text(
                content="Connect your X account to monitor analytics and account activity.",
                variant="body",
            ),
        ]
        if error:
            children.append(ui.Alert(message=error, type="error"))

        children.extend([
            ui.Stack(
                direction="h",
                gap=2,
                children=[
                    ui.Button(
                        label="Sign in with X",
                        icon="Plus",
                        variant="primary",
                        on_click=ui.Call("connect_x_account"),
                    ),
                ],
            ),
            ui.Text(
                content="Free tier includes account metrics and engagement overview.",
                variant="caption",
            ),
        ])
        return ui.Stack(children=children)

    # Connected accounts list
    items = _account_items(accounts)
    children = [
        ui.Header(text="X", level=4),
        ui.Badge(label=f"● {len(accounts)} connected", color="green"),
        ui.Divider(),
        ui.List(items=items),
        ui.Divider(),
        ui.Button(
            label="Add another X account",
            icon="Plus",
            variant="ghost",
            on_click=ui.Call("connect_x_account"),
        ),
    ]
    return ui.Stack(children=children)


@ext.panel("workspace", slot="center")
async def workspace_panel(ctx):
    """Clean, simple workspace overview with key metrics and engagement activity chart."""
    accounts = []
    try:
        resp = await call_backend(ctx, "GET", "/v1/oauth/accounts")
        if isinstance(resp, dict):
            accounts = resp.get("accounts", [])
    except Exception as exc:
        log.warning("Failed to fetch accounts for workspace: %s", exc)
        accounts = []

    if not accounts:
        return ui.Stack(
            gap=4,
            align="center",
            children=[
                ui.Avatar(fallback="X", size="lg"),
                ui.Header(text="X", level=3, subtitle="Connect your account to view profile and analytics"),
                ui.Button(
                    label="Sign in with X",
                    icon="Plus",
                    variant="primary",
                    on_click=ui.Call("connect_x_account"),
                ),
            ],
        )

    primary = accounts[0]
    username = primary.get("x_username", "account")
    display_name = primary.get("x_display_name", username)

    return ui.Stack(
        gap=4,
        children=[
            ui.Row(
                gap=3,
                children=[
                    ui.Avatar(fallback=(username[0].upper() if username else "X"), size="md"),
                    ui.Column(
                        gap=1,
                        children=[
                            ui.Header(text=display_name, level=3),
                            ui.Text(content=f"@{username}"),
                        ],
                    ),
                ],
            ),
            ui.Divider(),
            ui.Stats(
                columns=2,
                children=[
                    ui.Stat(
                        label="Status",
                        value="Connected",
                        icon="CheckCircle",
                        color="green",
                    ),
                    ui.Stat(
                        label="Account Mode",
                        value="OAuth 2.0",
                        icon="Shield",
                        color="blue",
                    ),
                ],
            ),
        ],
    )
