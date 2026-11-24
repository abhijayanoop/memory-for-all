# 02: Bench: run and report

**What to build:** The user runs one command on a Knowledge Base and gets the times that matter: search (first and later searches, each step), the incremental reindex after a Sync-sized change, a full rebuild's rate and projected total, `status`, and the index size on disk. Each time is marked pass or fail against the agreed budgets at 100,000 Conversations (report only below that), every run is kept in a results file for before/after comparison, and a failed budget gives a non-zero exit. See the spec: `.scratch/scale-and-speed/spec.md` (Solution, budgets table; Implementation Decisions, "Bench module": `measure`, Requests, `Report`, "Command line"; stories 8 to 15, 17 to 21).

**Blocked by:** 01 (Bench: generate changed copies of real Conversations)

**Status:** ready-for-agent

- [ ] `measure(kb, writer=None, requests=None, sync_size=100, clock=…) -> Report` on a Knowledge Base whose index is current
- [ ] Search: a first search in a fresh Knowledge Base object (cold), then the rest (warm); median and worst; time per step (keyword, meaning, fusion, re-ranking)
- [ ] Incremental reindex: applies a Sync-sized change (default 100: half new copies, half changed existing ones), then times `refresh_index`
- [ ] Full rebuild: times rebuilding a sample into a scratch index; reports Conversations per minute and a projected total; the real full rebuild is timed only with `--full-rebuild`
- [ ] `status` time; index size on disk by part (text and keyword index, vectors); vectors' memory size for the current model
- [ ] Requests default to a seeded sample of 20 user messages (first line, cut to Request length) from the measured Knowledge Base; a file with one Request per line may be passed instead
- [ ] `Report` holds every timing, Conversation and Chunk counts, settings (search Mode, embedder, re-ranker, `RERANK_TOP`, `MEANING_TOP`, `KEYWORD_TOP`, approximate search on/off) and a verdict per budget: `pass`, `fail`, or `report only` below 100,000 Conversations (warm search under 2 s, incremental reindex under 1 min; cold search reported only)
- [ ] `bench run --kb <folder> [--requests <file>] [--full-rebuild]` prints progress and the report, appends it as one JSON line (with date and code version) to a results file in the measured Knowledge Base's folder, and exits non-zero if any budget fails
- [ ] Tests with fakes and a scripted clock: the report holds every timing and count; `report only` below 100,000; with the count at the threshold, a 3 s search gives `fail` and 1 s gives `pass`
- [ ] Command-line smoke test: `bench run` prints the report, appends one line to the results file, and exits non-zero when a budget fails
