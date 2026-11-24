# match-score-and-checks

Type: grilling
Status: resolved
Blocked by: 03, 04

## Question

Define exactly how the Match Score and the four quality checks are measured, and how the Test Set is built from real chats.

## Answer

Settled by grilling (2026-11-22 to 2026-11-24). Builds on ticket 04.

**Match Score:**
- The Request is split into 1 to 4 needs, from the Request alone.
- A need is covered only if a quote the program has verified covers it.
- Match Score = covered ÷ total, with the uncovered needs named, for example "60%: missing the hosting choice".
- It's shown only in the extension preview.

**"Not found" floor:** a cutoff on search scores, applied to every source Chunk. If no Chunk passes it, the answer is "Nothing found in your chats for this" and no pack is written. The cutoff is set from the Test Set, not guessed. The prototype's 0.5 was untuned.

**Test Set:**
- 20 questions the user writes from their real chats. Right Chunks are marked with a small helper command.
- Each question is labelled *answerable*, *partly answerable* (some needs are not in the chats) or *unanswerable*.
- At least 4 unanswerable, and at least 3 where the user changed their mind.
- Stored in the Knowledge Base folder, outside the repo, because it holds private content.

**Five quality checks** (Hallucination and Abstention are separate classes; see GLOSSARY):
1. **Finding:** for answerable questions, a marked right Chunk is in the top 8. Pass: at least 90%.
2. **Hallucination:** the pack says nothing the chats don't. That covers wrong facts, wrong links between facts, and an assistant's suggestion shown as the user's decision. Marked by hand on the Test Set, on top of the program's quote check. Pass: 0 on every question.
3. **Correct Abstention:** unanswerable questions give "Nothing found", and partly answerable ones name exactly the missing needs. Pass: 100%.
4. **Wrong Abstention:** the answer is in the chats, but the pack leaves it out or the Match Score marks it missing. Pass: at most 10% of needs.
5. **Current Decision:** for changed-mind questions, the pack leads with the newest choice and names what it replaced. Pass: 100%.

These five replace the "four checks" in the map. The earlier "honest score" check is now check 4.

**Prototype evidence:** before the fixes, the guitar pack's Match Score swung between 25% and 75% across runs, with needs wrongly marked missing. That's why Wrong Abstention is measured as its own check.
