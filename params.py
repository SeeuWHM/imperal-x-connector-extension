"""Pydantic param models for X Connector chat functions.

Mirrors the backend's own request schemas (see x-connector-backend/service/
apps/{oauth,posts,reads,trends}/schemas.py) — this extension is a thin,
faithful client, not a second source of truth for validation rules.
"""
# No `from __future__ import annotations` — chat.function's param validator
# needs real runtime type annotations (article-writer-extension convention).

from typing import List, Optional
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    """No input required — imperal_id comes from ctx.user, not from the LLM."""


class AccountIdParams(BaseModel):
    account_id: str = Field(..., min_length=1, description="Account ID from list_x_accounts.")


class PostTweetParams(BaseModel):
    text: str = Field(..., min_length=1, max_length=25000, description="Tweet text.")
    media_ids: Optional[List[str]] = Field(None, description="Pre-uploaded media IDs to attach, if any.")


class ThreadParams(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=25, description="One tweet per entry, posted as a reply chain in order.")


class ReplyParams(BaseModel):
    post_id: str = Field(..., min_length=1, description="Post ID to reply to.")
    text: str = Field(..., min_length=1, max_length=25000)


class QuoteParams(BaseModel):
    post_id: str = Field(..., min_length=1, description="Post ID to quote.")
    text: str = Field(..., min_length=1, max_length=25000)


class PostIdParams(BaseModel):
    post_id: str = Field(..., min_length=1, description="Post ID — from a read/search result, never invented.")


class UsernameParams(BaseModel):
    username: str = Field(..., min_length=1, description="X username, without the @.")


class ListReadParams(BaseModel):
    limit: int = Field(20, ge=1, le=25, description="Max items to return (capped at 25).")


class FollowListParams(BaseModel):
    limit: int = Field(6, ge=1, le=6, description="Max items to return (capped at 6 — followers/following cost more per item).")


class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="X search query (supports X's own search operators).")
    limit: int = Field(20, ge=1, le=25)


class TrendsParams(BaseModel):
    woeid: int = Field(1, description="Yahoo WOEID for the location. Defaults to 1 (Worldwide). 23424977=US, 23424975=UK.")
