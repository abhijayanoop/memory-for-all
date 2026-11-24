# 08: Polite pace and interrupted runs

**What to build:** Sync asks the Platform for one thing at a time, at least half a second apart, and slows down rather than breaking when told "too many requests". If it still can't continue, it stops and keeps what it saved, and the next run picks up without gaps or refetching. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Sync run": Pace, Interrupted runs; stories 15, 17 to 19).

**Blocked by:** 05 (Extension skeleton and a first Claude Sync, end to end)

**Status:** ready-for-agent

- [ ] Requests to the Platform are sequential, with at least 500 ms between them
- [ ] HTTP 429 waits for `Retry-After` (30 s if absent) and retries, up to 3 times per request; then the run calls `finish` with `interrupted`
- [ ] The 500 ms gap, 30 s default and 3 retries are constants in one place
- [ ] An interrupted run does not move the watermark; the next run re-lists down to the old watermark and the needs step skips everything already saved
- [ ] Vitest with the fake clock: the gap is honoured; 429 with and without `Retry-After`; interrupted after 3 retries with earlier saves kept; the next run resumes with no gap and no refetch (fetch call counts)
