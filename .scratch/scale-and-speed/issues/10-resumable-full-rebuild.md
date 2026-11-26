# 10: Resumable full rebuild with progress

**What to build:** A full rebuild (after a model switch or a chunk rule change) may take hours. If it is interrupted by a closed laptop, crash, Ctrl-C or a failed embedding call, the next run continues where it stopped instead of starting over. The old index stays live until the swap, and the user sees progress and an estimate of time left. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Known fixes": resumable full rebuild; stories 40 to 45).

**Blocked by:** 07 (Incremental reindex skips unchanged files)

**Status:** ready-for-agent

- [ ] The rebuild writes into the side index as today, committing every few hundred Conversations
- [ ] On interruption or an embedding failure the side index is kept, not deleted; the live index stays live
- [ ] The next rebuild continues a side index built with the same embedder, dimension and rules version (files it holds with matching fingerprints are skipped); a side index with different ones is deleted and started over
- [ ] Conversations changed during a rebuild are picked up by it or by the next refresh
- [ ] Progress (done of total, Conversations per minute, estimated time left) printed to standard error
- [ ] Existing tests pass unchanged (safe swap, model switch)
- [ ] New tests with a counting embedder that fails after N Conversations: the live index stays searchable; the next rebuild with a working embedder completes and makes fewer embed calls than a fresh one; a side index from another embedder is discarded

- [ ] After this fix, run the existing test suite and have the user run `quality score` on a fresh run of the real Test Set and `bench run` at 100,000 Conversations; record the results in Comments. Keep the fix only if all five quality checks pass; otherwise adjust or revert it
