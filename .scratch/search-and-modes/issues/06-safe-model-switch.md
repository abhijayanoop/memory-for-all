# 06: Safe search-model switch

**What to build:** Switching the search model never breaks search. Until the next reindex swaps in the new index, search keeps using the old one and embeds the Request with the model the live index was built with, and says a switch is pending. `status` shows the live index's model and "re-embed pending" when it differs from the target. Switching back before reindex cancels the pending re-embed. If the old model can no longer be used (unknown name, missing key), search returns keyword-only results (re-ordered as usual if ticket 03 has landed) with a warning. Spec 6's long-running program will run the same reindex in the background; nothing here starts a separate process. See the spec: `.scratch/search-and-modes/spec.md` (Mode switching ("background" re-embed)).

**Blocked by:** 02 (Meaning search and rank fusion), 04 (Mode settings)

**Status:** resolved

- [ ] The Knowledge Base is constructed with the target embedder and an embedder lookup by name; tests pass a table of fakes
- [ ] A read action exposes the live index's embedder name
- [ ] Search embeds the Request with the embedder named in the live index's metadata
- [ ] `search` prints a notice when a re-embed is pending; `status` shows the live model and the pending state
- [ ] Test: index built with fake A, Knowledge Base targeting fake B: search works and uses A; after refresh it uses B
- [ ] Test: a refresh that fails part-way (a fake embedder that raises) leaves search working on A
- [ ] Test: with A missing from the lookup, search returns keyword-only results and warns
- [ ] Test: switching back to A before refresh means nothing is pending
