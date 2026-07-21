# X (Twitter) Connector — Extension Plan (A → Z)

**Status:** PLANNING — no code written yet. This doc is the spec to build against.
**Model:** single shared X App owned by us (Imperal/SeeU) — user just logs in via
"Sign in with X" (OAuth 2.0 + PKCE). User never sees an X API key, never pays X
directly. WE pay X for every call; the user pays US through the extension's own
token price per action (cost-plus, profitable on every single call, no usage caps).

Mirrors the existing architecture of `meta-social-extension` (thin chat-function
layer, zero direct calls to the real API, one shared OAuth app for everyone) —
see that extension's README for the proven pattern this plan reuses.

---

## 0. Why this shape (recap of the decision)

- User said: billing goes through US, we mark the extension up, user never touches
  X's own billing. Confirmed 2026-07-21.
- X API has had **no free tier since Feb 2026** — pay-per-usage, credits loaded in
  advance in X's Developer Console (verified live against docs.x.com/x-api/getting-
  started/pricing, 2026-07-21). Real costs (per resource / per request):

  | Operation | X's real cost |
  |---|---|
  | Read a Post/List/Space/Note (home timeline, mentions, search results, user's own posts) | \$0.005 each |
  | Read a user profile / follower·following list / DM event | \$0.010 each |
  | Read Trends | \$0.010 each |
  | Read Likes/Mutes/Blocks | \$0.001 each |
  | Read your OWN data (owned reads: own tweets/bookmarks/mentions/DMs) | \$0.001 each |
  | Post a tweet — no link | \$0.015 |
  | Post a tweet — contains a URL | \$0.200 (13x premium — X's own anti-spam pricing) |
  | Like / Follow / Retweet | \$0.015 |
  | Reply to a mention | \$0.010 |
  | Delete / bookmark / media-metadata op | \$0.005 |
  | 24h dedup: same resource re-requested same UTC day = charged once | — |

  No monthly subscription tiers exist anymore for new developers (Basic/Pro closed
  to new signups, auto-migrating existing ones to pay-per-use). Enterprise (full
  archive, streaming) is \$42k+/mo — **out of scope**, not needed for what users
  actually ask Webbee for.

- Imperal's own token economy (confirmed from `superpowers/specs/2026-04-14-
  billing-token-economy-v2-design.md`): **1 Imperal token = \$0.001 USD**, platform
  takes 20% of the extension's declared `base_price` per action, developer (us)
  keeps 80%. **Hard platform cap: 500 tokens base_price per single action.**

## 1. Pricing model — cost-plus, profitable on every call, no usage limits

Formula used for every priced action:

```
cost_tokens   = x_api_real_cost_usd / 0.001                # X's real cost, in tokens
target_net    = cost_tokens * MARGIN                       # what we want LEFT after platform's 20% cut
base_price    = ceil( target_net / (1 - 0.20) )            # what we declare as the action's price
```

`MARGIN = 5` (5x real cost) is the default for this extension — comfortably
profitable, still cheap enough per-action that a normal user never notices it.
`post_tweet_with_url` is the one exception (see §1.2).

### 1.1 Concrete per-action prices (tokens, at 3x realized margin AFTER platform's 20% cut)

Single-item / fixed-cost actions (flat price, no list involved):

| Chat function | X operation | Real cost | Imperal price (tokens) | ~USD to user |
|---|---|---|---|---|
| `get_my_likes`, connection checks | read (own data / likes) | $0.001 | **7 tok** | $0.007 |
| `post_tweet` (no URL) | write | $0.015 | **94 tok** | $0.094 |
| `post_tweet` (contains a URL) | write | $0.200 | **500 tok (platform cap, see 1.2)** | $0.50 |
| `post_thread` (N tweets) | write x N | $0.015 x N | **94 x N tok** (computed from actual tweet count, shown before send) | - |
| `like_post`, `retweet_post`, `follow_user` | write | $0.015 | **94 tok** | $0.094 |
| `reply_to_post` | write | $0.010 | **63 tok** | $0.063 |
| `delete_post`, `unlike_post`, `remove_bookmark` | write | $0.005 | **32 tok** | $0.032 |
| `list_x_accounts`, `switch_x_account`, connection status | zero X cost (reads our own store) | $0 | **1 tok** (platform default `read` floor) | $0.001 |

**List-returning reads are priced PER ITEM, not flat** — this is the fix for the
bug an earlier draft of this table had (a flat 32/63 tok price assumed one item,
but these calls return up to `limit` items and X bills per item returned):

| Chat function | X operation | Real cost/item | `limit` cap | Price formula | Price at max `limit` |
|---|---|---|---|---|---|
| `get_home_timeline`, `get_mentions`, `search_recent_posts`, `get_my_posts`, `get_bookmarks` | read Post | $0.005/item | `le=25` | `19 tok x actual_count` (min 19, i.e. 1 item) | 25 items -> **475 tok** |
| `get_user_profile` | read User (always exactly 1 item) | $0.010 | n/a | flat | **75 tok** |
| `get_followers`, `get_following` | read User | $0.010/item | `le=12` | `75 tok x actual_count` | 12 items -> **900 tok -> capped at 500** (see below) |

All three per-item rows use `MARGIN = 3` (not 5) specifically because they're
priced against the platform's `le=25`/`le=12` worst case, not the item cost alone
- the worst case is already the expensive case, no need to stack margin on margin.

`get_followers`/`get_following` at their own cap (12 items x 75 tok = 900 tok)
exceed the platform's 500-tok ceiling per action. Fix: lower the cap to
`le=6` (6 x 75 = 450 tok, under the ceiling) rather than trying to charge above
the cap - **do this at implementation time, `le=12` above was wrong**, corrected
cap is `le=6` for these two functions specifically.

`get_trends` is a special case, handled separately in §1.2b (shared cache, not
priced per-call at all) because X's Trends endpoint has no user-controllable
`limit` and can return ~50 items in one response - pricing it per-item like the
others would blow past the 500-tok cap on every single call, not just a corner
case.

### 1.2 The URL-post edge case

X charges **$0.20** for one tweet containing a link - 13x more than a plain tweet.
At 5x margin that's 1250 tokens, which blows through the platform's 500-token cap
per action. Two compliant options, pick at implementation time:

- **(a) Cap at 500 tok anyway.** After the 20% platform cut we net 400 tok = $0.40,
  which still fully covers the $0.20 X cost with 2x margin left over. Lower margin
  on this one action only, everything else keeps its full margin. Simplest, no
  special logic needed. **Recommended.**
- **(b) Detect the URL server-side before pricing** and charge the plain-tweet
  price ONLY when the draft text has no URL, else charge the capped 500. Same
  outcome as (a), just makes the price transparent to the user upfront in the
  confirmation dialog ("this tweet contains a link, it costs more"). Nicer UX,
  slightly more backend logic. Do this if we want to be extra transparent.

### 1.2b `get_trends` - shared cache, not per-call pricing

Trends are NOT personal data - the same "what's trending" result is identical
for every user asking at the same moment (X scopes trends by location, not by
account). So instead of charging each user for a fresh $0.01x50-item X call:

- The **backend** fetches trends for a small fixed set of locations on a timer
  (e.g. every 15 min) and caches the result once, shared across ALL users -
  real X cost stays ~constant regardless of how many of our users ask for
  trends, instead of scaling per-request.
- The extension prices `get_trends` at a small flat rate (**13 tok**, matching
  the single "own data" tier) since the marginal cost to us of serving it out
  of the shared cache is ~zero - this is comfortably profitable precisely
  because the real X cost is amortized across every user, not paid per-request.
- This is the same "shared backend, no per-tenant duplicate cost" principle
  already used for other multi-tenant-but-shared-data features in this repo -
  do not implement `get_trends` as a live X call triggered per chat message.

### 1.3 The "N items per call" problem - MUST be capped, this is the one real risk

X bills **per resource returned**, not per request. A `get_home_timeline` call
that returns 25 tweets costs us $0.125, not $0.005 - our platform's pricing
model wants ONE flat `base_price` declared per chat function, shown to the user
BEFORE execution ("no estimates, no surprises" - the guaranteed-price contract).
Since §1.1's list-priced functions already compute their price from
`actual_count x per-item price` (not a flat guess), the guarantee holds exactly
regardless of how many items come back, as long as the `limit` Pydantic field
truly hard-caps the request (`Field(le=25)` / `Field(le=6)`, enforced server-side,
never trusted from the caller).

**This is the single most important correctness rule in this whole plan** - get
it wrong (raise a `limit` cap later without recalculating the per-item price or
the platform-cap check) and individual heavy-list calls go into the red even
though the "per action" price looked profitable on paper for the old cap. A CI
test (see §4) enforces both the per-item math AND the `actual_count x price <=
500 tok` platform-cap invariant permanently, not just a one-time manual check.

## 2. Chat functions (what the user can actually ask for)

**Connection / account**
- `connect_x_account` — kicks off "Sign in with X" OAuth (shared app), stores the
  resulting user access/refresh token via `ctx.secrets` (per-user, never raw in
  DB/logs)
- `list_x_accounts`, `switch_x_account`, `disconnect_x_account` — multi-account
  support, same shape as se-ranking/bing/mailerlite's account switcher
- `connection_status`

**Posting**
- `post_tweet(text, media_ids?)` — plain post
- `post_thread(texts: list[str])` — chain of replies-to-self
- `reply_to_post(post_id, text)`
- `quote_post(post_id, text)`
- `delete_post(post_id)`
- `like_post` / `unlike_post`
- `retweet_post` / `undo_retweet`
- `bookmark_post` / `remove_bookmark`

**Reading / monitoring**
- `get_home_timeline(limit<=25)`
- `get_mentions(limit<=25)`
- `get_my_posts(limit<=25)`
- `get_bookmarks(limit<=25)`
- `search_recent_posts(query, limit<=25)` — last 7 days only (X's own limit,
  no full-archive on pay-per-use)
- `get_post_metrics(post_id)` — impressions/likes/replies/reposts for one post

**Profile / audience**
- `get_user_profile(username)`
- `get_followers(username, limit<=6)` / `get_following(username, limit<=6)` — capped at 6, not 25, specifically to keep this action's price under the platform's 500-tok ceiling (see §1.1)
- `follow_user` / `unfollow_user`
- `block_user` / `mute_user`

**Lists**
- `create_list`, `add_to_list`, `remove_from_list`, `get_list_timeline`

**Trends**
- `get_trends(location?)`

**Direct Messages** (needs elevated OAuth scope, flag as Phase 2 — see §5)
- `get_dm_conversations`, `send_dm`

## 3. Panels (DUI)

- **Sidebar (left):** connected X account(s) + quick stats (followers, last-post
  engagement) — **cached** via `ctx.cache` (same pattern just shipped across
  matomo/gsc/bing/se-ranking/mailerlite/article-writer/newsletter-writer this
  session) so opening the panel never fires a live (billable!) X call on every
  render. TTL ~180s is fine — X data doesn't need to be second-fresh for a sidebar
  glance, and every real render still costs us money per X's pricing, so caching
  here is not just a UX nicety, it directly protects margin.
- **Workspace (center):** recent posts board + one post's detail/metrics view.
- Same "cache the list views, leave the single-item detail live" split used
  everywhere else this session.

## 4. Params / response models / testing (federal-grade, same bar as every other
extension shipped this session)

- Every function: Pydantic `Params` (input) + typed response model (output) —
  no bare dicts.
- OpenAPI contract exported to `api-contracts/` (repo-wide convention).
- `tests/` — one file per handler group, `imperal_sdk.testing.MockContext` +
  `MockSecretStore`, no live network in tests; separately a small
  `tests/test_pricing.py` that asserts EVERY priced function's declared
  `base_price` covers its worst-case X cost after the 20% platform cut — this
  test is the actual guarantee that we never go negative, enforced in CI, not
  just in this doc.
- `imperal validate .` — must be 0 errors/0 warnings before submit_for_review,
  same bar as every other extension this session.

## 5. Phasing

- **Phase 1 (MVP):** connect, post/delete/like/retweet, home timeline, mentions,
  search, profile lookups, trends. Everything in §2 except DMs.
- **Phase 2:** Direct Messages (elevated scope — X reviews DM access requests
  separately, plan for approval lag).
- **Phase 3:** Lists management, competitor-style public monitoring (search +
  profile reads only, same "look at competitor's public content" idea as
  meta-social-extension already does for FB/IG).

## 6. What blocks Phase 1 from starting — needs YOU, not code

1. **Register the shared X Developer App** (developer.x.com) under our business
   identity — this is an account/ToS decision only the account owner can make,
   same as the Meta App Review case. Need: Client ID + Client Secret (OAuth 2.0),
   and the app's requested scopes (tweet.read, tweet.write, users.read,
   follows.read, follows.write, like.read, like.write, bookmark.read,
   bookmark.write, offline.access at minimum for Phase 1).
2. **Load X API credits** into that app's Developer Console — pay-per-use, no
   free tier, so the app needs a funded balance before Phase 1 can process a
   single real call.
3. Once both exist: drop them in `credentials.txt` (same convention as everything
   else this session) and I wire them into the backend's secrets store.

Everything else in this plan (functions, panels, pricing, tests) can be built and
tested against mocked X responses before those two exist — I'll start there.
