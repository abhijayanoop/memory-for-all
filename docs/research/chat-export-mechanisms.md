# Extracting full chat history from ChatGPT and Claude.ai

Researched 2026-11-20. Tags: [V] verified in a fetched primary source; [S] secondary or search-snippet only; [I] inferred or unverified.
Several OpenAI pages (help.openai.com, openai.com/policies) returned HTTP 403 to my fetcher, so OpenAI help and terms text comes from search-result snippets and a mirror. Re-check against the live pages before relying on exact wording.

## 1. Official data export

### ChatGPT
- Requested in ChatGPT settings or the Privacy Portal. A notice arrives by email or SMS when ready; it can take up to 7 days. The link expires 24 hours after you receive it, and you must be signed in to the requesting account. If it expires, request a new export. [S] https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data (search-result summary; page itself 403 to fetcher)
- Business, Enterprise and Healthcare workspace users must go through their workspace owner; self-service export is unavailable. Plan eligibility differs between article versions. [S] same URL
- ZIP contains conversations in JSON, other account data (JSON/CSV), and an `index.html` local viewer. [S] same URL
- `conversations.json` schema: an array of conversations with `id`, `title`, `create_time`, `update_time`, `mapping`, `current_node`. `mapping` is a tree of nodes `{id, message, parent, children}`; `current_node` marks the active branch. Message: `id`, `author.role`, `create_time`, `content.content_type`, `content.parts`, `metadata.model_slug`. [S] https://tomzxcode.github.io/llm-conversations-viewer/docs/formats. This matches the fields the live web API returns (section 2) [V].
- Incremental: no mechanism documented. Each export is a full snapshot. [I]

### Claude
- Settings > Privacy > "Export data" on the web app or Claude Desktop. It cannot be started from the iOS or Android apps. [V] https://support.claude.com/en/articles/9450526-how-can-i-export-my-claude-data
- A download link is emailed. "The download link will expire 24 hours after it's created, and it may work only once". Sign-in is required. Repeat the export to get a new link. [V] same URL
- Covers conversation data and account user data (plus voice recordings shared). Excludes the original uploaded files. Team and Enterprise exports exclude uploaded-file contents. [V] same URL
- The help page does not specify the file format. [V] Community sources say the ZIP contains `conversations.json`, `projects.json`, `users.json` (naming varies by guide). [S] https://univik.com/help/export-claude-chats.html (via search summary).
- Conversation fields reported by community parsers: `uuid`, `name`, `created_at`, `updated_at`, `chat_messages[]` with `uuid`, `text`, `sender` (`human`/`assistant`), `created_at`. Newer messages may carry `content[]` blocks (`{type, text}`) and leave `text` empty. Treat as [S]. https://tomzxcode.github.io/llm-conversations-viewer/docs/formats, https://docs.rs/pond-db/0.3.2/src/pond/adapter/claude_ai_export.rs.html
- Reported gap: `conversations.json` and `projects.json` are not linked by any key in the export. [S] https://claudeissues.com/issue/40411-claude-ai-data-export-missing-conversation-to-project-associations
- Incremental: none documented. Full snapshot. [I]

Verdict: official export is the most ToS-safe route, but it is manual (email, 24h link, ZIP), slow, and not incremental. It suits a one-time backfill, not continuous sync.

## 2. Internal web-app endpoints (undocumented)

### ChatGPT (chatgpt.com) — source: pionxzh/chatgpt-exporter `src/api.ts`
Fetched: https://raw.githubusercontent.com/pionxzh/chatgpt-exporter/master/src/api.ts [V]
- Auth: `GET /api/auth/session` (cookie session) returns `accessToken`. Every API call sends `Authorization: Bearer <token>` plus `X-Authorization: Bearer <token>`. For workspace/team accounts it adds `Chatgpt-Account-Id`, found by reading the `_account` cookie and looking it up via `/accounts/check/v4-2023-04-27`.
- List: `GET /conversations?offset=N&limit=100` (offset pagination, limit 100). Response: `items[]`, `total`, `cursor`, `has_missing_conversations`. Each item has `id`, `title`, `create_time`, `update_time`, plus flags `is_starred`, `is_archived`, `pinned_time`. No `order` param appears in that code. [I] other exporters reportedly use `order=updated`; I did not verify.
- Fetch one: `GET /conversation/:id` returns `title`, `create_time`, `update_time`, `current_node`, `mapping` (same tree as export).
- Projects ("gizmos"): `GET /gizmos/snorlax/sidebar?conversations_per_gizmo=0&cursor=` and `GET /gizmos/:gizmo/conversations?cursor&limit=50`. Hits the cursor-style pagination, not offset.
- Files: `GET /files/download/:id?post_id&inline=false` returns a signed `download_url`.
- Rate limits: not published. The exporter treats HTTP 429 as `RateLimitError` using `Retry-After` (default 30s, probe default 60s) and logs `x-ratelimit-*` headers. It does not retry, so a 429 leaves partial results.
- Stability: the code shows churn (separate `X-Authorization` header, "snorlax" project sidebar name, `sediment://` file URIs, thinking/reasoning metadata fields), i.e. the API shifts regularly. [I] inferred from code shape, not from a change log.

