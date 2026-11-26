# 08: Quick lookup on save, and a cheap `status`

**What to build:** Saving a Conversation finds its old file without searching the whole folder, so a first Sync of thousands of chats doesn't slow down as it goes. `memoryforall status` answers in a few seconds at any size, by counting from file names and the index instead of reading every Conversation and Chunk. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Known fixes": quick lookup on save, `status` counts cheaply; stories 38, 39).

**Blocked by:** 04 (Baseline measurement), spec 4 tickets 04 (`.scratch/quality/issues/04-hand-marks-and-full-scoring.md`) and 05 (`.scratch/quality/issues/05-current-decision-check.md`)

**Status:** ready-for-agent

- [ ] The Knowledge Base object keeps a map from (Platform, chat id) to file, built on first use from one scan of file names, confirmed by parsing only the candidate, and kept current by `save`, rename and removal
- [ ] `status` counts Conversations per Platform from file names in one scan, and Chunks with a count query
- [ ] Existing tests pass unchanged (save, rename, notes kept, mark gone and present)
- [ ] New tests: saving into a Knowledge Base with many fixture files finds and replaces the existing file, including after a title rename; an id that is a suffix of another id is not confused; `status` counts match the files
- [ ] `bench generate` save rate and `bench run` `status` time recorded in Comments, compared with the baseline

- [ ] After this fix, run the existing test suite and have the user run `quality score` on a fresh run of the real Test Set and `bench run` at 100,000 Conversations; record the results in Comments. Keep the fix only if all five quality checks pass; otherwise adjust or revert it
