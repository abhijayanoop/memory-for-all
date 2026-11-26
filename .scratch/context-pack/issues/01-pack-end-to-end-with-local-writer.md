# 01: Pack end-to-end with the local writing model

**What to build:** `pack "<request>"` returns a real Context Pack built only from verified exact quotes. It searches for up to 8 Chunks and keeps those at or above the "not found" floor. If none pass, it prints "Nothing found in your chats for this" without calling the model. Otherwise the local writing model (Qwen3-4B-Instruct through Ollama) chooses quotes grouped by subject (call 1). The program checks each quote word for word against the sources and finds its sources itself. It renders the header line, the Request, Key decisions and facts with [n] numbers, and the numbered Sources. If the writing model fails, the user gets a clear fix-it error and no pack. See the spec: `.scratch/context-pack/spec.md` (Modules 1 to 3; Pipeline: Search, Call 1, Quote verification, Rendering).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `pack(kb, request, writer) -> PackResult` with `text`, `nothing_found`, `sources`, `decisions`, `dropped`, `seconds` (later tickets add `needs` and `over_limit`)
- [ ] Writing model interface: `name`, `ask(prompt) -> dict`, temperature 0, JSON output; one writing-model error type with a fix-it message
- [ ] Local writer calls Ollama's HTTP API with `qwen3:4b-instruct` (named constant). "Not running" and "model not pulled" become the error with fix-it text (start Ollama, `ollama pull qwen3:4b-instruct`)
- [ ] An answer that is not JSON is the writing-model error; missing JSON fields are treated as empty
- [ ] `search(request, k=8)`, then keep only hits with re-ranker score >= `NOT_FOUND_FLOOR` (named, untuned constant). If none remain, `nothing_found` and no model call
- [ ] Call 1 asks only to choose and order exact quotes grouped by subject, in the spec's JSON shape (`subjects`, `quotes`, `replaces`, `accepted_by`); the model's source numbers are never asked for or used
- [ ] Verification: lower-case, collapse runs of non-word characters to one space, substring of a source's normalised text. Unverified quotes are dropped with reason "not in any source"; a subject with no verified quote is dropped; if no subject survives, `nothing_found`
- [ ] Rendered pack: "Context from my past chats (Memory for All):", **Request:**, **Key decisions and facts:** (quotes with [n]), **Sources:** (`[n] <title> (<Platform>, <date>)` then Chunk text). No instructions to the model, no Match Score
- [ ] CLI `pack "<request>"`: pack on stdout. Time taken and spec 2's pending re-embed / keyword-only notices on stderr. "Nothing found in your chats for this" exits 0; a writing-model error exits non-zero. Empty Request and empty/missing index behave as `search` does
- [ ] Tests at the `pack` seam with a scripted fake writer that records its call count: invented quote dropped; case/punctuation differences accepted; wrong source claimed by the fake makes no difference; floor gives `nothing_found` with 0 calls; empty index gives `nothing_found`; all quotes dropped gives `nothing_found`; raising and non-JSON fakes give the error and no pack
- [ ] CLI smoke tests with fakes injected (stdout/stderr split, exit codes)
- [ ] Slow test, skipped when Ollama is unreachable: an end-to-end pack on a small fixture with the real local models is well-formed, every quote is verified, and the time is recorded against the 30 s budget
