"""X Connector center workspace panel — rich, self-sufficient dashboard.

Provides 4 main views:
1. Overview & Stats: Active account profile, follower counts, quick actions.
2. Timeline & Feed: Home timeline, mentions, bookmarked posts with action triggers.
3. Compose: Interactive tweet composition form with character counter, reply/thread support.
4. Trending Topics: Live world/local trending topics table with direct explore actions.

All rendered declaratively via SDK ui.* components (zero LLM tokens consumed).
"""
from __future__ import annotations

import logging

from imperal_sdk import ui

from app import ext
from api_client import call_backend
from panels_feed import render_compose, render_feed, render_trends

log = logging.getLogger("x_connector.panels_workspace")


def _nav_toolbar(current_view: str) -> ui.UINode:
    """Header toolbar to switch between views inside the center workspace."""
    views = [
        ("overview", "Overview", "UserCheck"),
        ("feed", "Timeline & Mentions", "MessageSquare"),
        ("compose", "Compose Tweet", "PenTool"),
        ("trends", "Trending Topics", "TrendingUp"),
    ]
    buttons = []
    for vid, label, icon in views:
        is_active = (vid == current_view)
        buttons.append(
            ui.Button(
                label=label,
                icon=icon,
                variant="primary" if is_active else "ghost",
                size="sm",
                on_click=ui.Call("__panel__workspace", view=vid),
            )
        )
    return ui.Stack(direction="h", gap=2, wrap=True, children=buttons)


async def _render_overview(ctx, accounts: list[dict]) -> ui.UINode:
    """Overview view with profile cards, stats, and quick actions."""
    if not accounts:
        return ui.Empty(
            message="No X account connected yet.",
            icon="UserX",
            action={"label": "Sign in with X", "on_click": ui.Call("connect_x_account")},
        )

    acc = accounts[0]
    username = acc.get("x_username") or acc.get("x_user_id", "")
    display_name = acc.get("x_display_name") or username

    profile_data = await call_backend(ctx, "GET", f"/v1/reads/users/{username}")
    has_profile = "error" not in profile_data and profile_data.get("user")
    user_info = profile_data.get("user", {}) if has_profile else {}
    public_metrics = user_info.get("public_metrics", {})

    followers = public_metrics.get("followers_count", 0)
    following = public_metrics.get("following_count", 0)
    tweet_count = public_metrics.get("tweet_count", 0)

    stats_cards = ui.Stack(
        direction="h",
        gap=4,
        wrap=True,
        children=[
            ui.Stat(label="Followers", value=str(followers), icon="Users", color="blue"),
            ui.Stat(label="Following", value=str(following), icon="UserPlus", color="green"),
            ui.Stat(label="Posts", value=str(tweet_count), icon="Send", color="purple"),
            ui.Stat(label="Connected Accounts", value=str(len(accounts)), icon="CheckCircle", color="yellow"),
        ],
    )

    profile_card = ui.Card(
        title=f"Connected as @{username}",
        subtitle=display_name,
        content=ui.Stack(
            direction="v",
            gap=2,
            children=[
                ui.Text(
                    content=user_info.get("description", "Manage your X presence directly through Imperal.") or "Ready for actions.",
                    variant="body",
                ),
                ui.Stack(
                    direction="h",
                    gap=2,
                    wrap=True,
                    children=[
                        ui.Button(
                            label="Compose Tweet",
                            icon="PenTool",
                            size="sm",
                            on_click=ui.Call("__panel__workspace", view="compose"),
                        ),
                        ui.Button(
                            label="View Timeline",
                            icon="MessageSquare",
                            variant="secondary",
                            size="sm",
                            on_click=ui.Call("__panel__workspace", view="feed", subview="home"),
                        ),
                        ui.Button(
                            label="Trending Topics",
                            icon="TrendingUp",
                            variant="outline",
                            size="sm",
                            on_click=ui.Call("__panel__workspace", view="trends"),
                        ),
                    ],
                ),
            ],
        ),
    )

    tips_card = ui.Card(
        title="Available AI Chat Actions",
        subtitle="You can talk to Webbee naturally",
        content=ui.Stack(
            direction="v",
            gap=1,
            children=[
                ui.Text(content="• 'Post a tweet about our new release: https://example.com'", variant="caption"),
                ui.Text(content="• 'What are the top 5 tweets in my timeline right now?'", variant="caption"),
                ui.Text(content="• 'What is trending in the world today?'", variant="caption"),
                ui.Text(content="• 'Search X for mentions of Imperal Cloud'", variant="caption"),
                ui.Text(content="• 'Like and retweet tweet 123456789'", variant="caption"),
            ],
        ),
    )

    return ui.Stack(
        direction="v",
        gap=4,
        children=[
            stats_cards,
            profile_card,
            tips_card,
        ],
    )


@ext.panel("workspace", slot="center", title="X Dashboard", icon="Twitter",
           refresh="on_event:x-connector.disconnect_x_account,x-connector.post_tweet")
async def workspace_panel(ctx, view: str = "overview", subview: str = "home", **kwargs) -> ui.UINode:
    """Center workspace panel for X Connector."""
    accounts_res = await call_backend(ctx, "GET", "/v1/oauth/accounts")
    if "error" in accounts_res:
        return ui.Alert(message=accounts_res["error"], variant="error")

    accounts = accounts_res.get("accounts", [])
    if not accounts:
        return ui.Stack(
            direction="v",
            gap=4,
            children=[
                ui.Header(text="X Connector", level=2, subtitle="Your AI-powered bridge to X"),
                ui.Empty(
                    message="Connect your X account using the button on the left sidebar to unlock the full dashboard.",
                    icon="Twitter",
                ),
            ],
        )

    toolbar = _nav_toolbar(view)

    if view == "overview":
        content = await _render_overview(ctx, accounts)
    elif view == "feed":
        content = await render_feed(ctx, subview=subview)
    elif view == "compose":
        content = render_compose()
    elif view == "trends":
        content = await render_trends(ctx)
    else:
        content = await _render_overview(ctx, accounts)

    return ui.Stack(
        direction="v",
        gap=4,
        children=[
            toolbar,
            ui.Divider(),
            content,
        ],
    )
