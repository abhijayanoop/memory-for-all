# 05: Refresh only what changed

**What to build:** Running `reindex` on a Knowledge Base that already has an index redoes only the Conversation files that are new or changed, and drops Chunks of files that were deleted. Hand edits, including edits to notes, show up after a refresh. A file the user broke by hand never costs them data. See the spec (Index: refresh; user stories 49-51, 55-56).

**Blocked by:** 03

**Status:** resolved

- [ ] Refresh compares each file's fingerprint (content hash) with the index and re-chunks only new and changed files; unchanged files are not re-embedded
- [ ] Chunks of files no longer on disk are removed
- [ ] A file that cannot be parsed (for example a damaged header) is skipped with a warning; it is not modified or deleted, and its previous Chunks stay in the index
- [ ] Markdown files that are not Conversations are ignored
- [ ] `refresh_index()` returns, and `reindex` prints, counts of files added, changed, removed and skipped
- [ ] Knowledge Base tests cover new, edited (messages and notes), deleted, broken and non-Conversation files

## Answer

Implemented on branch `integration/knowledge-base-and-chunking`.
