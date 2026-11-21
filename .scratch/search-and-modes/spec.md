# Spec 2: Search and Modes

Status: resolved

Source decisions: `docs/spec-plan.md` (spec 2), `.scratch/memory-for-all-v1/issues/08-local-models.md` and `research/08-local-models.md`, `docs/adr/0001-markdown-source-of-truth.md`, spec 1 (`.scratch/knowledge-base-and-chunking/spec.md`). Vocabulary: `GLOSSARY.md`.

## Problem Statement

My Conversations are now saved as files and cut into Chunks with meaning-vectors (spec 1), but I still cannot find anything in them. When I want to carry past context into a new chat, I need to type a Request in plain words and get back the few Chunks that actually answer it. Keyword search alone misses answers phrased differently from my Request; meaning search alone misses exact names, numbers and code words. Both give a long, rough list where the best answer is often not first.

I also want to choose where the AI models run. By default nothing should leave my computer, but I may prefer hosted models (with my own OpenAI or Claude key) for better or faster results. Changing the search model means every Chunk has to be re-embedded, and that must never leave me without a working search while it happens.

## Solution

The Knowledge Base gains a search action. For a Request it runs a keyword search and a meaning search over the Chunks in the index, merges the two ranked lists with reciprocal rank fusion, re-orders the top few with a local re-ranking model, and returns the best few Chunks with their labels and scores. I use it from the command line with `search "<request>"`.

Two Mode settings say where models run, each `local` (default) or `hosted`: one for search (embedding) and one for pack-writing (the summary model spec 3 will use). Hosted search uses OpenAI embeddings with my OpenAI key. Hosted pack-writing uses OpenAI or Claude with my key. Keys come from environment variables and are never written to disk by the program.

When I switch the search Mode, the choice is recorded at once. The next reindex builds a new index with the new model beside the old one. Until it is swapped in, search keeps using the old index, with the old model embedding my Request, so search never breaks mid-switch.

## User Stories

### Searching

1. As a user, I want to type a Request in plain words and get back the Chunks that best answer it, so that I can find past context without remembering where it was.
2. As a user, I want search to find Chunks that share exact words with my Request (names, numbers, code words, error messages), so that precise lookups work.
3. As a user, I want search to find Chunks that mean the same as my Request even with different words, so that I don't have to guess how I phrased it back then.
4. As a user, I want the keyword and meaning results combined into one list, so that a Chunk strong on either side can appear.
5. As a user, I want the top of the combined list re-ordered by a model that reads my Request and each Chunk together, so that the best answer comes first.
6. As a user, I want a small number of results by default (5), so that I see only the most useful Chunks.
7. As a user, I want to ask for more or fewer results, so that I can dig deeper when the first few are not enough.
8. As a user, I want each result to show its chat title, Platform, date, Chunk ID and the start of its text, so that I can tell where it came from at a glance.
9. As a user, I want each result to carry its re-ranking score, so that later features (Match Score, "not found" floor) can judge how good a match is.
10. As a user, I want my own notes (from `## My notes`) to be searchable, and marked as notes in results, so that what I wrote myself is findable and recognisable.
11. As a user, I want search to work on Requests with quotes, punctuation, symbols or words that look like search operators, so that no Request causes an error.
12. As a user, I want an empty or whitespace-only Request rejected with a clear message, so that I know I must type something.
13. As a user, I want a clear message when the index is empty or missing, telling me to run reindex, so that I know why nothing came back.
14. As a user, I want a Request with no matching words still to return meaning matches, so that search is not useless when my words differ.
15. As a user, I want search results to come only from the index as last refreshed, with a hint to reindex if files changed, so that search stays fast and predictable.
16. As a user, I want search to run entirely on my computer in local Mode, so that my Request and my chats never leave it.
17. As a user, I want the re-ranking model downloaded once and reused, so that later searches work offline.
18. As a user, I want a search over a few thousand Conversations to return in a few seconds on my laptop, so that it feels usable.
19. As a developer of specs 3 and 6, I want search to be a single action on the Knowledge Base that returns structured hits, so that the Context Pack and the extension can call it directly.

### Choosing Modes

