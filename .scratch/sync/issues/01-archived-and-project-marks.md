# 01: Archived and project marks on a Conversation

**What to build:** A Conversation can say it is archived and which project it belongs to, and the Knowledge Base file keeps those marks. Re-saving a chat whose marks changed rewrites its file even when its update time did not change. Verifiable today through `import`. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Platform-neutral Conversation additions"; stories 16, 25, 26).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] The Platform-neutral Conversation accepts optional `archived` (bool, default false) and `project` (string or null); wrong types are rejected with a reason
- [ ] Front matter gains `archived: true` and `project: "<name>"` only when set; files without them still parse, and existing files are unchanged
- [ ] `parse` and `render` round-trip both fields
- [ ] Save rewrites the file when the incoming update time is newer **or** `archived`/`project` differ; notes are kept; otherwise `unchanged` as before
- [ ] Tests alongside the existing import tests: round-trip, old files still parse, an archive-only change re-saves, the same marks with an equal time change nothing
