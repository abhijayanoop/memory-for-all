# 05: Meaning search with numpy, and reading only what search needs

**What to build:** Search over a large Knowledge Base stops loading every Chunk and computing similarity one number at a time. Meaning search uses one numpy product over a vector matrix that refresh keeps on disk and search reads as needed, search fetches only the Chunks it will fuse and re-rank, and "the index is empty" is answered instantly. Results stay the same as before. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Known fixes": meaning search with numpy, read only what search needs; stories 22 to 24, 27).

**Blocked by:** 04 (Baseline measurement), spec 4 tickets 04 (`.scratch/quality/issues/04-hand-marks-and-full-scoring.md`) and 05 (`.scratch/quality/issues/05-current-decision-check.md`)

**Status:** ready-for-agent

- [ ] numpy becomes a direct dependency (already installed through fastembed)
- [ ] `refresh_index` writes the stored Chunk vectors as one float32 matrix in the index folder whenever Chunks changed, swapped in atomically like the index; search memory-maps it
- [ ] Similarity is one matrix-vector product; the top `MEANING_TOP` by partial sort; rank fusion and its tie rule unchanged
- [ ] A missing or mismatched matrix → keyword-only search with spec 2's notice; the next refresh rebuilds it from the stored vectors
- [ ] Search fetches text and labels only for the fused candidates, by id; the empty-index check is a count query
- [ ] No rules version change; existing tests pass unchanged
- [ ] New tests at the Knowledge Base seam with the fakes: after a refresh, added and changed Chunks are found and removed ones are not; a deleted or damaged matrix gives keyword-only results with the notice, and the next refresh restores meaning search; an empty index gives the empty-index message
- [ ] `bench run` at 100,000 recorded in Comments, compared with the baseline

- [ ] After this fix, run the existing test suite and have the user run `quality score` on a fresh run of the real Test Set and `bench run` at 100,000 Conversations; record the results in Comments. Keep the fix only if all five quality checks pass; otherwise adjust or revert it
