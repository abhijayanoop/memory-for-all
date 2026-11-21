# 06: Full rebuild and safe swap

**What to build:** The index is truly disposable (ADR 0001). If it is missing or unreadable, or was built with a different embedder or chunk rules, `reindex` rebuilds everything from the files. A rebuild never leaves the user without a working index: the old one stays live until the new one is complete. See the spec (Index: full rebuild).

**Blocked by:** 05

**Status:** resolved

- [ ] A full rebuild happens when the index is missing or unreadable, or when its stored embedder name, dimension or rules version differs from the current ones
- [ ] A rebuild writes a new index file beside the old one and swaps it in only when complete; a simulated failure mid-rebuild leaves the old index usable
- [ ] Deleting the `.index` folder and running `reindex` gives the same Chunks (IDs, text, labels) as before
- [ ] Tests cover each trigger and the interrupted rebuild

## Answer

Implemented on branch `integration/knowledge-base-and-chunking`.
