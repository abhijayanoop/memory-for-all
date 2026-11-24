# 06: "Not found" floor suggestion

**What to build:** Each `quality run` suggests a "not found" floor from the Test Set's re-ranker scores, so the floor is set from the user's data instead of guessed, and shows the trade-off. The user copies the value into spec 3's `NOT_FOUND_FLOOR` constant and runs again. See the spec: `.scratch/quality/spec.md` (User Stories 49–51; Floor suggestion).

**Blocked by:** 03 (Quality run end to end)

**Status:** ready-for-agent

- [ ] Per answerable/partly question: best re-ranker score among its right hits in the raw top 8 (none if no right hit); per unanswerable question: the top hit's score
- [ ] Suggested floor = the value that misclassifies the fewest questions (unanswerable at or above it, answerable/partly with best right hit below it or none); ties take the lower value
- [ ] `quality run` prints the suggestion with both counts (unanswerable let through, answerable wrongly emptied) and the review file records it
- [ ] Tests with a fake re-ranker giving controlled scores: separable groups give a value between them with zero errors; overlapping groups minimise errors and take the lower value on a tie; counts are right
