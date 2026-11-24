# 10: Project names and archived chats, live

**What to build:** Both Readers save archived chats and chats in projects with their marks, showing the project's name. Archiving, unarchiving or moving a chat between projects updates its file on the next Sync, even if its update time did not change. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Readers: conversion rules": Project names; stories 16, 25, 26, 28).

**Blocked by:** 01 (Archived and project marks on a Conversation), 07 (ChatGPT Reader with incremental Sync)

**Status:** ready-for-agent

- [ ] Both Readers list `archived` and `project` per chat and send them in needs and in the saved Conversation
- [ ] Project ids are resolved to names (Claude: the organization's projects list; ChatGPT: the project/gizmo lookup), cached for the run
- [ ] An unresolvable project name stores the id and is noted in the run's counts; this is not degraded
- [ ] Vitest through `syncPlatform`: an archive-only change and a project move are picked up; an unresolvable name stores the id
- [ ] Record in the research doc: the ChatGPT project-name endpoint, Claude's projects list, and whether archiving or moving a chat changes its update time
