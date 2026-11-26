# 07: Incremental reindex skips unchanged files

**What to build:** The refresh after a Sync stops reading and fingerprinting every Conversation file. A file whose size and modification time haven't changed is skipped without being read; a touched file is fingerprinted and re-chunked only if its content really changed. The user's existing index is upgraded in place, with no rebuild or re-embed. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Known fixes": incremental reindex skips unchanged files; stories 34 to 37).

**Blocked by:** 04 (Baseline measurement), spec 4 tickets 04 (`.scratch/quality/issues/04-hand-marks-and-full-scoring.md`) and 05 (`.scratch/quality/issues/05-current-decision-check.md`)

**Status:** ready-for-agent

- [ ] The index's file table gains a size and a modification time per file
- [ ] Matching size and time → the file is not read; either differs → fingerprinted as today, re-chunked only if the fingerprint changed, and size and time updated either way
- [ ] An existing index gets the new columns added in place, empty ("fingerprint once"); no rules version change, so nothing is re-embedded
- [ ] Existing tests pass unchanged
- [ ] New tests with a counting embedder: a second refresh with no changes makes zero embed calls; a touched file (new time, same content) is not re-embedded; changed content with the same size is re-chunked; an index from before this change is upgraded with zero embed calls
- [ ] `bench run` incremental reindex time at 100,000 recorded in Comments, compared with the baseline

- [ ] After this fix, run the existing test suite and have the user run `quality score` on a fresh run of the real Test Set and `bench run` at 100,000 Conversations; record the results in Comments. Keep the fix only if all five quality checks pass; otherwise adjust or revert it