20. As a user, I want two separate Mode settings, one for search and one for pack-writing, so that I can keep search local but write packs with a hosted model, or the other way round.
21. As a user, I want both Modes to default to fully local, so that nothing leaves my computer unless I choose it.
22. As a user, I want to see my current Modes with one command, so that I know where my models run.
23. As a user, I want to set the search Mode to hosted, using my OpenAI key, so that I can use OpenAI embeddings.
24. As a user, I want a clear message that hosted search needs an OpenAI key (Claude offers no embeddings), so that I am not confused when a Claude key alone is not enough.
25. As a user, I want to set the pack-writing Mode to hosted with either OpenAI or Claude, so that I can use the key I already have.
26. As a user, I want my API keys read from environment variables and never saved by the program, so that keys never end up in my Knowledge Base, settings file or backups.
27. As a user, I want status to show whether each needed key is present without ever printing it, so that I can check setup safely.
28. As a user, I want to be told, when I switch search to hosted, that my Chunks and Requests will be sent to OpenAI, so that I make that choice knowingly.
29. As a user, I want a Mode change refused with a clear reason when its key is missing, so that I don't end up with a setting that cannot work.
30. As a user, I want the re-ranker to stay local in both Modes, so that re-ordering always works without a key (neither OpenAI nor Claude offers one).
31. As a user, I want my Mode choices kept in the same settings file as my Knowledge Base folder, so that all my settings live in one place.
32. As a user, I want a corrupt or unknown Mode value in the settings file reported clearly, so that I can fix it.

### Switching the search model

33. As a user, I want switching the search Mode to only record my choice, so that the command returns at once.
34. As a user, I want the next reindex to rebuild every Chunk's vector with the new model, so that old and new vectors are never mixed.
35. As a user, I want search to keep working on the old index while the new one is being built, so that I am never left without search.
36. As a user, I want my Request embedded with the same model as the index being searched, so that results stay correct during a switch.
37. As a user, I want status to show that a re-embed is pending and which model the live index uses, so that I know a switch is not finished.
38. As a user, I want search to tell me when it is using the old model because a switch is pending, so that I am not surprised by results.
39. As a user, I want an interrupted or failed rebuild (for example a network error with hosted embeddings) to leave the old index live, so that a failed switch costs me nothing.
40. As a user, I want switching back before the rebuild runs to cancel the pending re-embed, so that a mistaken switch is free.
41. As a user, I want search to fall back to keyword search only, with a warning, if the old index's model cannot be used any more (for example its key was removed), so that search still returns something.
42. As a user, I want hosted embedding calls to be sent in batches and retried on rate limits, so that re-embedding a large Knowledge Base finishes.
43. As a developer of spec 6, I want the switch to depend only on "the next reindex", so that the long-running local program can run that reindex itself in the background.

### Index upkeep

44. As a user, I want the keyword index stored in the same hidden index as the Chunks, so that it is disposable and rebuilt from my files like everything else.
45. As a user, I want an index built by spec 1 (without a keyword index) rebuilt once automatically on the next reindex, so that upgrading needs no manual step.
46. As a user, I want the keyword index kept in step with Chunks on every refresh (added, changed, removed files), so that keyword and meaning search always see the same Chunks.

## Implementation Decisions

### Modules

1. **Knowledge Base** (the one seam), extended:
   - `search(request, k=5) -> list of hits`. Each hit is the Chunk (labels and text, as spec 1 defines it) plus its re-ranking score and its final rank. Raises a clear error for an empty Request.
   - Constructed with the target embedder (from the search Mode), a re-ranker, and a way to get an embedder by name, used to embed the Request with the model the live index was built with when that differs from the target.
   - `refresh_index()` also maintains the keyword index. Its existing full-rebuild-and-swap logic is what performs a re-embed.
   - A small read action exposes the live index's embedder name, so status can report a pending re-embed.
