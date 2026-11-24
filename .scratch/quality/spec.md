# Spec 4: Quality

Status: ready-for-agent

Source decisions: `docs/spec-plan.md` (spec 4), `.scratch/memory-for-all-v1/issues/05-match-score-and-checks.md` (Match Score, floor, Test Set, five checks), `.scratch/memory-for-all-v1/issues/04-context-pack-format.md`, spec 3 (`.scratch/context-pack/spec.md`, which this spec builds on), spec 1 (`.scratch/knowledge-base-and-chunking/spec.md`, untuned chunk constants). Vocabulary: `GLOSSARY.md` (Match Score, Test Set, Hallucination, Abstention, Current Decision).

## Problem Statement

Spec 3 gives me a Context Pack, but I have no way to know whether it is any good, and nothing stops a later change from quietly making it worse. The numbers that decide what I see were guessed: the "not found" floor is an untuned constant, and so are spec 1's merge cutoff (0.72) and Chunk size cap (1,800). In the prototype the Match Score for the same Request swung between 25% and 75%, with needs wrongly marked missing, and a small model swapped which product was the guitar and which was the amp.

I also don't get a single figure telling me how much of my Request my chats answered. Spec 3 lists the needs, but I want "60%: missing the hosting choice".

Quality can fail in two opposite directions. A pack can say something my chats don't (Hallucination), or it can say "nothing found" or "missing" when the answer is there (wrong Abstention). I need both measured on my own real Conversations, after every change, with clear pass marks, so that spec 7's speed work and any future change can prove it did not cost quality.

## Solution

1. **Match Score:** every pack result carries a Match Score: needs covered ÷ total needs, with the uncovered needs named, for example "60%: missing the hosting choice". The command line prints it after the pack, never inside it. (The extension preview in spec 6 is where it is shown to the user day to day.)
2. **Test Set:** a helper command, `quality add`, lets me write a question from my real chats, label it *answerable*, *partly answerable* or *unanswerable*, mark whether I changed my mind on it, and mark the right Chunks by picking search hits and giving a short exact phrase from each. The Test Set is saved in my Knowledge Base folder, outside the repo, because it holds private content.
3. **Quality run:** `quality run` puts every Test Set question through search and the pack, computes the checks the program can judge on its own, suggests a "not found" floor from the scores, and writes a review file in the Knowledge Base folder with each pack and blanks for the marks only I can make.
4. **Score:** after I fill in the blanks, `quality score` gives pass or fail for each of the five quality checks and an overall result, with a non-zero exit when anything fails, so it can gate other work.
5. **Tuning:** the "not found" floor is set from the run's suggestion. The 0.72 merge cutoff and 1,800 cap are re-checked against the Finding check and changed only if Finding improves without failing other checks.

The five checks and their pass marks (from ticket 05):

| # | Check | Pass |
|---|---|---|
| 1 | **Finding:** for answerable and partly answerable questions, a marked right Chunk is in the top 8 | at least 90% of questions |
| 2 | **Hallucination:** the pack says nothing my chats don't (wrong fact, wrong link between facts, an assistant's suggestion shown as my decision) | 0 on every question |
| 3 | **Correct Abstention:** unanswerable questions give "Nothing found"; partly answerable ones name exactly the missing needs | 100% |
| 4 | **Wrong Abstention:** the answer is in my chats but the pack leaves it out or the Match Score marks it missing | at most 10% of needs |
| 5 | **Current Decision:** for changed-mind questions, the pack leads with the newest choice and names what it replaced | 100% |

## User Stories

### Match Score

