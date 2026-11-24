# 06: Hosted writing models (OpenAI and Claude)

**What to build:** With the pack-writing Mode set to hosted (`mode pack hosted --api openai|claude`, from spec 2), `pack` writes the pack with the user's own OpenAI or Claude key. Only the Request, source Chunks and verified quotes are sent, and the key is never saved or printed. A missing key is refused before any work. Rejected keys and API failures give a clear error and no pack. See the spec: `.scratch/context-pack/spec.md` (Modules 2 and 3; Hosted Mode and privacy).

**Blocked by:** 01 (Pack end-to-end with the local writing model)

**Status:** ready-for-agent

- [ ] The CLI builds the writer from `pack_mode` / `pack_api` in the settings file (local gives the Ollama writer)
- [ ] OpenAI writer: a small current chat model (named constant), key from `OPENAI_API_KEY`, temperature 0, JSON output
- [ ] Claude writer: a small current Claude model such as `claude-haiku-5-5` (named constant), key from `ANTHROPIC_API_KEY`, temperature 0, JSON output
- [ ] A missing key is refused before search or any model call, with the same message `mode pack` gives; rejected keys, rate limits and other API errors become the writing-model error with a fix-it message
- [ ] Keys are read from the environment at call time, never stored or printed
- [ ] Tests: CLI with hosted Mode and a missing key is refused and the fake writer gets 0 calls; the writer is chosen from settings. No test calls OpenAI or Claude
