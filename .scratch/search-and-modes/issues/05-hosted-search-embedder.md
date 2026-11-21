# 05: Hosted search embedder

**What to build:** With the search Mode set to hosted, the program embeds Chunks with OpenAI `text-embedding-3-small` (1536 dimensions) using the key in `OPENAI_API_KEY`. The command line builds the Knowledge Base with the embedder that matches the saved search Mode, so the next `reindex` re-embeds everything with it through the existing full rebuild and safe swap. Calls are batched and retried on rate limits; a bad key gives a clear error and leaves the old index live. See the spec: `.scratch/search-and-modes/spec.md` (Modules: Embedder interface, Embedder lookup; Mode switching; Privacy).

**Blocked by:** 04 (Mode settings)

**Status:** ready-for-agent

- [ ] Hosted embedder implements the existing embedder interface (`name`, `dimension`, `embed`) and returns unit-length vectors
- [ ] Texts are sent in batches; rate-limit responses are retried with a wait; other errors raise a clear message without printing the key
- [ ] A fixed lookup table maps embedder name to constructor for the two real embedders
- [ ] The command line picks the target embedder from the search Mode; tests can still inject fakes
- [ ] A failed hosted rebuild leaves the old index live and searchable
- [ ] Tests use a fake HTTP layer (batching, retry, bad key); no test calls OpenAI
