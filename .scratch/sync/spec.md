# Spec 5: Sync (ChatGPT and Claude)

Status: ready-for-agent

Source decisions: `docs/spec-plan.md` (spec 5), `.scratch/memory-for-all-v1/issues/01-chatgpt-sync-check.md` (ChatGPT list and fetch shapes, newest-updated order), `02-claude-org-and-edge-chats.md` (organization choice, archived, project and deleted chats), `06-extension-local-link.md` (list-then-send handshake, Readers run in an open tab, Chrome-family), `09-kb-file-layout.md` (file per Conversation, re-sync rule, gone marking), `04-context-pack-format.md` (the Reader strips platform markup), `docs/research/chat-export-mechanisms.md` (endpoints, live probe results, layered design, terms of use). Builds on spec 1 (`.scratch/knowledge-base-and-chunking/spec.md`: the Platform-neutral Conversation, save, mark gone/present). Vocabulary: `GLOSSARY.md` (Platform, Conversation, Sync, Reader, Knowledge Base). ADR 0001 applies.

Seams settled with the user (2026-11-24): one seam per language (a sync action in the extension, the handshake in the program); a bare local link now and the pairing key in spec 6; the official export ZIP is read by the same Reader in the extension.

## Problem Statement

The Knowledge Base exists, but the only way to fill it is to hand-make Platform-neutral JSON files and run `import`. My real Conversations are still locked inside ChatGPT and Claude, and they keep changing: I add new chats every day, continue old ones, archive some, move some into projects and delete a few. Without Sync, my Knowledge Base goes out of date the day I fill it, and every Context Pack misses my latest decisions.

Both Platforms only offer an official export that takes up to days, arrives by email and is a full snapshot each time. Their web apps do have internal endpoints that my logged-in tab can call, but those are undocumented and change without warning. When they change, I need to find out right away and not discover months later that half my chats stopped saving. I also need a way to keep going (the official export) and a quick way to capture what broke so the Reader can be fixed.

## Solution

A Chrome extension with one Reader per Platform. While a ChatGPT or Claude tab is open, the Reader runs inside it, using my own logged-in session. It lists my Conversations and asks the local program which ones it needs (new or changed since the last save). Then it fetches only those, one at a time at a polite pace, turns each into the Platform-neutral Conversation and sends it to the program, which saves it with spec 1's save rules. It keeps only the active branch and the text, and it turns ChatGPT's rich-UI markup into the plain text I saw. Archived and project chats are saved and marked. Chats I deleted on the Platform keep their file, marked "no longer on the Platform".

If the Platform's responses no longer look as expected, Sync does not quietly skip chats. It stops that Platform, shows a **"sync degraded"** banner with the reason and offers two ways forward. **Guided export** walks me through requesting the official export and dropping the ZIP into the extension, and the same Reader reads it. **Report this** builds a short report of what broke (field names and error codes only, none of my chat text) that I can save or copy.

The program runs with one command (`memoryforall serve`) and listens only on my own computer. After a sync finishes it refreshes the search index in the background. The pairing key that stops other websites from using this address comes in spec 6.

## User Stories

### Running Sync

1. As a user, I want Sync to run inside an open ChatGPT or Claude tab using my existing login, so that I never give the program my password or a token.
2. As a user, I want Sync to start by itself when I open a ChatGPT or Claude tab, at most once an hour per Platform, so that my Knowledge Base stays current without me remembering.
3. As a user, I want a "Sync now" button per Platform in the extension, so that I can pull a chat I just finished straight away.
4. As a user, I want the extension to tell me "open claude.ai to sync Claude" (or chatgpt.com) when no tab of that Platform is open, so that I know why nothing happened.
5. As a user, I want a one-time notice before the first Sync explaining that it reads my chats from my own logged-in tab, slowly, and keeps everything on my computer, and that both Platforms' terms restrict automated access, so that I choose it knowingly.
6. As a user, I want automatic Sync off until I accept that notice, so that nothing runs without my say.
7. As a user, I want to see progress while a Sync runs ("Claude: 12 of 40 chats"), so that I know it is working.
8. As a user, I want to see when each Platform last synced successfully and how many chats were new, updated or unchanged, so that I can trust what is in my Knowledge Base.
9. As a user, I want only one Sync per Platform at a time, so that two open tabs do not fetch the same chats twice.
10. As a user, I want the extension to say "app not running, start it with `memoryforall serve`" when it cannot reach the program, so that I know what to do.

