"""Chat-function handlers: OAuth connect/disconnect + connected accounts.

X (Twitter) OAuth is NOT one of the SDK's built-in providers
(ctx.oauth_authorize_url only covers google/microsoft/yahoo), so the whole
flow is hand-built on our own x-connector-api backend: this extension just
asks the backend for a ready-to-open authorize_url and displays it — the
backend owns PKCE + state signing, the code exchange, and token storage
entirely.
"""
from imperal_sdk.types import ActionResult

from app import chat
from api_client import call_backend, _err
from params import AccountIdParams, NoParams
from response_models import (
    AccountsListResult, AccountSummaryRecord, AuthorizeUrlResult, DisconnectResultRecord,
)


@chat.function(
    "connect_x_account",
    description=(
        "Get a 'Sign in with X' link to connect an X (Twitter) account to your X Connector. "
        "Use for: connect X, connect Twitter, link my X account."
    ),
    action_type="read",
    data_model=AuthorizeUrlResult,
)
async def fn_connect_x_account(ctx, params: NoParams) -> ActionResult:
    """Connect X account."""
    data = await call_backend(ctx, "GET", "/v1/oauth/authorize")
    if "error" in data:
        return _err(data)
    result = AuthorizeUrlResult(authorize_url=data.get("authorize_url", ""), state=data.get("state", ""))
    return ActionResult.success(
        data=result,
        summary="Open this link to connect your X account.",
    )


@chat.function(
    "list_x_accounts",
    description="List connected X (Twitter) accounts. Use for: what X accounts are connected, is my X account connected.",
    action_type="read",
    chain_callable=True,
    data_model=AccountsListResult,
)
async def fn_list_x_accounts(ctx, params: NoParams) -> ActionResult:
    """List X accounts."""
    data = await call_backend(ctx, "GET", "/v1/oauth/accounts")
    if "error" in data:
        return _err(data)
    accounts = [AccountSummaryRecord(**a) for a in data.get("accounts", [])]
    result = AccountsListResult(accounts=accounts)
    return ActionResult.success(data=result, summary=f"{len(accounts)} connected X account(s).")


@chat.function(
    "disconnect_x_account",
    description="Disconnect an X (Twitter) account from your X Connector. Use for: disconnect X, disconnect Twitter.",
    action_type="write", event="x-connector.disconnect_x_account",
    effects=["delete:connection"],
    data_model=DisconnectResultRecord,
)
async def fn_disconnect_x_account(ctx, params: AccountIdParams) -> ActionResult:
    """Disconnect X account."""
    data = await call_backend(ctx, "DELETE", f"/v1/oauth/accounts/{params.account_id}")
    if "error" in data:
        return _err(data)
    result = DisconnectResultRecord(**data)
    return ActionResult.success(
        data=result, summary="Disconnected.", refresh_panels=["sidebar"],
    )
