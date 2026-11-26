# 03: Quality run end to end, with the automatic checks

**What to build:** `quality run` puts every Test Set question through search and the pack, writes a timestamped review file in `quality/runs/` showing each question, its label, its pack (or "Nothing found in your chats for this") and the run's settings, and prints the checks the program can judge alone. `quality score [<review file>]` scores the latest (or named) review file and exits non-zero on any failure. This ticket delivers Finding and Correct Abstention for unanswerable questions; later tickets add the rest. See the spec: `.scratch/quality/spec.md` (Solution 3–4; Modules 2–3; Checks: Finding, Correct Abstention).

**Blocked by:** 02 (Test Set and `quality add`), spec 3 ticket 01 (`.scratch/context-pack/issues/01-pack-end-to-end-with-local-writer.md`)

**Status:** ready-for-agent

- [ ] `run(kb, test_set, writer) -> Report` calls `search(question, k=8)` (raw, before the floor) and `pack` per question
- [ ] Finding: a hit is right when it comes from the marked Conversation and its normalised text contains the normalised phrase; answerable + partly questions with a right hit in the top 8 ÷ those questions; pass ≥ 90%
- [ ] Correct Abstention (unanswerable half): `nothing_found` passes, a pack fails
- [ ] Review file written per run with a timestamped name; header records search Mode, pack Mode and API, writing model, re-ranker, floor, merge cutoff, Chunk cap; `write_review` / `read_review` round trip
- [ ] A writing-model failure on one question is recorded and the run continues; that question fails its checks. If the first question cannot reach the writing model, the run stops with spec 3's fix-it message
- [ ] `quality run` prints the automatic results; `quality score` prints each check with measured value and pass mark, lists failing questions, exits 0 only when all pass
- [ ] Tests at the quality seam with fakes: right Chunk in top 8 passes, 9th fails; a phrase match from another Conversation is not right; a mark still matches after re-chunking with a different merge cutoff; unanswerable with and without "Nothing found"; one failing question doesn't stop the run; CLI smoke test writes a review file and checks `quality score` exit codes
