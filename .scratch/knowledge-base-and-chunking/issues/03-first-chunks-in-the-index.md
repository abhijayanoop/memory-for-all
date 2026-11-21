# 03: First Chunks in the index

**What to build:** `uv run memoryforall reindex` reads every Conversation file, cuts it into basic Chunks, embeds them, and stores them in a SQLite index in the hidden `.index` folder inside the Knowledge Base. `status` shows the Chunk count and when the index was last refreshed. This ticket brings in the embedder interface: the real bge-small model, and a deterministic fake for tests. See the spec (Modules; Chunk rules: unit, prefix, cap, record; Index).

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] The embedder interface has `name`, `dimension` and `embed(texts)`, returning unit-length vectors; the real version wraps fastembed `BAAI/bge-small-en-v1.5`; a fake test embedder returns deterministic vectors
- [ ] The Chunker is a pure function: Conversation (plus notes) and embedder in, Chunks out
- [ ] Unit = one user message plus every assistant message up to the next user message; assistant messages before the first user message are their own unit, and so is an unanswered question; unit text is `User: ...` then `Assistant: ...`
- [ ] Every Chunk starts with `Chat: <title>`; no Chunk's full text exceeds 1,800 characters (a simple cut is acceptable here; ticket 04 refines the splitting)
- [ ] Each Chunk has a stable ID `<platform>:<chat_id>:<n>`, kind `exchange`, Platform, chat ID, title, date (the question's time, else the Conversation's `updated`), position, text and vector; the vector is embedded from the full final text
- [ ] The index stores `meta` (embedder name, dimension, rules version, last refreshed), `files` (relative path, fingerprint, chat ID) and `chunks`; the Knowledge Base exposes `refresh_index()` and `chunks()`
- [ ] `reindex` builds the index from scratch, and `status` shows Chunk count and last refresh
- [ ] One slow test, marked to be skippable, runs the real model on a small fixture: vectors are 384-dimensional and unit-length, and chunking runs end to end
- [ ] One command-line smoke test runs `import`, `reindex` and `status` on a fixture into a temporary Knowledge Base and checks exit codes and counts
