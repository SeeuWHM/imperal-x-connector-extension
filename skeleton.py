"""Skeleton context providers for X Connector — LLM ambient awareness.

Injected into the intent classifier prompt on every chat turn, so the LLM
knows whether an X account is connected, active handle, and recent account state
WITHOUT having to make a tool call first.

Degrades to configured=False without calling the backend when no backend_jwt is
set (never leaks errors, never blocks routing).
"""
from __future__ import annotations

from app import ext
from api_client import call_backend


@ext.skeleton(
    "x_config",
    ttl=300,
    description="X (Twitter) connection status — whether the user has connected an X account",
)
async def skeleton_x_config(ctx) -> dict:
    """Provides ambient awareness to Webbee whether the user has connected X."""
    jwt = await ctx.secrets.get("backend_jwt")
    if not jwt:
        return {
            "response": {
                "configured": False,
                "connected": False,
                "instruction": (
                    "X (Twitter) backend is not configured yet. "
                    "Tell the user the extension service credentials need to be set."
                ),
            }
        }

    try:
        data = await call_backend(ctx, "GET", "/v1/oauth/accounts")
        if "error" in data:
            return {
                "response": {
                    "configured": True,
                    "connected": False,
                    "accounts_count": 0,
                    "instruction": (
                        "X (Twitter) account is not connected yet. "
                        "Tell the user to call connect_x_account to connect their X account via OAuth."
                    ),
                }
            }

        accounts = data.get("accounts", [])
        connected = len(accounts) > 0
        active_acc = accounts[0] if accounts else {}
        username = active_acc.get("x_username") or ""

        return {
            "response": {
                "configured": True,
                "connected": connected,
                "accounts_count": len(accounts),
                "active_username": username,
                "instruction": (
                    f"Connected to X as @{username}. You can post tweets, read timeline, reply, or check trends."
                    if connected
                    else "No X account connected. Suggest calling connect_x_account to link their profile."
                ),
            }
        }
    except Exception as exc:
        return {
            "response": {
                "configured": True,
                "connected": False,
                "error": str(exc),
                "instruction": "Unable to check X connection right now. Offer connect_x_account or list_x_accounts.",
            }
        }
