# 04: Background index refresh after a Sync

**What to build:** After a Sync finishes, the program refreshes the search index in the background, so newly synced chats are searchable without the user running `reindex`. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Handshake", after `finish`; story 30).

**Blocked by:** 03 (finish and the sync state)

**Status:** ready-for-agent

- [ ] After `finish` the program starts an index refresh without delaying the `finish` answer
- [ ] Only one refresh runs at a time; if one is running, at most one more is queued (further requests fold into it)
- [ ] A refresh failure is logged and leaves the old index live (spec 1's rule); `serve` keeps running
- [ ] pytest through the real server with the fake embedder: save a new chat, `finish`, and the chat becomes findable by `search`; several quick `finish` calls cause at most one running plus one queued refresh
