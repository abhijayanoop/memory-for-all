# 12: Guided export and ZIP import

**What to build:** When Sync is degraded, or on day one to load the whole history, the user follows step-by-step instructions to request the official export, then drops the ZIP onto an extension page. The same Reader reads it, and the user sees how many chats were new, updated, unchanged or rejected. An export never overwrites newer chats and never marks chats as gone. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Readers: conversion rules": Export ZIP; "Banner, guided export, report": Guided export; stories 42 to 49).

**Blocked by:** 07 (ChatGPT Reader with incremental Sync), 09 (Loud failure: degraded, logged out, banner and badge)

**Status:** ready-for-agent

- [ ] The degraded banner offers "Use an official export instead", which opens a guided page per Platform: where the export button is, that it arrives by email, that ChatGPT may take up to 7 days and the link expires after 24 hours
- [ ] A drop zone on that page runs `importExport(zipFile, deps)`: it unzips in the browser with a small zip library, finds `conversations.json` or numbered shards, and converts each item with the same Reader rules
- [ ] Then needs → save as in a live Sync, and `finish` with `ok` but no `full_list` and no watermark
- [ ] A Claude export (no project links) leaves project empty, and the save rule does not clear an existing project in that case
- [ ] The page shows new/updated/unchanged/rejected counts, with reasons for rejected chats
- [ ] Vitest: a ChatGPT export, a sharded ChatGPT export and a Claude export import; `full_list` and watermark are never sent; an older export changes nothing
- [ ] Record in the research doc: the real export ZIP file names and sharding for both Platforms
