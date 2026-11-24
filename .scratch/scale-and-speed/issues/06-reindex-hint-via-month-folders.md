# 06: Reindex hint without opening every file

**What to build:** The "files changed since the last reindex" hint keeps working but no longer checks every Conversation file on each search. It compares the index's last refresh time with the modification times of the Platform month folders, which change on every save, rename and removal. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Known fixes": reindex hint; stories 25, 26).

**Blocked by:** 04 (Baseline measurement)

**Status:** ready-for-agent

- [ ] The hint compares the last refresh time with the month folders' modification times (a few hundred folders), not every file
- [ ] Shown after a save, rename or removal by the program or Sync that is not yet indexed; not shown after a refresh with no changes
- [ ] A hand edit that rewrites a file in place may not show the hint; accepted and noted in a `shortcut:` code comment
- [ ] Existing tests pass unchanged
- [ ] New tests: the hint appears after `save` of a new or changed Conversation and disappears after a refresh; no hint when nothing changed
