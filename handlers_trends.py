"""Chat-function handler: trending topics.

Trends are shared, not personal — x-connector-api serves them from a
background-refreshed cache (never a live per-user X call), so this is
never billed per call (see backend apps/trends/router.py).
"""
from imperal_sdk.types import ActionResult

from app import chat
from api_client import call_backend, _err
from params import TrendsParams
from response_models import TrendsResult


@chat.function(
    "get_trends",
    description=(
        "What's trending on X right now, for a location (defaults to Worldwide). Use for: "
        "what's trending on X/Twitter, X trending topics."
    ),
    action_type="read",
    chain_callable=True,
    data_model=TrendsResult,
)
async def fn_get_trends(ctx, params: TrendsParams) -> ActionResult:
    """Get trends."""
    data = await call_backend(ctx, "GET", "/v1/trends", params={"woeid": params.woeid})
    if "error" in data:
        return _err(data)
    result = TrendsResult(**data)
    return ActionResult.success(data=result, summary=f"{len(result.trends)} trending topic(s).")
