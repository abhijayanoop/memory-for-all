# 03: Bench: time the Context Pack

**What to build:** The bench also times a Context Pack at scale, split into search time and writing time, so the user can tell whether scale or the writing model is the slow part. When the local writing model can't be reached, pack timing is skipped with a note and the rest of the bench still runs. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Bench module": pack; stories 16, 32, 33).

**Blocked by:** 02 (Bench: run and report), spec 3 ticket 01 (`.scratch/context-pack/issues/01-pack-end-to-end-with-local-writer.md`)

**Status:** ready-for-agent

- [ ] `measure` times spec 3's `pack` over the bench Requests when a writer is given: median and worst, each split into search and writing time
- [ ] The pack budget (under 30 s) gets a verdict at 100,000 Conversations, `report only` at other sizes
- [ ] `bench run` builds the writer as the `pack` command does; when the local writing model is unreachable it skips pack timing with a note and does not fail
- [ ] Tests with spec 3's scripted fake writer and a scripted clock: pack times and split are reported; a 40 s pack at the threshold gives `fail`; no writer → skipped with a note
