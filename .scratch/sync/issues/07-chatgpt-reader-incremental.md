# 07: ChatGPT Reader with incremental Sync

**What to build:** The user syncs ChatGPT from an open chatgpt.com tab. The first Sync saves every chat. Later Syncs read the list newest-updated first and stop at chats older than the last completed Sync, so a daily Sync costs a few calls. Saved text matches what the user saw: only the active branch, no hidden messages, and rich-UI markup turned into its displayed text. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Sync run" step 1, "Readers: conversion rules" (ChatGPT); stories 12, 14, 21, 22, 24, 29).

**Blocked by:** 05 (Extension skeleton and a first Claude Sync, end to end)

**Status:** ready-for-agent

- [ ] ChatGPT Reader: bearer token from `/api/auth/session`, list via `/backend-api` with `offset`/`limit=100`, fetch `/backend-api/conversation/{id}`
- [ ] Incremental: stop at the first item whose update time is not newer than the program's watermark; a first run (no watermark) and a "Full sync" popup button list everything
- [ ] `full_list` is sent only when the whole list was read
- [ ] Walk `mapping` from `current_node` up through `parent` to the root, then reverse
- [ ] Keep `user` and `assistant` text (text parts of multimodal content); drop system, tool and visually hidden messages
- [ ] Unix-second times become ISO UTC; attachment names come from message metadata
- [ ] Rich-UI markup (`<badge>`, `<Entity value="...">` and similar) becomes the text it displays, tested with scrubbed snippets from the user's real answers
- [ ] Vitest through `syncPlatform`: first sync saves all; incremental stops at the watermark (call count); branched fixture; hidden messages dropped; markup to plain text; `full_list` only on full runs
- [ ] Record in the research doc: whether the default list includes archived chats, and the full set of rich-UI tags found in the user's chats
