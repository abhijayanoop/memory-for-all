# Spec 7: Scale and Speed

Status: ready-for-agent

Source decisions: `docs/spec-plan.md` (spec 7, budgets settled 2026-11-22). Builds on spec 1 (`.scratch/knowledge-base-and-chunking/spec.md`: save, refresh, safe rebuild), spec 2 (`.scratch/search-and-modes/spec.md`: search, rank fusion, re-ranker, re-embed), spec 3 (`.scratch/context-pack/spec.md`: `pack`), spec 4 (`.scratch/quality/spec.md`: `quality score` as the gate), spec 5 (`.scratch/sync/spec.md`: background refresh after a Sync, saves one by one) and spec 6 (`.scratch/extension/spec.md`: pack `seconds`). Vocabulary: `GLOSSARY.md`. ADR 0001 applies: the index is derived and disposable, the Markdown files are the truth.

Seams settled with the user (2026-11-24): every speed fix stays behind the seams that already exist (`KnowledgeBase.search`, `refresh_index`, `save`, and spec 3's `pack`), with the existing tests as the regression guard and new cases added there. The one new seam is a bench module (`generate` and `measure`) exposed as a `bench` command. Spec 4's `quality score` is the quality gate and adds no seam.

## Problem Statement

Everything so far was built and tested on a handful of Conversations. My real history will grow to tens of thousands of Conversations, and I want it to keep working when it reaches 100,000 or more. Today it would not:

- Every search loads every Chunk, vector and text from the index and computes meaning similarity one number at a time in pure Python. At hundreds of thousands of Chunks that is minutes, not seconds.
- Every search also opens the timestamp of every Conversation file to decide whether to print "files changed since the last reindex", which alone grows with the size of my history.
- Every reindex reads and fingerprints every Conversation file, even when a Sync changed only a few, so the refresh after each Sync gets slower every day.
- Saving one Conversation searches the whole folder for its old file, so a large first Sync slows down as it goes.
- `status` reads every Conversation and every Chunk just to count them.
- A full rebuild (after switching the embedding model, or after a chunk rule change) may take hours at this size, and if it is interrupted it starts again from nothing.

I don't know which of these matter most, because nothing has been measured. I also cannot measure on my real history alone: it is not yet 100,000 Conversations, and making it faster must never make my Context Packs worse.

## Solution

1. **Measure first.** A `bench` command makes large Knowledge Bases of generated Conversations (copies of my real ones with changes, kept outside the repo) at 1,000, 10,000, 100,000 and about 300,000 Conversations, and times what I care about on each: search, Context Pack, the incremental reindex after a Sync, a full rebuild, saving, `status`, and the index size on disk. It reports each time against the agreed budgets and keeps every run's results so before and after can be compared.
2. **Fix what is slow, in order of cost.** The known fixes come first (fast meaning search with numpy, reading only the Chunks search needs, a reindex hint that does not open every file, an incremental reindex that skips unchanged files without reading them, a quick file lookup on save, counting from the index in `status`, a resumable full rebuild, and searches that keep working while a refresh runs). Further fixes (an approximate nearest-neighbour index, a cheaper re-ranking step, batched embedding across Conversations, smaller stored vectors) are made only if the bench shows a budget is still missed after the known fixes.
3. **Never trade quality for speed.** Every change must keep all five spec 4 quality checks passing on my real Test Set (`quality score` exits 0), and the existing test suite passing. An approximate search must also find nearly all of what exact search finds on the large generated Knowledge Base.

Budgets (settled 2026-11-22), on my laptop, fully local Mode, at 100,000 Conversations:

| What | Budget |
|---|---|
| Search | under 2 s |
| Context Pack | under 30 s |
| Incremental reindex after a Sync | under 1 min |
| Full rebuild | may take hours, in the background, while search keeps working |
| A few hundred thousand Conversations | must work (no crash, no running out of memory), times reported but not held to the budgets |

## User Stories

### Measuring

1. As a user, I want to make a large Knowledge Base of generated Conversations with one command, so that I can measure speed at sizes my real history has not reached yet.
2. As a user, I want generated Conversations to be copies of my real ones with changes, so that their length, shape and wording are like mine.
3. As a user, I want each copy changed (new chat id, new title suffix, dates spread across several years, some messages reworded, reordered or dropped), so that copies are not identical text that would make search unrealistically easy or hard.
4. As a user, I want generation to be repeatable from a seed, so that two measurements at the same size measure the same Knowledge Base.
5. As a user, I want generation refused when the destination is inside my real Knowledge Base folder or inside the repo, so that private copies never get committed and my real Knowledge Base is never polluted.
6. As a user, I want generated Conversations saved through the same save action as Sync, so that generating also measures how fast saving is at scale.
7. As a user, I want generation to be able to add to an existing generated Knowledge Base (grow 10,000 to 100,000), so that I don't regenerate from zero for each size.
8. As a user, I want one command that times search, Context Pack, incremental reindex, full rebuild, saving and `status` on a given Knowledge Base, so that measuring is one step.
9. As a user, I want search timed over many Requests and reported as the typical (median) and the worst time, so that one lucky Request doesn't hide a slow path.
10. As a user, I want the bench Requests taken by default from user messages in the Knowledge Base being measured, so that I don't have to write any and they look like real Requests.
11. As a user, I want to be able to pass my own Requests file instead, so that I can time the Requests I actually make.
12. As a user, I want search timed both on the first search after the program starts and on later searches, so that I see both what the command line and the long-running program feel like.
13. As a user, I want the time of each search step reported (keyword, meaning, fusion, re-ranking), so that I know which step to fix.
14. As a user, I want the incremental reindex timed after a change the size of a typical Sync (some new and some changed Conversations), so that the "under 1 minute after a Sync" budget is measured on the thing it is about.
15. As a user, I want the full rebuild reported as Conversations per minute and an estimated total, so that I know how long a model switch will take without always waiting hours.
16. As a user, I want the Context Pack timed with the real local writing model when it is reachable, and skipped with a note when it is not, so that a missing model doesn't fail the whole bench.
17. As a user, I want the index size on disk reported, split into its parts, so that I know what the Knowledge Base costs in disk space.
18. As a user, I want each result marked pass or fail against its budget when the Knowledge Base has exactly 100,000 Conversations, and only reported at other sizes, so that the budgets apply where they were agreed.
19. As a user, I want the bench to exit non-zero when a budget fails at 100,000 Conversations, so that it can be used as a gate like `quality score`.
20. As a user, I want every bench run appended to a results file next to the generated Knowledge Base with the date, the code version, the Conversation and Chunk counts and the settings used, so that I can compare runs before and after each change.
21. As a user, I want the bench to print what it is doing and how far along it is, so that a long run doesn't look frozen.

### Search speed

22. As a user, I want a search over 100,000 Conversations to finish in under 2 seconds, so that the extension feels instant enough to use mid-conversation.
23. As a user, I want meaning search to give the same results as before the speed change (apart from exact ties), so that speed does not change what I find.
24. As a user, I want search to read only the Chunks it will show or re-rank, not every Chunk in the index, so that its cost does not grow with every chat I add.
25. As a user, I want the "files changed since the last reindex" hint to keep working without opening every Conversation file on every search, so that the hint doesn't cost more than the search.
26. As a user, I want the hint still shown after a Sync or import saved new or changed Conversations and before they are indexed, so that I know to wait for the refresh or run reindex.
27. As a user, I want "the index is empty" detected without loading the index, so that an empty-index message is instant at any size.
28. As a user, I want searches to keep working, against the last finished index, while a refresh or rebuild is running, so that a background refresh never blocks me.
29. As a user, I want a Knowledge Base of a few hundred thousand Conversations to search without running out of memory on my laptop, so that it keeps working as my history grows.
30. As a user, I want any approximate search, if one is added, to find at least 95% of what exact search finds, so that speed costs nearly nothing in recall.
31. As a user, I want the re-ranker's cost kept inside the search budget without hurting the Finding check, so that re-ordering stays worth its time.

### Context Pack speed

32. As a user, I want a Context Pack at 100,000 Conversations written in under 30 seconds in local Mode, so that scale does not make the pack slower than on a small history.
33. As a user, I want the pack's time split into search time and writing time, so that I know whether scale or the writing model is the slow part.

### Reindex and Sync speed

34. As a user, I want the refresh after a Sync to finish in under 1 minute at 100,000 Conversations, so that new chats are searchable soon after they arrive.
35. As a user, I want reindex to skip files whose size and modification time have not changed without reading them, so that unchanged chats cost almost nothing.
36. As a user, I want a file whose size or modification time changed to be fingerprinted and re-chunked only if its content really changed, so that a touched but unchanged file is not re-embedded.
37. As a user, I want my existing index upgraded in place to the faster reindex, without a full rebuild, so that this speed change doesn't cost me hours of re-embedding.
38. As a user, I want saving a Conversation to find its old file without searching the whole folder, so that a first Sync of thousands of chats doesn't slow down as it goes.
39. As a user, I want `status` to answer in a few seconds at any size, by counting from the index and file names instead of reading every Conversation, so that checking status is cheap.

### Full rebuild

40. As a user, I want a full rebuild (after a model switch or a chunk rule change) to be allowed to take hours, so that a slow local model is acceptable.
41. As a user, I want search to keep using the old index until the rebuild is complete (as ADR 0001 requires), so that a long rebuild never leaves me without search.
42. As a user, I want an interrupted full rebuild (closed laptop, crash, Ctrl-C) to continue where it stopped the next time it runs, so that hours of embedding are not lost.
43. As a user, I want a partial rebuild built with a different model or chunk rules than the current ones thrown away, not continued, so that one index never mixes two models.
44. As a user, I want the rebuild to print its progress (Conversations done of total, and an estimate of time left), so that I know how long to leave it.
45. As a user, I want Conversations changed while a rebuild runs to be picked up by the rebuild or by the next refresh, so that nothing is silently left out.

### Quality gate

46. As a user, I want every speed change to keep all five spec 4 quality checks passing on my real Test Set, so that speed never costs Context Pack quality.
47. As a user, I want any speed change that changes search results (approximate search, fewer re-ranked Chunks, smaller stored vectors) to be judged by the Finding check and the 95% recall check before it is kept, so that a result-changing fix is only kept when it is proven harmless.
48. As a user, I want a speed change reverted if it fails a quality check and no adjusted version passes, so that the budgets never win over quality.
49. As a developer, I want the existing test suite to pass unchanged after every speed fix, so that behaviour stays exactly as specs 1 to 6 defined it.

### Hosted Mode and limits

50. As a user in hosted Mode, I want the same speed fixes to apply, so that hosted search is also fast at scale, even though the budgets were set for local Mode.
51. As a user, I want the bench to report the vectors' memory size for the current model, so that I know before switching to a larger hosted model whether it will fit on my laptop.

## Implementation Decisions

### Process

1. **Baseline first.** Before any fix, run the bench at 1,000, 10,000 and 100,000 generated Conversations on the current code and record the results. A few hundred thousand is measured once the known fixes are in (on today's code it would take too long to be useful).
2. **Known fixes**, each its own change, each followed by the test suite, `quality score` on the real Test Set, and a bench run: the fixes listed under "Known fixes" below.
3. **Conditional fixes**, only for a budget that is still missed at 100,000 after the known fixes, or for running out of memory at a few hundred thousand: the fixes listed under "Conditional fixes" below. Each one that changes search results is kept only if the Finding check still passes on the real Test Set and recall is at least 95% on the generated 100,000 Knowledge Base.
4. Constants changed for speed (for example `RERANK_TOP`) stay named constants with a comment saying the bench run and quality result that justified the value.

### Bench module (the one new seam)

- `generate(source, dest, count, seed) -> counts`: reads Conversations from the source Knowledge Base and saves `count` changed copies into the destination Knowledge Base through the existing `save` action. Each copy gets a new chat id derived from the seed and copy number, a title with a short suffix, created and updated dates shifted so the copies spread over several years of month folders, and a seeded light rewording of some messages (swapping or dropping a few words, dropping or repeating a message). If the destination already holds generated Conversations, new copies are added after them (story 7). Refuses a destination inside the source folder or inside a folder that holds a `.git` folder. Returns counts saved and the save rate.
- `measure(kb, writer, requests=None, sync_size=…, clock=…) -> Report`: on a Knowledge Base whose index is current, it times:
  - search: a first search in a fresh Knowledge Base object (cold), then the rest (warm), with the time of each step; median and worst;
  - pack: through spec 3's `pack`, when a writer is given; split into search and writing time;
  - incremental reindex: applies a Sync-sized change (default 100 Conversations: half new copies, half changed existing ones), then times `refresh_index`;
  - full rebuild: times rebuilding a sample of Conversations into a scratch index and reports Conversations per minute and the projected total (the real full rebuild is timed only when asked, because it takes hours);
  - `status`, and index size on disk by part (text and keyword index, vectors, any approximate index);
  - recall, when an approximate search is active: the share of exact search's top `MEANING_TOP` that the approximate search also returns, over the bench Requests.
  The clock is injectable so verdicts can be tested.
- Requests default to a seeded sample of 20 user messages (first line, cut to a Request-like length) from the measured Knowledge Base. A Requests file (one per line) may be passed instead.
- `Report` holds every timing, the Conversation and Chunk counts, the settings (search Mode, embedder, re-ranker, `RERANK_TOP`, `MEANING_TOP`, `KEYWORD_TOP`, approximate search on or off) and a verdict per budget: `pass` or `fail` at 100,000 Conversations, and `report only` at other sizes.

### Command line

- `bench generate --from <kb> --to <folder> --count N [--seed S]`.
- `bench run --kb <folder> [--requests <file>] [--full-rebuild]`: builds the Knowledge Base and the writer as `pack` does (writer skipped with a note when the local writing model is unreachable), runs `measure`, prints the report, appends it as one JSON line to a results file in the measured Knowledge Base's folder, and exits non-zero if any budget fails.

### Known fixes (behind existing seams)

- **Meaning search with numpy.** numpy is already installed as a dependency of fastembed; it becomes a direct dependency. Vectors are kept as one float32 matrix in a file inside the index folder, written by `refresh_index` from the stored Chunk vectors whenever Chunks changed, swapped in atomically like the index, and memory-mapped by search, so a cold search does not read every vector from SQLite. Similarity is one matrix-vector product; the top `MEANING_TOP` are taken by partial sort. Rank fusion and its tie rule (equal similarity, equal rank) are unchanged. The matrix is derived and disposable: a missing or mismatched matrix is rebuilt from the stored vectors by the next refresh, and until then search falls back to keyword only with spec 2's notice.
- **Read only what search needs.** Search fetches the text and labels of the fused candidates (at most `KEYWORD_TOP + MEANING_TOP`) by id, not every row. "The index is empty" is a count query.
- **Reindex hint without opening every file.** The hint compares the index's last refresh time with the modification times of the Platform month folders (a few hundred folders, not every file). Saving writes through a temporary file and a rename in the month folder, so every save, rename and removal by the program or by Sync changes its folder's time. A hand edit that rewrites a file in place may not show the hint; it is picked up by the next reindex or the refresh after the next Sync. (Shortcut, accepted: the hint is advice, not a guarantee.)
- **Incremental reindex skips unchanged files by size and modification time.** The index's file table gains a size and a modification time per file. A file whose size and modification time match is not read. A file where either differs is fingerprinted as today and re-chunked only if the fingerprint changed (then its size and time are updated either way). The new columns are added to an existing index in place, empty, which means "fingerprint once"; this is not a rules version change, so no rebuild or re-embed is triggered.
- **Quick lookup on save.** The Knowledge Base object keeps a map from (Platform, chat id) to file, built on first use from one scan of file names (`…-<chat_id>.md`), confirmed by parsing only the candidate, and updated by `save`, rename and removal. A Sync of thousands of chats does one folder scan, not one per chat.
- **`status` counts cheaply.** Conversations per Platform are counted from file names in one scan; Chunks are a count query. Nothing loads every Conversation or every Chunk.
- **Searches during a refresh.** The index uses SQLite's write-ahead log mode so a search reads the last committed index while a refresh writes. The vector matrix is swapped only after the refresh commits.
- **Resumable full rebuild.** The rebuild writes into the side index as today but commits every few hundred Conversations and keeps the side index (and does not delete it) when interrupted or when an embedding call fails. On the next rebuild, a side index built with the same embedder, dimension and rules version is continued: files it already holds with matching fingerprints are skipped. A side index with different ones is deleted and started over. The live index stays live until the swap, as now. Progress (done of total, Conversations per minute, estimated time left) is printed to standard error.

### Conditional fixes (only if the bench says so)

- **Approximate nearest-neighbour index**, if numpy search still misses 2 s at 100,000 Conversations, or the vectors do not fit in memory at a few hundred thousand. Requirements for the library chosen: installs from a pip wheel on Windows, runs in-process (no server), stores its index inside the index folder, is rebuilt from the stored vectors (derived and disposable), and supports adding and removing vectors so the incremental reindex budget still holds. Recall ≥ 95% against exact search on the bench Requests at 100,000. The choice is recorded as an ADR.
- **Cheaper re-ranking**, if the re-ranker alone takes most of the 2 s: first lower `RERANK_TOP`, then cut each re-ranked text to the re-ranker's input limit before sending; kept only if the Finding check passes.
- **Batched embedding across Conversations**, if per-call overhead is a large part of rebuild or incremental reindex time: the refresh hands several Conversations' Chunk texts to the embedder in one call. The chunker's rules and output are unchanged.
- **Smaller stored vectors** (half-precision floats in the matrix), if memory is the limit at a few hundred thousand: kept only if recall stays at least 95% and the Finding check passes.

### What this spec does not change

- The Markdown file format, the chunk rules (`CAP`, `MERGE_SIMILARITY`), rank fusion, the Context Pack's format and model calls, the Match Score, the settings file, Sync's throttling, and the command outputs other than new progress lines and the new `bench` command.
- The rules version is not bumped by any known fix, so no known fix forces a re-embed.

## Testing Decisions

- A good test drives an existing seam (`search`, `refresh_index`, `save`, `pack`, the command line) or the bench seam, and checks what the user sees: results and their order, counts, notices, progress, exit codes, how many times the embedder was called. It does not check the matrix file layout, SQL, or which numpy calls are used. A refactor that keeps behaviour must not break a test.
- **Regression guard:** the existing tests (`test_search.py`, `test_rebuild.py`, `test_model_switch.py`, `test_import.py`, `test_chunks.py`, `test_modes.py`, `test_review_fixes.py`, and specs 3 to 6's tests) pass unchanged after every fix. They already pin search order on fixtures (including ties), refresh after changes, the safe swap and the model switch.
- **New cases at the Knowledge Base seam** (temporary folder, fake embedder and re-ranker from `tests/conftest.py`, counting embedders as in `test_model_switch.py`):
  - search after refresh finds added and changed Chunks and not removed ones through the vector matrix; a deleted or damaged matrix gives keyword-only results with the notice, and the next refresh restores meaning search;
  - search results on the existing fixtures are the same with the matrix as before (the existing order tests cover this);
  - the reindex hint appears after `save` of a new or changed Conversation and does not appear after a refresh with no changes;
  - an empty index gives the empty-index message;
  - a file touched (new modification time, same content) is not re-embedded; a file with changed content and the same size is re-chunked; an unchanged file is not read again (embed call count stays 0 on a second refresh);
  - an index from before this spec (file table without the new columns) is upgraded in place by refresh with zero embed calls;
  - an embedder that fails after N Conversations during a rebuild leaves the live index searchable; the next rebuild with a working embedder continues and makes fewer embed calls than a fresh rebuild; a side index from another embedder is discarded, not continued;
  - a search run while a refresh is blocked inside the embedder (on another thread) returns the old index's results;
  - saving into a Knowledge Base with many fixture files finds and replaces the existing file (renamed title included), and `status` counts match the files.
- **Bench seam:**
  - `generate` from a small fixture Knowledge Base: the requested count is saved, every file parses, chat ids are distinct from the source and from each other, dates spread across months, text differs from the source, the same seed gives identical output, a second run adds rather than overwrites, and a destination inside the source folder or inside a folder with `.git` is refused;
  - `measure` with fakes and a scripted clock: the report holds every timing and count; budgets give `report only` below and above 100,000 Conversations; with the Conversation count faked at the threshold, a clock that makes search take 3 s gives `fail`, 1 s gives `pass`; pack is skipped with a note when no writer is given;
  - recall is computed correctly when the approximate search returns a known subset (only once an approximate search exists).
- **Command line smoke tests** (config directory pointed at a temporary folder, fakes injected, as in `tests/test_modes.py`): `bench generate` makes the files and prints counts; `bench run` prints the report, appends one line to the results file and exits non-zero when a budget fails.
- **Not in the test suite:** runs at 10,000 and above, the real local models' timings, and the real Test Set. Those are run by hand with `bench run` and `quality score`, and their results are kept in the results file outside the repo. No test calls OpenAI or Claude.
- **Prior art:** `tests/test_search.py` (search with fakes and table embedders), `tests/test_rebuild.py` (refresh after file changes, safe swap), `tests/test_model_switch.py` (counting embedders, old index stays live), `tests/test_modes.py` (command-line smoke tests), `tests/conftest.py` (fake embedder, keep-order re-ranker), spec 4's `quality` tests (gate with exit codes).

## Out of Scope

- Budgets for hosted Mode. The fixes apply to it, but the budgets were set for fully local Mode.
- Making the first Sync of a large history fast: Sync's half-second gap between Platform requests is deliberate (spec 5), so a first Sync of 100,000 chats takes many hours by design.
- GPU embedding, multi-process embedding, or a separate search server.
- Changing the chunk rules, rank fusion or Context Pack format for speed.
- Packaging, and running the program as a system service.
- Deleting and forgetting chats, and other later specs listed in `docs/spec-plan.md`.
- Committing generated Conversations, bench results or Test Set content to the repo.

## Further Notes

- The chunk count per Conversation in real chats is not known yet; it decides the vector memory (about 1.5 KB per Chunk with the local 384-dimension model, about 6 KB with the hosted 1,536-dimension model). The baseline bench run answers it. At an estimated 5 to 10 Chunks per Conversation, 100,000 Conversations is 0.5 to 1 million Chunks, which numpy can search well under a second if the matrix fits in memory; the hosted model at a few hundred thousand Conversations is where an approximate index or smaller vectors are most likely needed.
- The search budget is measured both cold (command line) and warm (the long-running program behind the extension). The 2 s budget is judged on warm search, because the extension is how searches are made day to day; cold search is reported. If cold search is far over 2 s, that is worth raising, but it is not a fail.
- The re-ranker's cost does not grow with the Knowledge Base (it always scores at most `RERANK_TOP` Chunks), so it matters only if it alone is near the 2 s budget on the laptop.
- The quality gate runs on the real Test Set, which lives in the real Knowledge Base, not the generated one. Changes that only matter at scale (approximate search) are also checked with the recall measure on the generated Knowledge Base, because the real Test Set is too small to show them.
- No new glossary terms: "generated Conversations" and "bench" are working words in this spec, not domain terms.
