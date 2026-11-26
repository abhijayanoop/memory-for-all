# 04: Baseline measurement

**What to build:** Before any speed fix, the user measures today's code on generated Knowledge Bases at 1,000, 10,000 and 100,000 Conversations made from their real one, so every later fix is compared against a real baseline. This also answers how many Chunks a real Conversation makes, which decides the vector memory. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Process" 1; Further Notes).

**Blocked by:** 03 (Bench: time the Context Pack)

**Status:** ready-for-human

- [ ] Generate 1,000, 10,000 and 100,000 Conversations from the real Knowledge Base into a folder outside the repo (growing one Knowledge Base, same seed)
- [ ] Run `reindex`, then `bench run`, at each size on today's code (no spec 7 fixes), in fully local Mode on the laptop
- [ ] The local writer is reachable and Context Pack timing is recorded at each size; a skipped pack measurement does not complete the baseline
- [ ] Results kept in the results file outside the repo; nothing private committed
- [ ] Note (in this ticket's Comments): Chunks per Conversation, vector memory size, and which budgets fail at 100,000 and by how much, so the fix tickets can be checked against it
