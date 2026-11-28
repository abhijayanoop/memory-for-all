# 04: Hand marks and full scoring

**What to build:** The review file gains blanks for what only the user can judge, and `quality score` scores all of it. Each pack section shows the Match Score and needs, and has `Hallucinations: ____` and `Needs wrongly missing: ____`; partly answerable sections add `Missing needs named exactly (yes/no): ____`; a "Nothing found" on an answerable or partly answerable question adds `Needs you expected: ____`. `quality score` computes Hallucination, Wrong Abstention and the partly answerable half of Correct Abstention, and gives an overall pass only when all five checks pass on a Test Set meeting the minimums. See the spec: `.scratch/quality/spec.md` (User Stories 32–48; Review file; Checks).

**Blocked by:** 01 (Match Score on the pack result), 03 (Quality run end to end)

**Status:** resolved

- [ ] Review file shows Match Score and needs per pack, and the hand-mark lines in the fixed form; unanswerable sections have none
- [ ] Hallucination: sum of marks; pass only when every question is 0; failing questions named
- [ ] Wrong Abstention: (needs wrongly missing + needs you expected on wrongly empty answers) ÷ (all needs from answerable and partly packs + those expected counts); pass ≤ 10%
- [ ] Correct Abstention includes partly answerable questions marked "yes"; pass = 100%
- [ ] A blank hand mark is an error naming the question, never a zero
- [ ] Overall pass requires all five checks passing and the Test Set minimums met; otherwise fail with the reason (shortfall named)
- [ ] Tests: write a review, fill marks, read back, scores match; Wrong Abstention just over 10% fails and at 10% passes; answerable "Nothing found" adds its expected needs; non-zero Hallucination fails and names the question; partly marked "no" fails; blank mark errors; below minimums is not an overall pass; `quality score` exits non-zero on a failing or unmarked run
