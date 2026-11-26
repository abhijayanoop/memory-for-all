# 11: Measure after the fixes and run the quality gate

**What to build:** With the known fixes in, the user measures again at 100,000 and about 300,000 Conversations and runs the spec 4 quality checks on their real Test Set, to confirm the budgets hold and Context Pack quality did not drop. Any budget still missed becomes a new ticket for the matching conditional fix. See the spec: `.scratch/scale-and-speed/spec.md` (Solution 3; Implementation Decisions, "Process" 2 and 3, "Conditional fixes"; stories 29, 46 to 49).

**Blocked by:** 03, 05, 06, 07, 08, 09, 10, spec 4 tickets 04 (`.scratch/quality/issues/04-hand-marks-and-full-scoring.md`) and 05 (`.scratch/quality/issues/05-current-decision-check.md`)

**Status:** ready-for-human

- [ ] `bench run` at 100,000 and about 300,000 generated Conversations in fully local Mode on the laptop; results kept in the results file outside the repo
- [ ] At 100,000: the local writer is reachable, pack timing is recorded, and every budget's verdict noted in Comments (warm search under 2 s, Context Pack under 30 s, incremental reindex under 1 min); at about 300,000: the bench completes with no crash or running out of memory
- [ ] `quality score` on the real Test Set exits 0 (all five checks pass)
- [ ] For each budget still missed, or memory running out at about 300,000, a new ticket is filed in this folder for the matching conditional fix (approximate nearest-neighbour index, cheaper re-ranking, batched embedding, smaller stored vectors), each carrying the spec's keep rule: Finding check passes, and recall at least 95% where results change
- [ ] If nothing is missed, note that no conditional fix is needed and spec 7 is done