### Fetching only what changed

11. As a user, I want the first Sync to save every Conversation I have, so that my whole history is in the Knowledge Base.
12. As a user, I want later Syncs to fetch only chats that are new or changed since they were last saved, so that Sync is quick and light on the Platform.
13. As a user, I want the program to decide which chats it needs, based on what is already saved, so that the files are the only record of what is synced (ADR 0001).
14. As a user, I want ChatGPT's list read newest-updated first and stopped once it reaches chats older than my last completed Sync, so that a daily Sync costs a handful of calls, not hundreds.
15. As a user, I want an interrupted Sync to pick up where it left off next time, without missing older changed chats, so that a closed tab or a rate limit never leaves gaps.
16. As a user, I want a chat that was archived, unarchived or moved into or out of a project to be updated even if its update time did not change, so that those marks stay correct.

### Being polite to the Platform

17. As a user, I want Sync to make one request at a time with about half a second between requests, so that it looks like normal use and does not strain the Platform.
18. As a user, I want Sync to wait and retry when the Platform says "too many requests", honouring the wait time it gives, so that a rate limit slows Sync down instead of breaking it.
19. As a user, I want Sync to stop after a few rate-limit retries and finish the rest next time, keeping everything already saved, so that it never hammers the Platform.

### What gets saved

20. As a user, I want each chat saved through the same save rules as `import` (one file per chat, my notes kept, older or equal update time changes nothing), so that Sync and import behave the same.
21. As a user, I want only the active branch of a branched chat saved, so that the file reads as the conversation I actually had.
22. As a user, I want only my messages and the assistant's visible answers saved, not hidden system, tool or reasoning messages, so that the file matches what I saw.
23. As a user, I want attachments recorded as a line naming the file ("not saved"), so that I know a file was there.
24. As a user, I want ChatGPT's rich-UI markup turned into the plain text it displays, so that Context Pack quotes from those answers match exactly.
25. As a user, I want archived chats saved and marked as archived in their file, so that I can still find them and see they were archived.
26. As a user, I want project chats saved with the project name in their file, keeping the usual Platform/month folders, so that I can tell which project a chat came from.
27. As a user, I want a chat I deleted on the Platform to keep its file, marked "no longer on the Platform" with the date it was noticed, so that I never lose history by tidying up on the Platform.
28. As a user, I want a chat that reappears (for example one I unarchived) marked as on the Platform again, so that the mark stays true.
29. As a user, I want deleted chats detected only by a Sync that saw the whole list, so that an early-stopped incremental Sync never wrongly marks chats as gone.
30. As a user, I want the search index refreshed in the background after a Sync, so that new chats are searchable without running `reindex` myself.

### Claude organization

31. As a user with more than one Claude organization, I want to pick which one to sync the first time, from a list showing their names, so that the right chats are saved.
32. As a user, I want that choice remembered and changeable later in the extension settings, so that I pick once.
33. As a user with only one Claude organization, I want no question asked, so that setup stays short.

### Loud failure

34. As a user, I want Sync to check every response for the fields it needs and stop that Platform with a "sync degraded" state when they are missing, so that a Platform change never silently loses chats.
35. As a user, I want the "sync degraded" banner to say which Platform, since when and in plain words what went wrong, so that I understand it.
36. As a user, I want a badge on the extension icon while a Platform is degraded, so that I notice even without opening the popup.
37. As a user, I want `memoryforall status` to show each Platform's last good Sync and any degraded state, so that I see the same truth from the command line.
38. As a user, I want "please log in to claude.ai" instead of "degraded" when the Platform says I am logged out, so that a simple fix is not reported as breakage.
39. As a user, I want unknown extra fields in responses ignored, so that harmless Platform additions do not trigger the banner.
40. As a user, I want one malformed chat to mark Sync degraded but still keep the chats already saved, so that I lose nothing that worked.
41. As a user, I want the degraded state cleared by the next successful Sync of that Platform, so that the banner goes away once things work again.

