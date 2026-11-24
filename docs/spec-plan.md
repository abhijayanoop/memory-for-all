# Spec plan for v1

One spec per feature, built in this order. For each spec the flow is: settle open decisions (short grilling) → `/to-spec` → `/to-tickets` → `/implement-spec`.

`/to-spec` writes one spec and does not interview, so decisions must be settled first. `/to-tickets` and `/implement-spec` also work on one spec at a time.

| # | Spec | What it covers | Decisions needed first |
|---|---|---|---|
| 1 | Knowledge Base and Chunking | Project skeleton (folders, test setup, one run command). Markdown file layout (ticket 09). Chunk rules (ticket 03). Rebuild the index from the files. | None (03 and 09 done) |
| 2 | Search and Modes | Keyword plus meaning search merged with reciprocal rank fusion, re-ordering of the top few. Two Mode settings (search, pack-writing), default fully local. Background re-embed when the embedder changes. | None (08 done) |
| 3 | Context Pack | Summary, key decisions, source Chunks. Current Decision rule: newest leads, pack notes what it replaced. | None (04 done) |
| 4 | Quality | Match Score, "not found" floor, Test Set from real chats, five quality checks. | None (05 done) |
| 5 | Sync (ChatGPT and Claude) | A Reader per Platform, layered fallback, "sync degraded" banner, guided export, report button. | None (02 done) |
| 6 | Extension | Local link with pairing key (ticket 06), preview, text insertion with clipboard fallback (ticket 07), "working" indicator. | None (06 and 07 done) |
| 7 | Scale and Speed | Measure search, reindex and Context Pack time at 1,000, 10,000 and a few hundred thousand Conversations, then fix what is slow: brute-force pure-Python meaning search (move to numpy, then an approximate nearest-neighbour index if needed), the per-search scan of every file for the reindex hint, re-ranker cost, full re-embed time and index size. Every change must keep the spec 4 quality checks passing on the Test Set, so speed never costs Context Pack quality. | Settled 2026-11-22: on the user's laptop, fully local, at 100,000 Conversations: search under 2 s, Context Pack under 30 s, incremental reindex after a sync under 1 min; full rebuild may take hours in the background; a few hundred thousand Conversations must work but need not meet these times. Speed is measured on generated Conversations (copies of real ones with changes, kept outside the repo); quality stays on the real Test Set. |

## Why this order

Specs 1 to 4 are Python only and testable without a browser. The riskier browser work (5 and 6) comes last. Sync (5) comes before the Extension (6) because the Extension needs synced data. 5 and 6 can be swapped to see something in the browser sooner. Scale and Speed (7) comes last so it can be measured on real synced data and checked against spec 4's Test Set.

## Not in v1 (later specs)

Gemini; choosing the Current Decision when chats disagree subtly; deleting and forgetting chats; packaging; stale-sync warning; non-active branches and attachment files.

## Source of decisions

`.scratch/memory-for-all-v1/map.md` and `.scratch/memory-for-all-v1/issues/01..09-*.md`. Once tickets 02, 04 and 05 are closed, the Wayfinder map can be retired.
