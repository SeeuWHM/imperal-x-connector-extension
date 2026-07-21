"""Pydantic response models for X Connector chat functions.

Every @chat.function(action_type="read") must declare a data_model so the
platform can validate return shapes (federal V23). Mirrors
x-connector-backend/service/apps/*/schemas.py field-for-field.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# ── oauth ──────────────────────────────────────────────────────────────

class AuthorizeUrlResult(BaseModel):
    # Field name MUST be ``auth_url`` (not ``authorize_url``) — the platform
    # recognises this exact field on an OAuth-connect function's response and
    # opens it in a small popup window, identical to Gmail / Google Drive /
    # Search Console. Any other field name just renders as plain chat text
    # (a link the user has to spot and click manually — the bug this fixes).
    auth_url: str = ""
    instruction: str = ""
    state: str = ""


class AccountSummaryRecord(BaseModel):
    id: str = ""
    x_user_id: str = ""
    x_username: Optional[str] = None
    x_display_name: Optional[str] = None
    access_token_expires_at: Optional[str] = None
    created_at: Optional[str] = None


class AccountsListResult(BaseModel):
    accounts: List[AccountSummaryRecord] = []


class DisconnectResultRecord(BaseModel):
    disconnected: bool = False
    account_id: str = ""


# ── posts (write) ─────────────────────────────────────────────────────

class TweetResult(BaseModel):
    id: str = ""
    text: str = ""
    contains_url: bool = False
    x_cost_usd: float = 0.0


class ThreadResult(BaseModel):
    post_ids: List[str] = []
    count: int = 0
    x_cost_usd: float = 0.0


class ActionResultRecord(BaseModel):
    ok: bool = True
    post_id: Optional[str] = None
    x_cost_usd: float = 0.0


class MediaUploadResult(BaseModel):
    media_id: str = ""
    x_cost_usd: float = 0.0


# ── reads ─────────────────────────────────────────────────────────────

class PostRecord(BaseModel):
    id: str = ""
    text: str = ""
    created_at: Optional[str] = None
    author_username: Optional[str] = None
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    impression_count: int = 0


class PostsListResult(BaseModel):
    posts: List[PostRecord] = []
    count: int = 0
    x_cost_usd: float = 0.0


class UserProfileResult(BaseModel):
    id: str = ""
    username: str = ""
    name: str = ""
    description: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    verified: bool = False
    x_cost_usd: float = 0.0


class UserRecord(BaseModel):
    id: str = ""
    username: str = ""
    name: str = ""
    followers_count: int = 0


class UsersListResult(BaseModel):
    users: List[UserRecord] = []
    count: int = 0
    x_cost_usd: float = 0.0


class PostMetricsResult(BaseModel):
    id: str = ""
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    impression_count: int = 0
    x_cost_usd: float = 0.0


# ── trends ────────────────────────────────────────────────────────────

class TrendItemRecord(BaseModel):
    name: str = ""
    post_count: Optional[int] = None
    trend_url: Optional[str] = None


class TrendsResult(BaseModel):
    woeid: int = 1
    trends: List[TrendItemRecord] = []
    cached_at: Optional[str] = None
    x_cost_usd: float = 0.0