1. As a user, I want a Match Score for every pack, so that I know at a glance how much of my Request my chats answered.
2. As a user, I want the Match Score computed as covered needs ÷ total needs, so that the figure means something concrete.
3. As a user, I want the uncovered needs named next to the percentage (for example "60%: missing the hosting choice"), so that I know exactly what to add or explain myself in the new chat.
4. As a user, I want a fully covered Request shown as "100%" with nothing listed missing, so that the good case is short.
5. As a user, I want a need counted as covered only when a quote the program verified covers it (spec 3's rule), so that the Match Score cannot be inflated by the model's say-so.
6. As a user, I want the needs split from my Request alone, before looking at what was found, so that the denominator does not shrink to fit the results.
7. As a user, I want the Match Score never written inside the pack, so that the new chat's model is not given a number about my search.
8. As a user, I want no Match Score when the answer is "Nothing found in your chats for this", so that I am not shown a meaningless 0%.
9. As a user, I want the command line to print the Match Score line on standard error after the pack, so that piping the pack still gives only the pack.
10. As a developer of spec 6, I want the Match Score (percentage and missing needs) returned on the pack result, so that the extension preview can show it without recomputing.

### Building the Test Set

11. As a user, I want to add a question to the Test Set with one helper command, so that building 20 questions is not a chore.
12. As a user, I want to write each question in my own words from my real chats, so that the Test Set reflects how I actually ask.
13. As a user, I want to label each question *answerable*, *partly answerable* or *unanswerable*, so that the checks know what result is right.
14. As a user, I want to flag questions where I changed my mind, so that the Current Decision check can use them.
15. As a user, I want the helper to show me the top search hits for my question (more than 8, so a right Chunk ranked low can still be marked), so that I can pick the right Chunks without opening files.
16. As a user, I want to mark a right Chunk by picking a hit and giving a short exact phrase from it, so that the mark is tied to what makes that Chunk right.
17. As a user, I want a right Chunk mark to keep working after the Knowledge Base is re-chunked or a chat grows, so that tuning the chunk rules doesn't make me redo the Test Set.
18. As a user, I want the helper to refuse a phrase that is not in the chosen hit, so that a typo never makes a mark that can't match.
19. As a user, I want to be able to mark a right Chunk the search did not find, by naming the Conversation and a phrase, so that a search miss can still be recorded as a miss.
20. As a user, for a changed-mind question, I want to give a phrase for my newest choice and a phrase for the choice it replaced, each checked against my chats, so that the Current Decision check can be judged by the program.
21. As a user, I want unanswerable questions to need no marks, so that adding them is quick.
22. As a user, I want the Test Set stored in my Knowledge Base folder, outside the repo, so that my private chats never end up committed.
23. As a user, I want the Test Set to be a plain readable file, so that I can fix a typo or remove a question by hand.
24. As a user, I want a malformed Test Set file reported with the question and field at fault, so that a hand edit can't silently break the checks.
25. As a user, I want to be told when my Test Set is short of the agreed minimums (20 questions, at least 4 unanswerable, at least 3 changed-mind), so that I know the result is not yet a real pass.
26. As a user, I want quality files in the Knowledge Base folder never read as Conversations by reindex, so that my Test Set and review files don't pollute search.

### Running the checks

27. As a user, I want one command that runs every Test Set question through search and the pack, so that measuring quality is one step.
28. As a user, I want the Finding check measured on search's top 8 before the floor is applied, so that Finding measures search, not the floor.
29. As a user, I want a hit to count as a right Chunk when it comes from the marked Conversation and contains the marked phrase (ignoring case and punctuation, as spec 3's quote check does), so that marks survive re-chunking.
30. As a user, I want the program to judge Correct Abstention for unanswerable questions itself ("Nothing found" or not), so that I only mark what needs a human.
31. As a user, I want the program to judge the Current Decision check itself, by checking that a subject's leading quote holds my newest-choice phrase and its replaced quotes hold my old-choice phrase, so that this check needs no hand marks.
32. As a user, I want a review file written for each run, showing each question, its label, its pack (or "Nothing found"), its Match Score and needs, and the program's own check results, so that I can read the packs in one place.
33. As a user, I want blanks in the review file only for what the program cannot judge (Hallucinations, needs wrongly missing, and whether a partly answerable pack named exactly the missing needs), so that hand marking is as short as possible.
34. As a user, I want each run's review file kept with a timestamp in its name, so that I can compare runs before and after a change.
35. As a user, I want the review file to record the settings the run used (search Mode, pack Mode and API, writing model, re-ranker, floor, merge cutoff, Chunk cap), so that runs are comparable.
36. As a user, I want a run to continue past a question whose pack fails (writing-model error) and record the failure, so that one bad answer doesn't waste the whole run.
37. As a user, I want a run to stop with the spec 3 fix-it message when the writing model can't be reached at all (first question fails to connect), so that I don't wait for 20 identical failures.
38. As a user, I want the run's automatic results printed when it finishes, so that I see Finding, unanswerable Abstention and Current Decision straight away.

### Scoring

39. As a user, I want `quality score` to read my hand marks from the latest review file (or one I name), so that scoring is one command after marking.
40. As a user, I want pass or fail for each of the five checks with the measured value next to the pass mark, so that I see how close each one is.
41. As a user, I want an overall pass only when all five pass on a Test Set that meets the minimums, so that "pass" means the agreed bar.
42. As a user, I want `quality score` to exit non-zero on any failure, so that spec 7 and later work can use it as a gate.
43. As a user, I want a blank hand mark treated as an error that names the question, not as zero, so that an unmarked Hallucination can never pass silently.
44. As a user, I want a writing-model failure on a question counted as a fail for that question's checks, so that failures can't improve a score.
45. As a user, I want Wrong Abstention counted over all needs in answerable and partly answerable questions, so that the 10% mark is a share of needs, as agreed.
46. As a user, I want an answerable or partly answerable question that got "Nothing found" counted as Wrong Abstention on every need I expected (I write how many in the review file), so that a wrongly empty answer weighs as much as it should.
47. As a user, I want the Hallucination check to rest on my hand marks on top of spec 3's quote check, so that wrong links between true quotes and suggestions shown as decisions, which the quote check cannot see, are still caught.
48. As a user, I want the failing questions listed under each failing check, so that I know where to look.

### Tuning

49. As a user, I want each run to suggest a "not found" floor from the re-ranker scores of the Test Set, so that the floor is set from my data, not guessed.
50. As a user, I want the suggestion to show how many unanswerable questions it would still let through and how many answerable questions it would wrongly empty, so that I can see the trade-off.
51. As a user, I want the floor set in the code as a named constant from that suggestion, so that everyone running the program gets the tuned value and no private content is committed (it is one number).
52. As a user, I want the merge cutoff (0.72) and Chunk cap (1,800) re-checked with the Finding check after a full rebuild, and changed only if Finding improves without any other check failing, so that the chunk rules are tuned on real data.
53. As a developer of spec 7, I want the quality checks runnable the same way after any speed change, so that speed never costs Context Pack quality.

## Implementation Decisions

### Modules

1. **Context Pack writer (spec 3), extended, no new seam:** `PackResult` gains `match_score`: a whole percentage (covered ÷ total, rounded to the nearest whole number) and the list of missing needs, or none when `nothing_found`. A short text form is part of the result: `"60%: missing the hosting choice"`, `"100%"`, several missing needs joined with commas. The pack text is unchanged and never holds the Match Score. The command line's `pack` prints the Match Score line to standard error after spec 3's needs listing.
2. **Quality module (new, the one new seam):**
   - `load_test_set(path) -> TestSet`: reads and validates the Test Set file; errors name the question and field. Reports (does not refuse) a shortfall against the minimums.
   - `run(kb, test_set, writer) -> Report`: for each question, `kb.search(question, k=8)` (raw, before the floor) and `pack(kb, question, writer)`; computes the automatic checks; collects re-ranker scores for the floor suggestion. Writes nothing itself.
   - `write_review(report, folder) -> path` and `read_review(path) -> Report with marks`: the review file round trip.
   - `score(report) -> Scores`: the five checks, each with measured value, pass mark, pass/fail and failing questions; an overall pass; errors for blank marks.
   - `suggest_floor(report) -> FloorSuggestion`: the suggested value and its trade-off counts.
3. **Command line:** a `quality` command with subcommands, Knowledge Base and writer built as `pack` builds them:
   - `quality add "<question>" --label answerable|partly|unanswerable [--changed-mind]`: interactive. Shows the top 20 hits numbered. For non-unanswerable questions, asks which hit numbers are right and a phrase for each, checking each phrase is in its hit; also accepts a Conversation reference plus phrase for a Chunk the search missed. For `--changed-mind`, asks for the newest-choice phrase and the replaced-choice phrase, each checked to exist in the Knowledge Base. Appends to the Test Set.
   - `quality run`: runs, writes the review file, prints the automatic results, the floor suggestion and any Test Set shortfall.
   - `quality score [<review file>]`: scores the latest (or named) review file; prints each check; exit 0 only on an overall pass.

### Storage

- A `quality/` folder in the Knowledge Base folder holds the Test Set file and a `runs/` folder of review files. The Knowledge Base's file scan skips `quality/`, so these are never parsed as Conversations (today's scan reads every `.md` in the folder).
- **Test Set file:** JSON, one object per question. Shape:

  ```json
  {"questions": [{"id": 3, "question": "which amp did I settle on?", "label": "answerable",
                  "changed_mind": true,
                  "right": [{"conversation": "claude:abc123", "phrase": "going with the Katana 50"}],
                  "current": "going with the Katana 50", "replaced": "the Boss Nextone"}]}
  ```

  `label` is `answerable`, `partly` or `unanswerable`. `right` is required (non-empty) unless unanswerable. `current` and `replaced` are required when `changed_mind` is true. `id`s are assigned by `quality add` and never reused.
- **Right Chunk rule:** a hit is right when its Chunk's Conversation (`platform:chat_id`) matches the mark and its normalised text contains the normalised phrase, using spec 3's quote normalisation (lower case, every run of non-word characters to one space). Chunk ids are not stored, because they are positions and shift on re-chunking.
- **Review file:** Markdown, one section per question, with the hand-mark lines in a fixed form the program reads back, for example:

  ```
  ## Q3: which amp did I settle on? (answerable, changed mind)
  ...pack or "Nothing found in your chats for this"...
  Match Score: 60%: missing the hosting choice
  Automatic: Finding pass · Current Decision pass
  Hallucinations: ____
  Needs wrongly missing: ____
  ```

  Partly answerable sections add `Missing needs named exactly (yes/no): ____`. A "Nothing found" on an answerable or partly answerable question adds `Needs you expected: ____`. Unanswerable sections have no hand marks. The header records the run's settings (story 35).

### Checks (how `score` computes them)

- **Finding:** answerable + partly questions with a right hit in the raw top 8 ÷ those questions. Pass ≥ 90%.
- **Hallucination:** sum of the hand-marked counts. Pass when every question is 0. A question whose pack failed counts as a fail.
- **Correct Abstention:** unanswerable questions with `nothing_found` (automatic) plus partly questions marked "yes" (hand) ÷ unanswerable + partly questions. Pass = 100%.
- **Wrong Abstention:** (sum of "needs wrongly missing" + "needs you expected" on wrongly empty answers) ÷ (all needs from answerable and partly packs + those expected counts). Pass ≤ 10%.
- **Current Decision (automatic):** a changed-mind question passes when some subject in `PackResult.decisions` has a leading quote containing `current` and a replaced quote containing `replaced` (normalised containment). Pass = 100%.
- **Overall:** all five pass and the Test Set meets the minimums. Otherwise fail, with the reason.

### Floor suggestion

- For each answerable or partly question, take the best re-ranker score among its right hits in the raw top 8 (none if no right hit). For each unanswerable question, take the top hit's score.
- The suggested floor is the value that misclassifies the fewest questions (unanswerable above it, or answerable/partly with their best right hit below it); ties pick the lower value, because wrong Abstention is the failure the prototype showed. Reported with both counts.
- The user copies it into spec 3's `NOT_FOUND_FLOOR` constant and runs again to confirm the checks. The floor is tied to the re-ranker; changing the re-ranker means tuning again.

### What this spec does not change

- Search, the index format, the pack's text and rendering, the model calls (still two per pack) and the settings file are unchanged. The only Knowledge Base change is skipping `quality/` in the file scan.
- No model call is added for quality: Match Score and checks use what `pack` already returns.

## Testing Decisions

- A good test drives the seam with a Test Set and a fixture Knowledge Base and checks what the user sees: check values, pass/fail, failing questions, the floor suggestion, Match Score text, review file round trip, exit codes. It does not check review-file layout details beyond what `read_review` needs, or internal helpers.
- **`pack` seam (spec 3's tests, extended):** with the scripted fake writer, 3 needs of which 2 are covered by verified quotes gives 67% and names the missing need; all covered gives "100%"; a need the fake claims covered by an unverified quote counts as missing; `nothing_found` has no Match Score; the pack text never contains the Match Score.
- **Quality seam (`run`, `score`, `suggest_floor`, review round trip):** a temporary Knowledge Base from fixture Conversations, spec 2's fake embedder and a fake re-ranker with controllable scores, and spec 3's scripted fake writer. Cases:
  - Finding: a right Chunk in the top 8 passes; one ranked 9th fails; a right Chunk still counts after the fixture is re-chunked with a different merge cutoff (phrase marks survive);
  - a hit from another Conversation containing the phrase is not right;
  - Correct Abstention: unanswerable with "Nothing found" passes, with a pack fails; partly marked "no" fails;
  - Wrong Abstention: marks summing to just over 10% of needs fail, at 10% pass; an answerable "Nothing found" adds its expected needs;
  - Hallucination: any non-zero mark fails the check and names the question;
  - Current Decision: passes when the newer quote leads with the older replaced; fails when the phrases are absent or reversed;
  - a blank hand mark is an error naming the question, never a zero;
  - a writing-model failure on one question is recorded, the run continues, and that question fails its checks;
  - Test Set below minimums: checks still computed, overall result is not a pass, the shortfall is named;
  - malformed Test Set (missing `right` on an answerable question, missing `current` on a changed-mind one, unknown label) is rejected with question and field;
  - floor suggestion: with separable scores it picks a value between the groups; with overlap it minimises errors and takes the lower value on a tie; counts are right;
  - write a review, fill marks, read it back: scores match.
- **Command line smoke tests** (config directory pointed at a temporary folder, fakes injected, as in specs 1 to 3): `quality add` with scripted standard input appends a valid question and refuses a phrase not in the chosen hit; `quality run` writes a review file under `quality/runs/`; `quality score` exits 0 on a fully passing marked run and non-zero on a failing or unmarked one; `pack` prints the Match Score on standard error only; reindex ignores files in `quality/`.
- No test uses the user's real Test Set, and no test calls OpenAI or Claude. No new slow tests: spec 3's slow test already covers the real local models.
- **Prior art:** spec 3's `pack` tests and scripted fake writer; `tests/test_search.py` and `tests/test_model_switch.py` (Knowledge Base with fakes); `tests/test_modes.py` (command-line smoke tests); `tests/conftest.py` (fake embedder and re-ranker).

## Out of Scope

- Showing the Match Score in the extension preview: spec 6 (this spec only returns it).
- Writing the user's 20 real questions and doing the hand marks: the user does this with the tools here; the tuned floor value lands once that is done.
- Automatic Hallucination detection beyond spec 3's quote check (no judge model).
- Repeating each question several times to measure Match Score swing; one run per question at temperature 0.
- Automatic sweeps over floor, merge cutoff or Chunk cap values; tuning is suggest, edit the constant, run again.
- Speed measurement: spec 7.
- Choosing the Current Decision when chats disagree subtly: later spec.
- Sharing or syncing the Test Set; it stays in the user's Knowledge Base folder.

## Further Notes

- Ticket 05 replaces the map's "four checks" with these five; the earlier "honest score" check is now Wrong Abstention.
- Before the fixes in spec 3, the guitar pack's Match Score swung between 25% and 75% across runs with needs wrongly marked missing. That is why Wrong Abstention is a check of its own. If it fails on the real Test Set, the first suspect is call 2's needs split, not the floor.
- The floor is untuned until the user's Test Set exists. Until then the spec 3 constant stays as is. The prototype's 0.5 was a guess.
- Spec 1's chunk evidence was thin (5 questions on 7 chats). Re-checking the 1,800 cap and 0.72 cutoff here needs a full rebuild per value tried, which is slow with real models; try few values.
- Spec 7 depends on `quality score` as its gate: every speed change must keep all five checks passing on the real Test Set.
- `GLOSSARY.md` already defines Match Score, Test Set, Hallucination and Abstention as used here; no new terms.
