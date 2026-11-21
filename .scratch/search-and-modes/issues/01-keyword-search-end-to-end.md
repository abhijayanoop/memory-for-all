# 01: Keyword search end to end

**What to build:** A user can run `uv run memoryforall search "<request>" [-k N]` and get back the Chunks that share words with their Request, best first, each shown with title, Platform, date, Chunk ID, a notes marker for notes Chunks, and the first ~200 characters of text. The keyword index lives in the same hidden index as the Chunks and stays in step on every refresh. Indexes built by spec 1 are rebuilt once automatically. This ticket adds the Knowledge Base `search(request, k=5)` action that later tickets extend. See the spec: `.scratch/search-and-modes/spec.md` (Search pipeline: Keyword search; Index changes; Command line).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Refresh fills and cleans an FTS5 keyword table in the same transaction as the Chunks (added, changed, removed files)
- [ ] The rules version is bumped, so a spec-1 index is rebuilt through the existing safe swap and is then searchable
- [ ] `search` returns hits (Chunk plus rank), keyword-ranked by BM25, at most `k` (default 5); `k` above the Chunk count returns all matches
- [ ] Request words are each quoted as literal terms and joined with OR, so Requests with quotes, `*`, `-`, `:`, `AND`, `NEAR`, brackets or emoji never error
- [ ] An empty or whitespace-only Request is rejected with a clear message
- [ ] A missing or empty index returns no hits, and the command line says to run reindex
- [ ] Notes Chunks are searchable and marked as notes in results
- [ ] Tests through the Knowledge Base seam with the fake embedder, plus a command-line smoke test of `search`
