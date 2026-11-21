# 04: Mode settings

**What to build:** A user can see and set where their models run. `mode` shows both Modes; `mode search local|hosted` and `mode pack local|hosted [--provider openai|claude]` set them. Both default to local. Hosted choices are refused with a clear reason when the needed key is missing from the environment (hosted search needs `OPENAI_API_KEY`, since Claude offers no embeddings; hosted pack-writing needs the chosen provider's key). `status` shows both Modes and each relevant key as `present` or `missing`, never its value. This ticket only stores and checks the settings; using hosted embeddings is ticket 05, and calling a writing model is spec 3. See the spec: `.scratch/search-and-modes/spec.md` (Settings; Mode switching; Pack-writing Mode; Privacy).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Settings file gains `search_mode`, `pack_mode`, `pack_provider`; missing values mean local; the Knowledge Base folder setting is kept when Modes change
- [ ] Unknown Mode values in the settings file give an error naming the file and the bad value
- [ ] `mode search hosted` without `OPENAI_API_KEY` is refused and says Claude has no embeddings; with it, prints that Chunks and Requests will be sent to OpenAI
- [ ] `mode pack hosted --provider claude|openai` checks `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- [ ] Keys are read only from environment variables and are never written to any file or printed
- [ ] `status` shows both Modes and key presence
- [ ] Command-line tests with a temporary config directory and controlled environment variables
