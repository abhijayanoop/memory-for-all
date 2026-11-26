# 02: Test Set and `quality add`

**What to build:** The user can build their Test Set from real chats with one helper command. `quality add "<question>" --label answerable|partly|unanswerable [--changed-mind]` shows the top 20 search hits, lets the user mark right Chunks by picking hits and giving a short exact phrase from each (or naming a Conversation plus phrase for a Chunk the search missed), and for changed-mind questions asks for the newest-choice and replaced-choice phrases. The Test Set is a readable JSON file in a `quality/` folder in the Knowledge Base folder, outside the repo, which reindex never reads as Conversations. See the spec: `.scratch/quality/spec.md` (User Stories 11–26; Storage; Modules 2 `load_test_set`, 3 `quality add`).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Test Set file shape as in the spec (`id`, `question`, `label`, `changed_mind`, `right` as Conversation + phrase, `current`, `replaced`); ids assigned by `quality add`, never reused
- [ ] `load_test_set` validates: `right` required unless unanswerable, `current`/`replaced` required when changed-mind, known labels only; errors name the question and field
- [ ] A shortfall against the minimums (20 questions, at least 4 unanswerable, at least 3 changed-mind) is reported, not refused
- [ ] `quality add` is interactive: top 20 hits numbered; a phrase not in its chosen hit (normalised as in spec 3's quote check) is refused; Conversation + phrase accepted for a missed Chunk; changed-mind phrases checked to exist in the Knowledge Base; unanswerable questions need no marks
- [ ] The Knowledge Base's file scan skips `quality/`; reindex output is unchanged by files there
- [ ] Tests: malformed Test Sets rejected with question and field; `quality add` smoke test with scripted standard input appends a valid question and refuses a bad phrase; reindex ignores `.md` files under `quality/`
