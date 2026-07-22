"""Chat-function handlers: write actions — post/reply/quote/delete/like/
retweet/bookmark/follow/block/mute.

Every handler is a thin pass-through to x-connector-api, which owns the
real X API v2 call and the usage-ledger cost recording (see backend
apps/posts/router.py — the "always profitable" guarantee lives there, not
here). This extension's only job is param validation + a friendly summary.
"""
from imperal_sdk.types import ActionResult

from app import chat
from api_client import call_backend, _err
from params import (
    ImageUrlParams, PostIdParams, PostTweetParams, QuoteParams, ReplyParams,
    ThreadParams, UsernameParams,
)
from response_models import ActionResultRecord, MediaUploadResult, ThreadResult, TweetResult


@chat.function(
    "post_tweet",
    description="Post a new tweet to X. Use for: post to X, post to Twitter, tweet this.",
    action_type="write", event="x-connector.post_tweet",
    effects=["create:post"],
    data_model=TweetResult,
)
async def fn_post_tweet(ctx, params: PostTweetParams) -> ActionResult:
    """Post tweet."""
    data = await call_backend(ctx, "POST", "/v1/posts", json={"text": params.text, "media_ids": params.media_ids})
    if "error" in data:
        return _err(data)
    result = TweetResult(**data)
    return ActionResult.success(data=result, summary=f"Posted (id {result.id}).")


@chat.function(
    "post_thread",
    description="Post a thread (chain of connected tweets) to X, in order. Use for: post a thread, post this as multiple tweets.",
    action_type="write", event="x-connector.post_thread",
    effects=["create:post"],
    data_model=ThreadResult,
)
async def fn_post_thread(ctx, params: ThreadParams) -> ActionResult:
    """Post thread."""
    data = await call_backend(ctx, "POST", "/v1/posts/thread", json={"texts": params.texts})
    if "error" in data:
        return _err(data)
    result = ThreadResult(**data)
    return ActionResult.success(data=result, summary=f"Posted a {result.count}-tweet thread.")


@chat.function(
    "reply_to_post",
    description=(
        "Reply to an X post. Use for: reply to this tweet, respond to this post. "
        "IMPORTANT (X platform rule, not something we control): X's API only allows a reply "
        "if the post's author already @mentioned this account in that post, or it's this "
        "account's own post -- reply_settings on the post is irrelevant to this. Check the "
        "post's can_reply field from a read (e.g. search_posts/get_post_metrics) BEFORE "
        "calling this to avoid a guaranteed-failing paid write."
    ),
    action_type="write", event="x-connector.reply_to_post",
    effects=["create:post"],
    data_model=TweetResult,
)
async def fn_reply_to_post(ctx, params: ReplyParams) -> ActionResult:
    """Reply to post."""
    data = await call_backend(ctx, "POST", "/v1/posts/reply", json={"post_id": params.post_id, "text": params.text})
    if "error" in data:
        return _err(data)
    result = TweetResult(**data)
    return ActionResult.success(data=result, summary=f"Replied (id {result.id}).")


@chat.function(
    "quote_post",
    description=(
        "Quote-tweet an X post with your own comment. Use for: quote this tweet. "
        "IMPORTANT (X platform rule, not something we control): same restriction as replies -- "
        "X's API only allows quoting a post if its author already @mentioned this account in "
        "that post, or it's this account's own post. Check can_reply from a read first."
    ),
    action_type="write", event="x-connector.quote_post",
    effects=["create:post"],
    data_model=TweetResult,
)
async def fn_quote_post(ctx, params: QuoteParams) -> ActionResult:
    """Quote post."""
    data = await call_backend(ctx, "POST", "/v1/posts/quote", json={"post_id": params.post_id, "text": params.text})
    if "error" in data:
        return _err(data)
    result = TweetResult(**data)
    return ActionResult.success(data=result, summary=f"Quote-posted (id {result.id}).")


@chat.function(
    "delete_post",
    description="Permanently delete one of your own X posts. Use for: delete this tweet.",
    action_type="write", event="x-connector.delete_post",
    effects=["delete:post"],
    data_model=ActionResultRecord,
)
async def fn_delete_post(ctx, params: PostIdParams) -> ActionResult:
    """Delete post."""
    data = await call_backend(ctx, "DELETE", f"/v1/posts/{params.post_id}")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary="Deleted.")


@chat.function(
    "like_post",
    description="Like an X post. Use for: like this tweet.",
    action_type="write", event="x-connector.like_post",
    effects=["create:like"],
    data_model=ActionResultRecord,
)
async def fn_like_post(ctx, params: PostIdParams) -> ActionResult:
    """Like post."""
    data = await call_backend(ctx, "POST", f"/v1/posts/{params.post_id}/like")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary="Liked.")


@chat.function(
    "unlike_post",
    description="Unlike an X post you previously liked. Use for: unlike this tweet.",
    action_type="write", event="x-connector.unlike_post",
    effects=["delete:like"],
    data_model=ActionResultRecord,
)
async def fn_unlike_post(ctx, params: PostIdParams) -> ActionResult:
    """Unlike post."""
    data = await call_backend(ctx, "DELETE", f"/v1/posts/{params.post_id}/like")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary="Unliked.")


@chat.function(
    "retweet_post",
    description="Retweet (repost) an X post. Use for: retweet this, repost this tweet.",
    action_type="write", event="x-connector.retweet_post",
    effects=["create:retweet"],
    data_model=ActionResultRecord,
)
async def fn_retweet_post(ctx, params: PostIdParams) -> ActionResult:
    """Retweet post."""
    data = await call_backend(ctx, "POST", f"/v1/posts/{params.post_id}/retweet")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary="Retweeted.")


