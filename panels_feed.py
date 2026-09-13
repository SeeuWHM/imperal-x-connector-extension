"""X Connector center workspace views — Feed, Compose, and Trends tabs.

Sub-views rendered declaratively via SDK ui.* components (zero LLM tokens).
Kept under 250 lines to strictly respect the module size ceiling.
"""
from __future__ import annotations

from imperal_sdk import ui

from api_client import call_backend


async def render_feed(ctx, subview: str = "home") -> ui.UINode:
    """Feed view supporting Home Timeline, Mentions, Bookmarks, and My Posts."""
    tabs = [
        ("home", "Home Timeline", "/v1/reads/home-timeline"),
        ("mentions", "Mentions", "/v1/reads/mentions"),
        ("my_posts", "My Posts", "/v1/reads/my-posts"),
        ("bookmarks", "Bookmarks", "/v1/reads/bookmarks"),
    ]

    feed_buttons = [
        ui.Button(
            label=label,
            variant="secondary" if subview == sv else "ghost",
            size="sm",
            on_click=ui.Call("__panel__workspace", view="feed", subview=sv),
        )
        for sv, label, _ in tabs
    ]
    subnav = ui.Stack(direction="h", gap=2, wrap=True, children=feed_buttons)

    endpoint = next((ep for sv, _, ep in tabs if sv == subview), "/v1/reads/home-timeline")
    feed_data = await call_backend(ctx, "GET", endpoint, params={"limit": 20})

    if "error" in feed_data:
        content = ui.Alert(
            title="Unable to load feed data",
            message=str(feed_data.get("error", "Error loading feed")),
            variant="warn",
        )
    else:
        posts = feed_data.get("posts", [])
        if not posts:
            content = ui.Empty(
                message=f"No posts found in {subview.replace('_', ' ').title()}.",
                icon="Inbox",
            )
        else:
            items = []
            for p in posts:
                post_id = p.get("id", "")
                text = p.get("text", "")
                author = p.get("author_username", "user")
                created = p.get("created_at", "")[:10]
                metrics = p.get("public_metrics", {})
                likes = metrics.get("like_count", 0)
                rts = metrics.get("retweet_count", 0)

                items.append(
                    ui.ListItem(
                        id=post_id,
                        title=f"@{author}: {text[:90]}{'...' if len(text) > 90 else ''}",
                        subtitle=f"{created} • ❤️ {likes} • 🔁 {rts}",
                        avatar=ui.Avatar(fallback=author[0].upper() if author else "X", size="sm"),
                        actions=[
                            {
                                "label": "Like",
                                "icon": "Heart",
                                "on_click": ui.Call("like_post", post_id=post_id),
                            },
                            {
                                "label": "Repost",
                                "icon": "Repeat",
                                "on_click": ui.Call("retweet_post", post_id=post_id),
                            },
                            {
                                "label": "Save",
                                "icon": "Bookmark",
                                "on_click": ui.Call("bookmark_post", post_id=post_id),
                            },
                        ],
                    )
                )
            content = ui.List(items=items, searchable=True, search_placeholder="Filter posts...")

    return ui.Stack(
        direction="v",
        gap=3,
        children=[
            ui.Header(text="Feed & Activity", level=3, subtitle="Recent tweets and interactions"),
            subnav,
            content,
        ],
    )


def render_compose() -> ui.UINode:
    """Interactive Compose Tweet view."""
    form = ui.Form(
        children=[
            ui.TextArea(
                label="What's happening?",
                placeholder="Write your tweet here (max 280 characters)...",
                param_name="text",
                rows=5,
                required=True,
            ),
            ui.Input(
                label="Image URL (optional)",
                placeholder="https://example.com/image.jpg",
                param_name="image_url",
                type="url",
            ),
            ui.Text(
                content="Tip: You can also ask Webbee in chat to generate, edit, or post threads anytime.",
                variant="caption",
            ),
        ],
        action="post_tweet",
        submit_label="Post Tweet to X",
    )
    return ui.Card(
        title="Compose a New Tweet",
        subtitle="Publish directly to your connected X account",
        content=form,
    )


async def render_trends(ctx) -> ui.UINode:
    """Live Trending Topics view with volume and direct explore action."""
    trends_res = await call_backend(ctx, "GET", "/v1/trends")
    if "error" in trends_res:
        return ui.Alert(message=trends_res["error"], variant="warn")

    trends_list = trends_res.get("trends", [])
    if not trends_list:
        return ui.Empty(message="No trending topics available right now.", icon="TrendingDown")

    rows = []
    for idx, t in enumerate(trends_list[:30], start=1):
        name = t.get("name", "")
        vol = t.get("tweet_volume")
        vol_str = f"{vol:,}" if isinstance(vol, (int, float)) and vol else "Trending"
        rows.append({"rank": str(idx), "name": name, "volume": vol_str})

    return ui.Stack(
        direction="v",
        gap=3,
        children=[
            ui.Header(text="Trending Topics", level=3, subtitle="Real-time trends on X"),
            ui.DataTable(
                columns=[
                    ui.DataColumn(key="rank", label="#", width="10%"),
                    ui.DataColumn(key="name", label="Trend Topic / Hashtag", width="60%"),
                    ui.DataColumn(key="volume", label="Tweet Volume", width="30%"),
                ],
                rows=rows,
            ),
        ],
    )
