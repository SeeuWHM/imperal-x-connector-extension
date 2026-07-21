"""Param-model validation tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from pydantic import ValidationError

from params import (
    AccountIdParams, FollowListParams, ListReadParams, PostIdParams,
    PostTweetParams, ReplyParams, SearchParams, ThreadParams, TrendsParams,
    UsernameParams,
)


def test_account_id_requires_non_empty():
    with pytest.raises(ValidationError):
        AccountIdParams(account_id="")


def test_post_tweet_requires_text():
    with pytest.raises(ValidationError):
        PostTweetParams(text="")


def test_post_tweet_accepts_media_ids():
    p = PostTweetParams(text="hello world", media_ids=["m1", "m2"])
    assert p.media_ids == ["m1", "m2"]


def test_thread_requires_at_least_one_text():
    with pytest.raises(ValidationError):
        ThreadParams(texts=[])


def test_thread_caps_at_25():
    with pytest.raises(ValidationError):
        ThreadParams(texts=["x"] * 26)


def test_reply_requires_post_id_and_text():
    with pytest.raises(ValidationError):
        ReplyParams(post_id="", text="hi")
    p = ReplyParams(post_id="123", text="hi")
    assert p.post_id == "123"


def test_post_id_requires_non_empty():
    with pytest.raises(ValidationError):
        PostIdParams(post_id="")


def test_username_requires_non_empty():
    with pytest.raises(ValidationError):
        UsernameParams(username="")


def test_list_read_default_and_cap():
    p = ListReadParams()
    assert p.limit == 20
    with pytest.raises(ValidationError):
        ListReadParams(limit=26)


def test_follow_list_capped_at_6():
    p = FollowListParams()
    assert p.limit == 6
    with pytest.raises(ValidationError):
        FollowListParams(limit=7)


def test_search_requires_query():
    with pytest.raises(ValidationError):
        SearchParams(query="", limit=10)


def test_trends_defaults_to_worldwide():
    p = TrendsParams()
    assert p.woeid == 1