@chat.function(
    "undo_retweet",
    description="Undo a retweet/repost of an X post. Use for: undo this retweet.",
    action_type="write", event="x-connector.undo_retweet",
    effects=["delete:retweet"],
    data_model=ActionResultRecord,
)
async def fn_undo_retweet(ctx, params: PostIdParams) -> ActionResult:
    """Undo retweet."""
    data = await call_backend(ctx, "DELETE", f"/v1/posts/{params.post_id}/retweet")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary="Retweet undone.")


@chat.function(
    "bookmark_post",
    description="Bookmark an X post for later. Use for: bookmark this tweet, save this post.",
    action_type="write", event="x-connector.bookmark_post",
    effects=["create:bookmark"],
    data_model=ActionResultRecord,
)
async def fn_bookmark_post(ctx, params: PostIdParams) -> ActionResult:
    """Bookmark post."""
    data = await call_backend(ctx, "POST", f"/v1/posts/{params.post_id}/bookmark")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary="Bookmarked.")


@chat.function(
    "remove_bookmark",
    description="Remove an X post from your bookmarks. Use for: remove this bookmark, unsave this post.",
    action_type="write", event="x-connector.remove_bookmark",
    effects=["delete:bookmark"],
    data_model=ActionResultRecord,
)
async def fn_remove_bookmark(ctx, params: PostIdParams) -> ActionResult:
    """Remove bookmark."""
    data = await call_backend(ctx, "DELETE", f"/v1/posts/{params.post_id}/bookmark")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary="Bookmark removed.")


@chat.function(
    "follow_user",
    description="Follow an X user by username. Use for: follow this account, follow @someone.",
    action_type="write", event="x-connector.follow_user",
    effects=["create:follow"],
    data_model=ActionResultRecord,
)
async def fn_follow_user(ctx, params: UsernameParams) -> ActionResult:
    """Follow user."""
    data = await call_backend(ctx, "POST", f"/v1/users/{params.username}/follow")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary=f"Now following @{params.username}.")


@chat.function(
    "unfollow_user",
    description="Unfollow an X user by username. Use for: unfollow this account.",
    action_type="write", event="x-connector.unfollow_user",
    effects=["delete:follow"],
    data_model=ActionResultRecord,
)
async def fn_unfollow_user(ctx, params: UsernameParams) -> ActionResult:
    """Unfollow user."""
    data = await call_backend(ctx, "DELETE", f"/v1/users/{params.username}/follow")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary=f"Unfollowed @{params.username}.")


@chat.function(
    "block_user",
    description="Block an X user by username. Use for: block this account.",
    action_type="write", event="x-connector.block_user",
    effects=["create:block"],
    data_model=ActionResultRecord,
)
async def fn_block_user(ctx, params: UsernameParams) -> ActionResult:
    """Block user."""
    data = await call_backend(ctx, "POST", f"/v1/users/{params.username}/block")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary=f"Blocked @{params.username}.")


@chat.function(
    "mute_user",
    description="Mute an X user by username. Use for: mute this account.",
    action_type="write", event="x-connector.mute_user",
    effects=["create:mute"],
    data_model=ActionResultRecord,
)
async def fn_mute_user(ctx, params: UsernameParams) -> ActionResult:
    """Mute user."""
    data = await call_backend(ctx, "POST", f"/v1/users/{params.username}/mute")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary=f"Muted @{params.username}.")


@chat.function(
    "unblock_user",
    description="Unblock an X user by username, reversing a previous block. Use for: unblock this account, undo a block.",
    action_type="write", event="x-connector.unblock_user",
    effects=["delete:block"],
    data_model=ActionResultRecord,
)
async def fn_unblock_user(ctx, params: UsernameParams) -> ActionResult:
    """Unblock user."""
    data = await call_backend(ctx, "DELETE", f"/v1/users/{params.username}/block")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary=f"Unblocked @{params.username}.")


@chat.function(
    "unmute_user",
    description="Unmute an X user by username, reversing a previous mute. Use for: unmute this account, undo a mute.",
    action_type="write", event="x-connector.unmute_user",
    effects=["delete:mute"],
    data_model=ActionResultRecord,
)
async def fn_unmute_user(ctx, params: UsernameParams) -> ActionResult:
    """Unmute user."""
    data = await call_backend(ctx, "DELETE", f"/v1/users/{params.username}/mute")
    if "error" in data:
        return _err(data)
    result = ActionResultRecord(**data)
    return ActionResult.success(data=result, summary=f"Unmuted @{params.username}.")


@chat.function(
    "upload_image_for_post",
    description=(
        "Upload an image from a public URL to X so it can be attached to a tweet — returns a "
        "media_id to pass into post_tweet's media_ids. Use for: attach this image to my tweet, "
        "post a picture on X. NOTE: requires the connected X account to have re-authorized after "
        "media support was added — if this fails with a scope/permission error, ask the user to "
        "reconnect via connect_x_account."
    ),
    action_type="write", event="x-connector.upload_image_for_post",
    effects=["create:media"],
    data_model=MediaUploadResult,
)
async def fn_upload_image_for_post(ctx, params: ImageUrlParams) -> ActionResult:
    """Upload image for post."""
    data = await call_backend(ctx, "POST", "/v1/media/upload", json={"image_url": params.image_url})
    if "error" in data:
        return _err(data)
    result = MediaUploadResult(**data)
    return ActionResult.success(data=result, summary=f"Image uploaded (media_id {result.media_id}) — pass this into post_tweet's media_ids.")
