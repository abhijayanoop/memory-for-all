# 09: Searches keep working during a refresh

**What to build:** A search made while a refresh or rebuild is running answers from the last finished index instead of waiting or failing, so a background refresh after a Sync never blocks the user. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Known fixes": searches during a refresh; story 28).

**Blocked by:** 05 (Meaning search with numpy, and reading only what search needs)

**Status:** ready-for-agent

- [ ] The index uses SQLite's write-ahead log mode, so search reads the last committed index while a refresh writes
- [ ] The vector matrix is swapped only after the refresh commits
- [ ] Existing tests pass unchanged
- [ ] New test: with a refresh blocked inside the embedder on another thread, a search returns the old index's results; after the refresh finishes, a search sees the new Chunks

- [ ] After this fix, run the existing test suite and have the user run `quality score` on a fresh run of the real Test Set and `bench run` at 100,000 Conversations; record the results in Comments. Keep the fix only if all five quality checks pass; otherwise adjust or revert it
