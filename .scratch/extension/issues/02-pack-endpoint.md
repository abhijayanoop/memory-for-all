# 02: Pack endpoint

**What to build:** The paired extension can ask the running program for a Context Pack and get back everything the preview needs, written exactly as the `pack` command writes it with the user's saved pack-writing Mode. Failures come back with the same fix-it messages the command line prints, and only one pack is written at a time. See the spec: `.scratch/extension/spec.md` (Implementation Decisions, "Pack endpoint (program side, seam B)"; stories 27, 33, 55 to 58, 62, 64).

**Blocked by:** 01 (Pairing and the key check), spec 3 ticket 01 (`.scratch/context-pack/issues/01-pack-end-to-end-with-local-writer.md`)

**Status:** ready-for-agent

- [ ] `POST /pack` `{request}` (keyed) builds the Knowledge Base and writer exactly as the `pack` command does (settings, pack-writing Mode, hosted-key check before any work) and calls `pack(kb, request, writer)` unchanged
- [ ] The answer holds `text`, `nothing_found`, `match_score` (`percent`, `missing`, `text`), `sources` (`n`, `title`, `platform`, `date`), `notices` (re-embed pending, keyword-only, over limit, each a plain sentence), `chars`, `limit` (9,500) and `seconds`; Chunk texts are not repeated
- [ ] If spec 4's Match Score is not built yet, `match_score.text` carries spec 3's needs coverage instead
- [ ] Errors share one shape `{error: {kind, message}}` with the command line's fix-it text: `empty_request` 400, `busy` 409, `index_empty` 409, `hosted_key_missing` 400, `writer_failed` 502
- [ ] A non-blocking lock: a second pack request while one runs gets `busy` without waiting; the lock is released when the pack finishes, including after a writer failure
- [ ] Health and sync endpoints keep answering while a pack runs
- [ ] Shared JSON fixtures for pack answers and errors
- [ ] pytest through the real server with the fake embedder and re-ranker and spec 3's scripted fake writer: same pack text as calling `pack` directly; every answer field present; each error kind's status and message; `busy` while the fake writer blocks; lock released after a writer failure
