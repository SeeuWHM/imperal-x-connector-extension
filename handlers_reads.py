"""Chat-function handlers: reads — home timeline, mentions, own posts,
bookmarks, search, post metrics, user profile, followers/following.

Every list-returning read is billed by x-connector-api PER ITEM actually
returned (see backend apps/reads/router.py) — this extension just passes
the `limit` through and shows whatever came back.
"""
from imperal_sdk.types import ActionResult

from app import chat
from api_client import call_backend, _err
from params import FollowListParams, ListReadParams, PostIdParams, SearchParams, UsernameParams
from response_models import PostMetricsResult, PostsListResult, UserProfileResult, UsersListResult


@chat.function(
    "get_home_timeline",
    description="Read your X home timeline (posts from accounts you follow). Use for: show my X timeline, what's new on X.",
    action_type="read",
    chain_callable=True,
    data_model=PostsListResult,
)
async def fn_get_home_timeline(ctx, params: ListReadParams) -> ActionResult:
    """Get home timeline."""
    data = await call_backend(ctx, "GET", "/v1/reads/home-timeline", params={"limit": params.limit})
    if "error" in data:
        return _err(data)
    result = PostsListResult(**data)
    return ActionResult.success(data=result, summary=f"{result.count} post(s) from your home timeline.")


@chat.function(
    "get_mentions",
    description="Read recent posts that mention you on X. Use for: who mentioned me on X, my X mentions.",
    action_type="read",
    chain_callable=True,
    data_model=PostsListResult,
)
async def fn_get_mentions(ctx, params: ListReadParams) -> ActionResult:
    """Get mentions."""
    data = await call_backend(ctx, "GET", "/v1/reads/mentions", params={"limit": params.limit})
    if "error" in data:
        return _err(data)
    result = PostsListResult(**data)
    return ActionResult.success(data=result, summary=f"{result.count} mention(s).")


@chat.function(
    "get_my_posts",
    description="Read your own recent X posts. Use for: show my recent tweets, my X posts.",
    action_type="read",
    chain_callable=True,
    data_model=PostsListResult,
)
async def fn_get_my_posts(ctx, params: ListReadParams) -> ActionResult:
    """Get my posts."""
    data = await call_backend(ctx, "GET", "/v1/reads/my-posts", params={"limit": params.limit})
    if "error" in data:
        return _err(data)
    result = PostsListResult(**data)
    return ActionResult.success(data=result, summary=f"{result.count} of your post(s).")


@chat.function(
    "get_bookmarks",
    description="Read your bookmarked X posts. Use for: show my X bookmarks, saved tweets.",
    action_type="read",
    chain_callable=True,
    data_model=PostsListResult,
)
async def fn_get_bookmarks(ctx, params: ListReadParams) -> ActionResult:
    """Get bookmarks."""
    data = await call_backend(ctx, "GET", "/v1/reads/bookmarks", params={"limit": params.limit})
    if "error" in data:
        return _err(data)
    result = PostsListResult(**data)
    return ActionResult.success(data=result, summary=f"{result.count} bookmark(s).")


@chat.function(
    "search_posts",
    description="Search recent public X posts by keyword/operators. Use for: search X for, find tweets about.",
    action_type="read",
    chain_callable=True,
    data_model=PostsListResult,
)
async def fn_search_posts(ctx, params: SearchParams) -> ActionResult:
    """Search posts."""
    data = await call_backend(ctx, "GET", "/v1/reads/search", params={"query": params.query, "limit": params.limit})
    if "error" in data:
        return _err(data)
    result = PostsListResult(**data)
    return ActionResult.success(data=result, summary=f"{result.count} matching post(s).")


@chat.function(
    "get_post_metrics",
    description="Get engagement metrics (likes/retweets/replies/quotes/impressions) for one X post. Use for: how is this tweet doing.",
    action_type="read",
    chain_callable=True,
    data_model=PostMetricsResult,
)
async def fn_get_post_metrics(ctx, params: PostIdParams) -> ActionResult:
    """Get post metrics."""
    data = await call_backend(ctx, "GET", f"/v1/reads/posts/{params.post_id}/metrics")
    if "error" in data:
        return _err(data)
    result = PostMetricsResult(**data)
    return ActionResult.success(data=result, summary=f"{result.like_count} likes, {result.retweet_count} retweets, {result.reply_count} replies.")


@chat.function(
    "get_user_profile",
    description="Look up a public X user's profile by username. Use for: who is this X account, look up this X profile.",
    action_type="read",
    chain_callable=True,
    data_model=UserProfileResult,
)
async def fn_get_user_profile(ctx, params: UsernameParams) -> ActionResult:
    """Get user profile."""
    data = await call_backend(ctx, "GET", f"/v1/reads/users/{params.username}")
    if "error" in data:
        return _err(data)
    result = UserProfileResult(**data)
    return ActionResult.success(data=result, summary=f"@{result.username} — {result.followers_count} followers.")


@chat.function(
    "get_followers",
    description="List your (or the connected account's) X followers. Use for: who follows me on X, my X followers.",
    action_type="read",
    chain_callable=True,
    data_model=UsersListResult,
)
async def fn_get_followers(ctx, params: FollowListParams) -> ActionResult:
    """Get followers."""
    data = await call_backend(ctx, "GET", "/v1/reads/followers", params={"limit": params.limit})
    if "error" in data:
        return _err(data)
    result = UsersListResult(**data)
    return ActionResult.success(data=result, summary=f"{result.count} follower(s).")


@chat.function(
    "get_following",
    description="List who you (the connected account) follow on X. Use for: who do I follow on X, my X following list.",
    action_type="read",
    chain_callable=True,
    data_model=UsersListResult,
)
async def fn_get_following(ctx, params: FollowListParams) -> ActionResult:
    """Get following."""
    data = await call_backend(ctx, "GET", "/v1/reads/following", params={"limit": params.limit})
    if "error" in data:
        return _err(data)
    result = UsersListResult(**data)
    return ActionResult.success(data=result, summary=f"You follow {result.count} shown here.")