2. **Re-ranker interface:** `name`, `rerank(request, texts) -> list of scores` (higher is better, raw model scores). The real version wraps fastembed's cross-encoder with `Xenova/ms-marco-MiniLM-L-6-v2`, loaded on first use. Tests use a deterministic fake.
3. **Embedder interface** (from spec 1, unchanged shape): `name`, `dimension`, `embed(texts)`. A second real implementation is added for hosted search: OpenAI `text-embedding-3-small` (1536 dimensions), batched, retrying on rate limits, reading the key from `OPENAI_API_KEY`. Per-model query prefixes, if a future model needs them, live inside its embedder. Neither v1 model needs one.
4. **Embedder lookup:** a fixed table from embedder name to constructor, covering the two real embedders. Tests pass their own table of fakes.
5. **Settings** (the existing settings file in the user's config directory) gains `search_mode` (`local` | `hosted`), `pack_mode` (`local` | `hosted`) and `pack_api` (`openai` | `claude`, used only when `pack_mode` is hosted). Missing values mean local. Unknown values are an error naming the file and the bad value.
6. **Command line**, extended:
   - `search "<request>" [-k N]` prints numbered hits: title, Platform, date, Chunk ID, kind if notes, score, and the first ~200 characters of text. It prints a notice when a re-embed is pending.
   - `mode` shows both Modes. `mode search local|hosted` and `mode pack local|hosted [--api openai|claude]` set them.
   - `status` adds both Modes, the live index's model, "re-embed pending" when it differs from the target, and each relevant key as `present` or `missing`.

### Search pipeline

- **Keyword search:** a SQLite FTS5 table in the same index file, holding each Chunk's ID and text, filled and cleaned in the same refresh transaction as the `chunks` table. The Request is broken into words, each word quoted as a literal term and joined with OR, so user text can never be read as FTS syntax. Ranked by FTS5's built-in BM25. Takes the top 50.
- **Meaning search:** embed the Request with the live index's model, cosine similarity (vectors are unit-length, so a dot product) against every Chunk vector, top 50. Brute force over all vectors is fine at personal scale.
- **Fusion:** reciprocal rank fusion, score = sum over both lists of `1 / (60 + rank)`. A Chunk in only one list still counts.
- **Re-ordering:** the top 20 fused Chunks are scored by the re-ranker against the Request, sorted by that score, and the top `k` are returned. The returned score is the raw re-ranker score. Turning it into a Match Score is spec 4.
- The four numbers (50, 50, 60, 20) are named constants, untuned. They will be tuned against the Test Set in spec 4.
- `exchange` and `notes` Chunks are searched together.
- Search never refreshes the index. If the index is missing or empty, it returns no hits and the command line says to run reindex.

### Index changes

- The index format gains the FTS5 table. The rules version from spec 1 is bumped so that an existing index rebuilds once, through the existing safe swap.
- `meta` already records the embedder name and dimension. Search reads them to choose the Request's embedder.

### Mode switching ("background" re-embed)

- `mode search hosted` checks `OPENAI_API_KEY` is set (refuses otherwise), prints that Chunks and Requests will be sent to OpenAI, and saves the setting. It does no embedding itself.
- The command line builds the Knowledge Base with the target embedder for the saved search Mode. On the next `reindex`, the existing check sees the embedder name in `meta` differs and does a full rebuild into a new file, swapping it in only when complete. A failure leaves the old index live.
- While the swap has not happened, `search` gets the embedder for the name in `meta` from the lookup and uses it for the Request. If that embedder cannot be built (unknown name, missing key), search uses keyword results only, re-ordered as usual, and warns.
- Switching back before reindex makes target and `meta` match again, so nothing is pending.
- Spec 6's long-running program will call the same reindex in the background. Nothing in this spec runs a separate process.

### Pack-writing Mode

- This spec only stores, validates and shows the pack-writing Mode and checks the key for the chosen API (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) when set to hosted. The local default is Qwen3-4B-Instruct-2507 through Ollama (from ticket 08). Calling any writing model is spec 3.

### Privacy

- Keys are read only from environment variables, never written to the settings file, the Knowledge Base or the index, and never printed.
- In local Mode nothing leaves the computer. In hosted search Mode, Chunk text (on reindex) and Request text (on search) go to OpenAI, and nothing else does.

## Testing Decisions

- A good test calls the public actions and checks what a user or a later spec sees: the hits returned (which Chunks, in what order, with what labels), command output and exit codes, and the settings file. It does not check SQL, FTS query strings, fusion internals or private helpers. A refactor that keeps behaviour must not break tests.
- **The one seam, Knowledge Base `search`:** tests use a temporary folder, the existing fake embedder and a new fake re-ranker. Cases:
  - an exact-word Request finds the Chunk containing that word even when the fake vectors say it is unrelated (keyword side works);
  - a Request with no shared words finds the Chunk whose fake vector matches (meaning side works);
  - a Chunk found by both lists outranks one found by only one, before re-ordering;
  - the fake re-ranker's order decides the final order, and only the top `k` come back;
  - `k` larger than the number of Chunks returns them all;
  - notes Chunks are returned and marked as notes;
  - Requests with quotes, `*`, `-`, `:`, `AND`, `NEAR`, brackets or emoji do not error;
  - an empty Request is rejected, and an empty or missing index returns no hits;
  - after a refresh that adds, changes or deletes a file, both keyword and meaning search see the change (no stale keyword rows);
  - a spec-1-format index is rebuilt on refresh and is then searchable.
- **Switching the model:** with two fake embedders of different names in the lookup table, build an index with A, construct the Knowledge Base with target B, and check that search still works and embeds the Request with A. After refresh, it uses B. A refresh that fails part-way (a fake embedder that raises) leaves search working on A. With A missing from the lookup, search returns keyword-only results.
- **Fake re-ranker:** deterministic, for example scoring by a test-supplied table or by word overlap, so tests can force an order that differs from the fused order.
- **Command line:** smoke tests with the config directory pointed at a temporary folder and fakes injected, as in spec 1. They cover `mode` show and set, refusal without the needed environment key, an unknown Mode value in the settings file, `search` output and its pending-switch notice, and `status` showing Modes, pending re-embed and key presence, never key values.
- **Slow tests** (marked, skippable like spec 1's): the real MiniLM re-ranker scores an obviously relevant text above an unrelated one, and an end-to-end search on a small fixture with the real local models. No test calls OpenAI. The hosted embedder is tested with a fake HTTP layer for batching, retry on rate limit, and a clear error on a bad key.
- **Prior art:** the spec 1 tests (`tests/test_chunks.py`, `tests/test_import.py`, `tests/test_rebuild.py`, `tests/test_settings.py`) and the fake embedder fixture in `tests/conftest.py`. The prototype's `search` in `prototype/pipeline.py` shows the hybrid, fusion and re-rank behaviour to match, but it is not test code.

## Out of Scope

- Context Packs, the summary model call, and the Current Decision rule: spec 3.
- Match Score, the "not found" floor, calibrating re-ranker scores, the Test Set and tuning the search constants and the 0.72 merge cutoff: spec 4.
- Sync and the extension, including the long-running local program that will run reindex in the background: specs 5 and 6.
- Filtering search by Platform, date or chat; showing only one hit per Conversation.
- Hosted re-ranking (Voyage, Cohere), Voyage embeddings, and embedding models other than bge-small and OpenAI text-embedding-3-small (for example nomic or bge-m3).
- Storing API keys in the program, or in an OS keychain.
- Resuming a half-finished rebuild. A failed rebuild starts over next time.
- Automatically refreshing the index before a search, or watching the folder.
- Approximate nearest-neighbour indexes or vector databases.

## Further Notes

- Re-ranker CPU speed on the target laptop is unmeasured (ticket 08). Re-ranking 20 Chunks of up to 1,800 characters should be fast, but check this on the real machine with the slow test.
- Hosted embeddings score about the same as bge-small on the owners' MTEB numbers (ticket 08). Hosted search is mainly a choice for speed or a weak laptop, not quality.
- With bge-small, Chunks over about 450 tokens are truncated by the model. Spec 1's 1,800-character cap is meant to prevent this. OpenAI's 8,192-token limit removes it.
- Brute-force meaning search loads every vector per search. At personal scale (tens of thousands of Chunks) this is fine. Revisit only if search gets slow.
- A rebuild with hosted embeddings costs money roughly in proportion to the Knowledge Base size, and a failed rebuild repays that cost on retry. Acceptable for one user in v1.
