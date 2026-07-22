"""Pydantic response models for X Connector chat functions.

Every @chat.function(action_type="read") must declare a data_model so the
platform can validate return shapes (federal V23). Mirrors
x-connector-backend/service/apps/*/schemas.py field-for-field.

2026-07-22: enriched to match the backend's expanded PostRecord/
UserProfileResult/PostMetricsResult — same priced X call, much richer data
(reply_settings/can_reply/reply_restriction_reason computed BEFORE any write
is attempted, entities, topics, media, thread shape). See backend's
core/x_enrich.py docstring for the reasoning (this is the direct fix for
replies to @justbyte_/@RedHat posts failing with a misreported "temporary
hiccup" instead of the real, permanent "reply_settings restricts this post").
"""
from __future__ import annotations

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

class MediaRecord(BaseModel):
    type: str = ""            # photo / video / animated_gif
    url: Optional[str] = None
    preview_image_url: Optional[str] = None
    alt_text: Optional[str] = None
    duration_ms: Optional[int] = None


class PostRecord(BaseModel):
    id: str = ""
    text: str = ""
    created_at: Optional[str] = None
    author_username: Optional[str] = None
    author_name: Optional[str] = None
    author_verified: bool = False
    author_verified_type: Optional[str] = None
    author_followers_count: int = 0
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    impression_count: int = 0
    bookmark_count: int = 0

    # ── reply-ability, computed BEFORE any write attempt so Webbee can tell
    # the user up front instead of discovering it via a paid, failed write ──
    reply_settings: str = "everyone"        # everyone | mentionedUsers | following
    can_reply: bool = True
    reply_restriction_reason: Optional[str] = None

    # ── content structure X already parsed for us ──
    hashtags: List[str] = []
    mentioned_usernames: List[str] = []
    urls: List[str] = []
    media: List[MediaRecord] = []
    topics: List[str] = []                  # X's own context_annotations entity names

    # ── thread shape ──
    conversation_id: Optional[str] = None
    is_reply: bool = False
    is_retweet: bool = False
    is_quote: bool = False
    in_reply_to_username: Optional[str] = None

    lang: Optional[str] = None
    possibly_sensitive: bool = False


class PostsListResult(BaseModel):
    posts: List[PostRecord] = []
    count: int = 0
    x_cost_usd: float = 0.0


class UserProfileResult(BaseModel):
    id: str = ""
    username: str = ""
    name: str = ""
    description: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    profile_image_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    listed_count: int = 0
    verified: bool = False
    verified_type: Optional[str] = None
    protected: bool = False
    created_at: Optional[str] = None
    pinned_tweet_id: Optional[str] = None
    hashtags: List[str] = []                # from bio entities
    urls: List[str] = []                    # from bio entities
    x_cost_usd: float = 0.0


class UserRecord(BaseModel):
    id: str = ""
    username: str = ""
    name: str = ""
    description: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    verified: bool = False
    verified_type: Optional[str] = None
    protected: bool = False


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
    bookmark_count: int = 0
    reply_settings: str = "everyone"
    can_reply: bool = True
    reply_restriction_reason: Optional[str] = None
    conversation_id: Optional[str] = None
    lang: Optional[str] = None
    possibly_sensitive: bool = False
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
