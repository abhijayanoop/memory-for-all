# 05: Extension skeleton and a first Claude Sync, end to end

**What to build:** The user loads the extension, opens claude.ai, presses "Sync now" and watches progress ("Claude: 12 of 40 chats") while every Claude Conversation lands in the Knowledge Base, read from their own logged-in tab. This ticket sets up the extension and its tests, and proves the full path with the Claude Reader for a single organization. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Two parts, one contract", "Sync run", "Readers: conversion rules" (Claude); stories 1, 3, 7, 11 to 13, 20 to 23, 58 to 61).

**Blocked by:** 03 (finish and the sync state)

**Status:** ready-for-agent

- [ ] A new top-level extension folder (TypeScript, Chrome Manifest V3, Chrome-family browsers) with Vitest, separate from the Python package and the prototype
- [ ] One action `syncPlatform(platform, deps)` with `deps = {fetch, program, clock, settings}`; Platform fetch calls run in a content script in the Platform tab, using the page's own session
- [ ] The Reader interface (list, fetch one, convert, required fields per response) with the Claude Reader behind it: `/api/organizations` (single organization), list chats (every Claude run is a full list), fetch with `tree=True&rendering_mode=messages`, walk from the current leaf to the root, text from `content[]` text blocks or `text`, `human` → user, attachment and file names → attachment lines
- [ ] Run steps: list → needs in batches → fetch, convert and save each chat as soon as it is fetched → `finish` ok with `full_list` and the newest update time as the watermark
- [ ] Popup with "Sync now" and progress
- [ ] Fixtures recorded from the probes in the prototype folder, with every text, title and id replaced by made-up values; real responses stay in the gitignored prototype data folder
- [ ] Vitest with fake fetch, in-memory fake program and fake clock: first sync saves all; a branched fixture keeps only the active branch; `content[]` vs `text`; attachments become names; `full_list` is sent
- [ ] The TypeScript fake program answers the shared handshake fixtures exactly as the Python server does
- [ ] Manual live check (listed in the PR): one live Claude Sync of the user's account saves their chats (about 320), and they are searchable after the background refresh
