# 04: Full chunk rules

**What to build:** The Chunker follows all the rules tested in the prototype (ticket 03 of the v1 map) plus the line-break improvement. Long answers split cleanly, and each piece keeps its question. Small same-subject neighbours are merged. The user's notes become searchable Chunks. See the spec (Chunk rules), and `prototype/pipeline.py` for the behaviour this replaces.

**Blocked by:** 03

**Status:** resolved

- [ ] A unit over the cap is split: the answer breaks at blank lines first, then single line breaks, then sentence ends, packed greedily; a hard cut happens only when one segment alone exceeds the room left
- [ ] Every piece is `Chat: <title>`, then `User: <first 300 characters of the question>`, then `Assistant: <piece>`, and is within 1,800 characters including the prefix
- [ ] A question that alone exceeds the room is itself split the same way, then the answer pieces follow with the 300-character heading
- [ ] Neighbouring units in the same Conversation are merged when the combined text stays within the cap and cosine similarity is above 0.72 (a named, untuned constant); split pieces of one unit are never re-merged; Chunks never span Conversations
- [ ] Non-empty `## My notes` text becomes Chunks of kind `notes` with prefix `Chat: <title>` and heading `My notes:`, split by the same size rules, never merged with exchanges
- [ ] The rules version constant is bumped
- [ ] Pure Chunker tests with the fake embedder cover each rule above, including forcing "same subject" and "different subject"

## Answer

Implemented on branch `integration/knowledge-base-and-chunking`.
