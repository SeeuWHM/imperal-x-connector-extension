"""Chat-function handlers: user social graph actions — follow/unfollow/block/unblock/mute/unmute.

Thin pass-through to x-connector-api, which handles X API v2 and usage accounting.
"""
from imperal_sdk.types import ActionResult

from app import chat
from api_client import call_backend, _err
from params import UsernameParams
from response_models import ActionResultRecord


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