### Guided export

42. As a user, I want the degraded banner to offer "Use an official export instead", so that I can keep my Knowledge Base current while the Reader is broken.
43. As a user, I want step-by-step instructions for requesting the export on that Platform (where to click, that it arrives by email, how long it may take, that the link expires), so that I do not have to look it up.
44. As a user, I want to drop the export ZIP into an extension page and have it imported, so that I do not have to unzip or convert anything.
45. As a user, I want the export read by the same Reader as live Sync, so that a chat looks the same whichever way it arrived.
46. As a user, I want export chats that are already saved with the same or newer update time to change nothing, so that importing an old export never overwrites newer chats.
47. As a user, I want the export import to show how many chats were new, updated, unchanged or rejected, with reasons for the rejected ones, so that I know what happened.
48. As a new user, I want to use the export import to load my whole history on day one, so that I do not wait for a long first live Sync.
49. As a user, I want the export import never to mark chats as gone, so that an old export cannot wrongly mark newer chats as deleted.

### Report this

50. As a user, I want a "Report this" button on the degraded banner, so that I can capture what broke in one click.
51. As a user, I want the report to hold only the Platform, the step that failed, the request path without chat IDs, the HTTP status, the missing fields, the field-name outline of the response (names and types, no values), the extension and Reader versions and the time, so that none of my chat text leaves in it.
52. As a user, I want to read the report before doing anything with it, then copy it or save it as a file, so that I decide where it goes.
53. As a user, I want the report never sent anywhere automatically, so that Sync stays local.

### The local program

54. As a user, I want to start the program with `memoryforall serve`, so that the extension has something to sync into.
55. As a user, I want the program to listen only on my own computer (127.0.0.1), so that other machines cannot reach it.
56. As a user, I want the program to refuse requests that do not come from a browser extension, so that ordinary websites cannot write into my Knowledge Base before the spec 6 pairing key exists.
57. As a user, I want the program to reject a Conversation that fails validation with a reason, so that bad data never reaches my files.

### Developer

58. As a developer, I want each Platform's endpoints, field checks and conversion kept in that Platform's own Reader, so that a change on one Platform touches only one Reader.
59. As a developer, I want the whole Sync run testable through one action with a fake fetch, a fake program and a fake clock, so that throttling, retries and drift are tested in milliseconds without a browser.
60. As a developer, I want test fixtures recorded from real responses with the chat text replaced by made-up text, so that tests reflect real shapes without committing my chats.
61. As a developer, I want the handshake messages defined once as shared fixtures that both the TypeScript and the Python tests use, so that the two sides cannot drift apart.
62. As a developer of spec 6, I want the local link to be a small server that spec 6 extends with the pairing key and the Context Pack request, so that nothing is built twice.
63. As a developer of spec 7, I want Sync to save chats one by one through the existing save action, so that its speed can be measured and improved without changing the contract.

## Implementation Decisions

### Two parts, one contract

- **Extension (TypeScript, Chrome Manifest V3, Chrome-family browsers):** a new top-level folder in the repo, separate from the Python package and the prototype. It has the Readers, the Sync run, the popup (Sync now, progress, last Sync, banner, Report this), an options page (Claude organization, auto-sync on/off) and the export import page. Tests run with Vitest. The Readers' fetch calls run in a content script in the Platform tab, so they use the page's own session.
- **Program (Python):** the existing package, plus a `serve` command, a sync handshake on top of the Knowledge Base, and per-Platform sync state.
- **Contract:** the existing Platform-neutral Conversation (spec 1), extended as below, plus three handshake messages. Example messages live as shared JSON fixtures used by both test suites.

### Platform-neutral Conversation additions