### Claude (claude.ai) — sources: userscript and extension code
- Base `https://claude.ai/api`. Auth is the browser session cookie only (no token header). `credentials: 'include'`, `Accept: application/json`. [V] https://greasyfork.org/scripts/499310-claude-ai-sharegpt-exporter/code and https://raw.githubusercontent.com/socketteer/Claude-Conversation-Exporter/main/content.js
- Org id: `GET /organizations` and take `[0].uuid` (naive: users with several orgs need to pick). [V] greasyfork script.
- List: `GET /organizations/{orgId}/chat_conversations` — items have at least `uuid`, `name`. The socketteer code reads no pagination params and sends none, so the list appears to return everything in one response. [V] for what the code does; [I] that no server-side cap exists. `updated_at` is present on full conversation objects [V]; whether the list items carry `updated_at` is not shown by either exporter, so verify by inspecting a live response. [I] (community parsers describe it on conversation objects.)
- Fetch one: `GET /organizations/{orgId}/chat_conversations/{id}?tree=True&rendering_mode=messages&render_all_tools=true`. Returns `name`, `created_at`, `updated_at`, `model`, `current_leaf_message_uuid`, `chat_messages[]` with `uuid`, `parent_message_uuid` (root parent is `00000000-0000-4000-8000-000000000000`), `sender`, `created_at`, `content[]` or `text`, `attachments[]` (`file_name`, `file_size`, `file_type`, `extracted_content`). [V]
- Rate limits: not published. socketteer's extension fetches sequentially with a 500 ms delay and its README says it batches "to avoid overwhelming the API". [V] https://github.com/socketteer/Claude-Conversation-Exporter
- Stability: the older userscript reads `text` only; the newer extension handles `content[]` and extra query params. Shows the response shape has evolved. [I]
- Related but different: Anthropic has an official Compliance API for retrieving chats, aimed at organizations (https://platform.claude.com/docs/en/manage-claude/compliance-content-data.md) [S]. I did not verify its eligibility or auth. It is not a consumer solution. [I]

## 3. Terms of use

### OpenAI (Terms of Use, "What you cannot do") [S, quoted from mirror https://open.windriver.com/info/uni-license-list/licenses/openai-tou-20241211.html; live page 403]
- "Automatically or programmatically extract data or Output (defined below)."
- "Interfere with or disrupt our Services, including circumvent any rate limits or restrictions or bypass any protective measures or safety mitigations we put on our Services."
- Official source to re-check: https://openai.com/policies/terms-of-use/ and https://openai.com/policies/row-terms-of-use/. Wording varies by region/version.
- Reading: a script or extension that bulk-pulls your own chats through internal endpoints plausibly falls under the first bullet, even though the data is yours. Legal interpretation is [I]; get actual advice before shipping a product that does this for other users.

### Anthropic (Consumer Terms) [V] https://www.anthropic.com/legal/consumer-terms
- Sec. 3(7): do not "access the Services through automated or non-human means, whether through a bot, script, or otherwise."
- Sec. 3(4): do not "crawl, scrape, or otherwise harvest data or information from our Services other than as permitted under these Terms."
- Also bars "bypassing any of our systems or protective measures."
- Sec. 4: "you retain any right, title, and interest that you have in the Inputs you submit"; Outputs are assigned to you "subject to your compliance with our Terms." The terms contain no clause granting a right to export; the official export is documented only on the help page.
- Reading: user-initiated clicks that make the page's own requests are a gray area; scheduled background scripts are more clearly in the prohibited category. [I]

Net: both services restrict automated access. The official export is the only clearly permitted path. Any automated internal-API path carries ToS risk (account action is the realistic consequence [I]), so it should be opt-in, user-initiated, throttled, and local-only.

## 4. Incremental sync

- ChatGPT: list items expose `update_time` (and `create_time`) [V]. Keep a local map `id -> update_time`; page the list (newest first if ordering is available [I]; otherwise full list scan at 100 per page, cheap), and refetch only conversations whose `update_time` is greater than stored. Stop early only if ordering by update is confirmed.
- Claude: list returns `uuid` and `name` [V]; if list items also include `updated_at` (to be checked live [I]) use the same approach. If not, fall back to fetching each conversation, which is O(n) requests. Claude is linear (leaf plus parent chain), so compare `updated_at` or last message `uuid`.
- Hashing the stored message count or `current_node` / `current_leaf_message_uuid` is a cheap secondary change check. [I]
- Deletions: a conversation missing from the list means deleted or archived; decide whether to tombstone. [I]

## 5. Recommended design

Ranking by maintenance and speed:
1. Official export ZIP: zero API fragility and clearly permitted, but slow and manual. Format changes rarely [I]. Best for backfill.
2. Internal API calls in the user's own logged-in tab (content script or extension service worker): fast (hundreds of conversations per minute at a polite pace), uses the user's session so no credential handling, but undocumented and changing, plus ToS risk.
3. DOM scraping: slowest, most brittle. Last resort.

Layered design:
- Layer 0 (onboarding, always available): import the official export ZIP (drag and drop). Parsers for both schemas into one internal model (conversation id, source, title, created/updated, messages with role/text/time, raw JSON kept). Tolerate unknown fields and both `text` and `content[]`.
- Layer 1 (primary for ongoing sync): content script running in the chatgpt.com / claude.ai tab, user-triggered or triggered when the user opens the site, calling the internal endpoints above with the page's own session. Throttle (about 500 ms between calls as socketteer does), honor `Retry-After`, back off on 429, and resume after partial failure (pionxzh stops instead of retrying; do better). Sync using the `update_time` diff in section 4. Keep all data local.
- Layer 2 (fallback when endpoints break): schema-drift detection (required fields missing triggers a visible "sync degraded" state, not silent loss), then prompt the user to request a fresh official export and import it; dedupe by conversation id plus `update_time`.
- Optional Layer 3: DOM or "copy conversation" scraping for the currently open chat only.
- Maintenance tactics: isolate endpoint definitions and response adapters in one small file per site; keep fixtures of real responses for tests; track upstream exporters (pionxzh/chatgpt-exporter, socketteer/Claude-Conversation-Exporter) for breakage reports. [I]

## Gaps and things to verify live
- Live ToS text of OpenAI (403 to fetcher).
- Whether claude.ai list items include `updated_at`, and any pagination or limit params.
- Whether ChatGPT `/conversations` supports `order=updated`.
- Real export ZIP filenames and sharding (e.g. split `conversations-NNN.json` for large histories) for both services; not verified.
- Actual rate-limit thresholds for either service (none published).
- Compliance API eligibility for Anthropic.

## Live probe results (2026-11-20, user's own claude.ai session) [V]
- Claude list (`/api/organizations/{org}/chat_conversations`) returned all 320 conversations in one response, no pagination. Items carry `updated_at`, `created_at`, `name`, `summary`, `project_uuid`, `is_archived`, `current_leaf_message_uuid`, `model`. So incremental sync needs only the list call, then fetch changed chats.
- `/api/organizations` returned 2 orgs. The Reader must pick the right one, not blindly `[0]`.
- Single chat has `chat_messages[]` with both `text` and `content`, plus `parent_message_uuid`, `index`, `attachments`, `files`.
- ChatGPT probe [V]: base path `/backend-api` works with the session token. List items have `update_time`, `create_time`, `is_archived`, `gizmo_id`, `snippet`. `order=updated` accepted and equals the default order (newest updated first). Single chat returns `mapping` + `current_node`. The test account had only 6 chats, so large-history speed and rate limits are untested.
