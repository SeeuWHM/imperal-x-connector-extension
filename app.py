"""X (Twitter) Connector extension — core init + shared helpers.

Architecture (mirrors meta-social-extension's shared-backend pattern):

  - This extension is a thin chat-function layer over the x-connector-api
    backend microservice, which owns the Galera-backed database, the OAuth
    flow with X, and every real X API v2 call. This extension NEVER talks
    to api.x.com directly and never sees a raw X access token — only the
    backend does.

  - x-connector-api is multi-tenant by platform identity: every request
    carries the caller's `imperal_id` as `X-Imperal-Id`, same pattern as
    article-writer-api / meta-social-api.

  - x-connector-api requires a platform JWT on every call (backend_jwt,
    app-scope secret, developer-managed only — never entered or seen by
    end users).

  - ONE X Developer App (registered once by us) serves every installer:
    each user's own "Sign in with X" connects their own account through
    that single shared app — the user never sees or enters an X API key
    and never pays X directly. Imperal absorbs X's real per-call cost and
    the extension is priced cost-plus so every action stays profitable,
    deliberately with no usage limits (see x-connector-backend PLAN.md §1
    and tests/test_pricing_invariant.py in the backend for the enforced
    guarantee).
"""
from __future__ import annotations

import os

from imperal_sdk import Extension, ChatExtension

# Shared backend bridge — same public API gateway host every extension on
# this platform calls. Not a secret: it's the platform's own microservice.
SERVER_URL = os.environ.get("X_CONNECTOR_BACKEND_URL", "") or "https://api.webhostmost.com/x-connector"

ext = Extension(
    "x-connector",
    version="0.1.0",
    display_name="X Connector",
    description=(
        "Post, reply, like, retweet, follow and read your X (Twitter) timeline, mentions, "
        "bookmarks and profile — all through chat. Connect once via 'Sign in with X'; "
        "everything else happens by asking. You never see or pay for an X API key."
    ),
    icon="icon.svg",
    actions_explicit=True,
    capabilities=[
        "Post/Reply/Quote/Delete Tweets",
        "Like/Retweet/Bookmark",
        "Follow/Block/Mute",
        "Timeline/Mentions/Search Reads",
        "Trending Topics",
        "notify:push",
    ],
)

chat = ChatExtension(
    ext,
    tool_name="x_connector",
    description=(
        "X (Twitter) Connector — post/reply/quote/delete tweets, like/retweet/bookmark, "
        "follow/block/mute users, read your home timeline/mentions/own posts/bookmarks, "
        "search recent posts, check a post's metrics or a user's public profile, list your "
        "followers/following, and check what's trending. Always call connect_x_account first "
        "if no account is connected (list_x_accounts to check)."
    ),
    max_rounds=10,
)

ext.secret(
    name="backend_jwt",
    description=(
        "Platform JWT authenticating this extension to the x-connector-api backend "
        "microservice. Developer-managed only — never entered or seen by end users."
    ),
    required=True,
    scope="app",
    env_fallback="IMPERAL_APPSECRET_X_CONNECTOR_BACKEND_JWT",
    max_bytes=2048,
)(lambda: None)


@ext.health_check
async def health(ctx) -> dict:
    """Report whether the backend JWT is configured."""
    jwt = await ctx.secrets.get("backend_jwt")
    return {"status": "ok" if jwt else "degraded", "version": ext.version}
