# chunk-rules

Type: prototype
Status: resolved
Blocked by: -

## Question

Try the Chunk-cutting rules (question kept with answer, same-subject grouping, labels) on a few real chats and decide the rules and sizes.

## Progress (unresolved)

Tested on 7 real chats (6 ChatGPT, 1 Claude; local only, `prototype/data-real/`). Finding 1: with no size cap the old rules made 24 Chunks up to 90,000 characters; the embedding model reads only about 2,000 characters (512 tokens), so most of each Chunk was invisible to search. Finding 2: capping at 1,800 characters and splitting long answers at paragraph then sentence ends (each piece keeps its question as a heading) gives 230 Chunks, median 1,737 characters, none over the cap, 6 under 300. Not yet tested: whether retrieval finds the right Chunk on real questions, and which cap works best (e.g. 800 vs 1,800).

## Answer

Tested on 7 real chats (6 ChatGPT, 1 Claude, local only) with the user's 5 test questions (4 answerable, 1 not in any chat). Prototype: `prototype/chunkcompare.py`, `prototype/chunkcompare2.py`.

Rules to specify:
- **Size cap 1,800 characters** (about 450 tokens; the default search model reads at most 512 tokens). An 800-character cap found the same answers on these questions and made 614 Chunks instead of 230, so 1,800 wins on cost.
- **Unit:** a question with its answer. Long answers split at paragraph breaks, then sentence ends, with a hard cut only when no break exists (code, tables). Every piece keeps its question (first 300 characters) as a heading.
- **Merging:** small neighbouring units on the same subject (similarity above 0.72) are merged up to the cap. The 0.72 cutoff was not tuned.
- **Title prefix:** every Chunk starts with `Chat: <title>`. Without it the Career3 question found the right chat but not the Chunk with the answer (the name appears in about 100 of 230 Chunks of that 114-message chat); with it, all four answerable questions found their answer at rank 1.
- **Not found:** the unanswerable question scored 0%, well apart from the 94 to 100% of the answerable ones.

Caveats: only 5 questions, one unanswerable; "answer found" was judged by a keyword in the top 3 Chunks; the hard cut loses meaning in code and tables; pasted files and image-only chats are untested; Match Score cutoff calibration needs a bigger Test Set (ticket 05).
