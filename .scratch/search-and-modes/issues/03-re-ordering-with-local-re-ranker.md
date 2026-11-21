# 03: Re-ordering with the local re-ranker

**What to build:** The best answer comes first: the top 20 fused Chunks are scored by a local re-ranking model that reads the Request and each Chunk together, and the top `k` by that score are returned. Each hit and each printed result carries its re-ranking score, for spec 4's Match Score to use later. The model is downloaded once and loaded on first use. See the spec: `.scratch/search-and-modes/spec.md` (Modules: Re-ranker interface; Search pipeline: Re-ordering).

**Blocked by:** 02 (Meaning search and rank fusion)

**Status:** resolved

- [ ] Re-ranker interface: `name`, `rerank(request, texts) -> scores` (higher is better, raw scores)
- [ ] Real re-ranker wraps fastembed's cross-encoder `Xenova/ms-marco-MiniLM-L-6-v2`, loaded lazily so `status` stays instant
- [ ] The Knowledge Base takes a re-ranker in its constructor (real one by default); tests inject a deterministic fake
- [ ] Top 20 fused Chunks (named, untuned constant) are re-scored; hits carry the raw score and final rank
- [ ] `search` output shows the score
- [ ] Test: the fake re-ranker's order decides the final order, even when it differs from the fused order, and only `k` come back
- [ ] Slow, skippable test: the real re-ranker scores an obviously relevant text above an unrelated one, and an end-to-end search with the real local models works on a small fixture