- Two optional fields: `archived` (bool, default false) and `project` (string or null, the project's name).
- Front matter gains `archived: true` and `project: "<name>"` only when set, so existing files and Obsidian keep working. `parse` and `render` round-trip them.
- The save rule changes in one way: a file is rewritten when the incoming update time is newer **or** `archived`/`project` differ from the file. Notes are kept as before.

### Handshake (program side, seam B)

A small sync module over `KnowledgeBase`, exposed as three local HTTP endpoints by `serve`:

1. **needs**: in `{platform, items: [{chat_id, updated, archived, project}]}`; out `{needed: [chat_id]}`. A chat is needed when it has no file, the incoming `updated` is newer, or `archived`/`project` differ.
2. **save**: in `{conversation}`; out `{result: created|updated|renamed+updated|unchanged}` or a rejection with the validation reason. It calls the existing save action.
3. **finish**: in `{platform, outcome: ok|degraded|interrupted|logged_out, reason?, watermark?, full_list?: [chat_id]}`; out the stored sync state.
   - `ok` with `watermark` records it as the Platform's "synced through" time. The watermark is only advanced by a run that completed.
   - `full_list` (sent only when the run listed the whole Platform list) marks every saved chat of that Platform not in the list as gone (`mark_gone`, noticed now), and every chat in the list that was marked gone as present again.
   - `degraded` records the reason and the time it started. Any later `ok` clears it.
   - After `finish`, the program starts a background index refresh (one at a time; if a refresh is already running, one more is queued).
- A fourth read-only endpoint returns the sync state (per Platform: last good Sync, watermark, last counts, degraded reason and since when), which the popup and `status` use.
- **Sync state** is stored as a small JSON file in a hidden folder inside the Knowledge Base folder, next to `.index/` but separate from it, because the index is disposable and this is not. Losing it is harmless: the next run behaves like a first run, and the save rules keep that cheap.
- **The bare local link:** `memoryforall serve` binds 127.0.0.1 on a fixed default port (a setting, overridable by a flag). It uses the standard library's threaded HTTP server, so no new dependency is added. It accepts only requests whose `Origin` is a `chrome-extension://` origin and answers CORS preflight for those. Spec 6 adds the pairing key on top of this check, plus the "app not running" detection and the Context Pack endpoint.
- `memoryforall status` adds one line per Platform: last good Sync, or `sync degraded since <date>: <reason>`.

### Sync run (extension side, seam A)

One action: `syncPlatform(platform, deps)`, with `deps = {fetch, program, clock, settings}`. A second entry, `importExport(zipFile, deps)`, shares the same Reader. Everything below is behind these two actions.

- **Reader interface (one per Platform):** list the Conversations (with id, title, created, updated, archived, project), fetch one, convert a fetched or exported Conversation to the Platform-neutral form, and declare the required fields for each response. Endpoints and field checks live only in the Reader.
- **Run steps:**
  1. List. Claude: one call returns everything (live probe: 320 chats in one response), so every Claude run is a full list. ChatGPT: page with `offset`/`limit=100` in newest-updated order. Stop at the first item whose update time is not newer than the program's watermark. A first run (no watermark) or a user-chosen "Full sync" lists everything.
  2. Ask **needs** in batches.
  3. Fetch each needed chat in list order, convert it, then **save**. Each chat is saved as soon as it is fetched, so an interruption keeps the work done.
  4. **finish**, with `full_list` only when the whole list was read. The watermark is the newest update time seen, sent only on `ok`.
- **Interrupted runs:** because the watermark only advances on a completed run, the next run re-lists down to the old watermark. The needs step skips everything already saved, so the run resumes without gaps and without refetching.
- **Pace:** sequential, at least 500 ms between requests to the Platform. On HTTP 429, wait for `Retry-After` (30 s if absent) and retry, up to 3 times per request. After that, `finish` with `interrupted`. These numbers are constants in one place.
- **Errors:**
  - 401/403 or a login page → `logged_out` ("please log in to <Platform>"), not degraded.
  - Missing required fields, an unexpected status (404, 5xx after one retry) or a conversion error → `degraded` with a plain reason naming the step and the fields. Unknown extra fields are ignored.
  - A failing chat stops the run. Chats already saved stay saved.
- **Locking:** one run per Platform at a time across all tabs, held by the extension's background worker.
- **Triggers:** opening a Platform tab (at most once an hour per Platform, only after the user accepted the first-run notice and auto-sync is on), and "Sync now" / "Full sync" in the popup.

### Readers: conversion rules

- **ChatGPT:**
  - Base `/backend-api`, bearer token from `/api/auth/session`.
  - List items: `id`, `title`, `create_time`, `update_time`, `is_archived`, `gizmo_id`.
  - Fetch `/backend-api/conversation/{id}`. Walk `mapping` from `current_node` up through `parent` to the root, then reverse.
  - Keep `user` and `assistant` messages whose content is text (text parts of multimodal content). Skip system, tool and visually hidden messages.
  - Unix-second times become ISO UTC.
  - Attachment names come from message metadata.
  - Rich-UI markup (`<badge>`, `<Entity value="...">` and similar tags) becomes the text it displays. The rule is tested with snippets taken from the user's real answers, scrubbed.
- **Claude:**
  - Base `/api`, session cookie only.
  - `/api/organizations` → the saved organization (see below).
  - List `/organizations/{org}/chat_conversations`: `uuid`, `name`, `created_at`, `updated_at`, `is_archived`, `project_uuid`.
  - Fetch with `tree=True&rendering_mode=messages`. Walk from `current_leaf_message_uuid` through `parent_message_uuid` to the root.
  - Text comes from `content[]` text blocks, or `text` when `content` is absent. Other block types are dropped.
  - `human` becomes user. Attachment and file names become attachment lines.
- **Project names:** the Reader resolves a project id to its name (Claude: the org's projects list; ChatGPT: the project/gizmo lookup), caching names for the run. If a name cannot be resolved, it stores the id as the project and notes it in the run's counts. That is not degraded, because the chat itself is intact.
- **Claude organization:** if `/api/organizations` returns more than one, the popup lists them by name and the user picks one. The choice is saved in extension storage and changeable in options. A saved organization that no longer exists asks again. With one organization nothing is asked.
- **Export ZIP:** `importExport` unzips in the browser (a small zip library), finds `conversations.json` (or numbered shards) and converts each item with the same Reader rules. The ChatGPT export has the same `mapping`/`current_node` shape. The Claude export has `chat_messages` without project links, so project is left empty and the save rule does not clear an existing project in that case. It then runs needs → save like a live Sync and calls `finish` with `ok` but without `full_list` or watermark, so exports never mark chats gone and never move the watermark.

### Banner, guided export, report

- **Degraded state** is shown in the popup banner and as a badge on the extension icon, read from the program's sync state so the CLI and extension agree.
- **Guided export** is a static page per Platform: where the export button is, that it arrives by email (ChatGPT may take up to 7 days and the link expires after 24 hours), then a drop zone that runs `importExport` and shows the counts and rejection reasons.
- **Report this** builds a JSON report in memory:
  - Platform, step, request path with ids replaced by placeholders, HTTP status, missing fields;
  - the response outline (keys and value types, arrays trimmed to their first element, no values);
  - extension and Reader versions, time.
  It shows the report in a read-only box with Copy and Save buttons. Nothing is sent.

## Testing Decisions

- **Good tests** check behaviour at the two seams only: what the program saves and reports given handshake messages, and what `syncPlatform` / `importExport` send to the program given Platform responses. They never test Reader internals, private helpers or call order, except the call counts that are the behaviour (pacing, early stop, no refetch).
- **Seam A (TypeScript, Vitest):** `syncPlatform` and `importExport` with:
  - a fake fetch that routes paths to fixtures;
  - an in-memory fake program implementing needs/save/finish over a map;
  - a fake clock, so the 500 ms gap and `Retry-After` waits are asserted without real waiting.

  Cases:
  - first sync saves all;
  - incremental ChatGPT stops at the watermark;
  - an interrupted run resumes with no gap and no refetch;
  - archived/project changes are picked up;
  - active-branch walk on a branched fixture for each Platform;
  - hidden/system/tool messages dropped;
  - attachments become names;
  - ChatGPT markup becomes plain text;
  - Claude `content[]` vs `text`;
  - multiple organizations ask, one does not, and the saved one is used;
  - 429 with and without `Retry-After`, then interrupted after 3;
  - a missing required field leads to degraded with the field named and earlier saves kept;
  - 401 leads to logged_out;
  - unknown extra fields are ignored;
  - `full_list` is sent only on full runs;
  - export ZIP (both Platforms, sharded ChatGPT) imports and never sends `full_list` or watermark;
  - the report contains no string value from the fixture's chat text.
- **Fixtures:** recorded from the user's real responses (the probes in `prototype/probe/`), with every text and title value replaced by made-up text and ids by fake ones. Real raw responses stay in the gitignored prototype data folder.
- **Seam B (Python, pytest):** the sync module through the real `serve` HTTP server started on a free port in-process, with the fake embedder from `tests/conftest.py`:
  - needs (new, newer, same, older, archived/project changed);
  - save results and rejection reasons;
  - finish with `full_list` (gone and back again, notes kept);
  - the watermark advances only on ok;
  - degraded set then cleared;
  - the state file is missing or damaged, and the next run still works;
  - requests without a `chrome-extension://` Origin are refused, and CORS preflight is answered;
  - a background refresh after finish makes the new chat searchable;
  - `status` prints the per-Platform line;
  - `archived`/`project` round-trip in `parse`/`render`, and files without them still parse.
- **Contract:** the shared handshake fixtures are sent by the TypeScript fake-program tests and replayed against the Python server in pytest, asserting the same answers.
- **Prior art:** `tests/test_import.py` (save rules, mark gone/present, counts), `tests/test_rebuild.py` (refresh after file changes), `tests/conftest.py` (fake embedder). The prototype's `prototype/convert.py` shows the ChatGPT tree walk and Claude message reading to match, but it is not test code. The extension has no prior tests; this spec sets up its test runner.
- **Manual live check** (not automated, listed in the PR): one live Sync of each Platform on the user's account. It confirms 320 Claude chats, an incremental ChatGPT run stopping early, an archived and a project chat marked, and a deliberately renamed required field producing the banner and a report.

## Out of Scope

- The pairing key, "app not running" detection beyond a failed connection message, the Context Pack request, preview, text insertion and the working indicator: spec 6.
- Auto-starting the program at login; packaging the extension for the Chrome Web Store.
- Gemini and other Platforms.
- Non-active branches, attachment contents and images (text-only lines as in ticket 09).
- Deleting or forgetting chats locally; the file is never deleted.
- A stale-sync warning ("Claude not synced for 2 weeks").
- Project files and instructions (only the project name is stored).
- Sending reports anywhere, the scheduled test-account check, and an agent that drafts Reader fixes.
- DOM scraping of the open chat (research's optional Layer 3).
- Speed at large histories: spec 7.

## Further Notes

- **Terms of use:** both Platforms restrict automated access. Sync is user-enabled, runs only in the user's own logged-in tab, is slow and sequential, and keeps everything local. The official export is the fully permitted path and is always offered.
- **Until spec 6 ships,** the local link is protected only by the 127.0.0.1 bind and the extension-origin check. A browser sets `Origin` honestly for web pages, but other local programs could still call it. This is acceptable for one user on their own machine and closed by spec 6's pairing key.
- **To verify live during implementation** (record results in the research doc):
  - whether ChatGPT's default list includes archived chats or needs `is_archived=true`;
  - the endpoint that gives ChatGPT project names, and Claude's projects list;
  - whether archiving or moving a chat changes its update time;
  - the real export ZIP file names and sharding for both Platforms;
  - the full set of ChatGPT rich-UI tags in the user's chats.
- Rate-limit thresholds are unknown for both Platforms. The 500 ms gap and 3 retries are a starting point. Spec 7 measures large-history Sync speed.
- After this spec, the bare `import` of Platform-neutral JSON stays as the developer and test path. Users use Sync or the export import.
