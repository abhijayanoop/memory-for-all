# 02: Meaning search and rank fusion

**What to build:** Search also finds Chunks that mean the same as the Request even with different words. The Request is embedded, compared to every Chunk vector, and the meaning list is merged with the keyword list by reciprocal rank fusion. A Request with no shared words still returns meaning matches. See the spec: `.scratch/search-and-modes/spec.md` (Search pipeline: Meaning search, Fusion).

**Blocked by:** 01 (Keyword search end to end)

**Status:** ready-for-agent

- [ ] The Request is embedded with the Knowledge Base's embedder; cosine similarity (dot product of unit vectors) against all Chunk vectors gives the top 50
- [ ] Keyword top 50 and meaning top 50 are fused with score = sum of `1 / (60 + rank)`; a Chunk in only one list still counts
- [ ] The constants (50, 50, 60) are named and marked untuned (tuned in spec 4)
- [ ] Test: a Request with no shared words finds the Chunk whose fake vector matches
- [ ] Test: an exact-word Request finds its Chunk even when the fake vectors call it unrelated
- [ ] Test: a Chunk found by both lists outranks one found by only one
- [ ] Test: after a refresh that adds, changes or deletes a file, both sides see the change
