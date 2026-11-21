# 01: Project skeleton and first import

**What to build:** A user can run `uv run memoryforall import <folder> --kb <path>` on a folder of Platform-neutral Conversation JSON files and get one readable Markdown file per Conversation in their Knowledge Base. `uv run memoryforall status --kb <path>` shows how many Conversations each Platform has. This ticket also sets up the Python package (Python 3.12, `uv`, `pytest`) that every later ticket builds on. See the spec: `.scratch/knowledge-base-and-chunking/spec.md` (Project skeleton; Platform-neutral Conversation; File layout and format).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] The local program is its own Python package in the repo, separate from `prototype/`; `uv run pytest` runs the tests and `uv run memoryforall` runs the command line
- [ ] `import` validates each JSON file against the Conversation shape (platform `chatgpt`/`claude`, non-empty chat_id, ISO times, senders `user`/`assistant`); an invalid file is rejected with a reason and the rest continue
- [ ] Messages with empty text and no attachments are dropped; times are stored in UTC; a null title becomes "untitled"
- [ ] Each Conversation is written to `<platform>/<YYYY-MM>/<YYYY-MM-DD>-<title slug>-<chat_id>.md` using the created date; the slug strips Windows-forbidden and control characters, uses `-` for spaces, trims dots and spaces, is capped at 60 characters, and falls back to "untitled"
- [ ] The file has YAML front matter (platform, chat_id, title, created, updated, status `on platform`), then `### User · <time>` / `### Assistant · <time>` headings with text verbatim, `attachment: <name> (not saved)` lines, and an empty `## My notes` section at the end
- [ ] Writes are atomic (temporary file in the same folder, then replace)
- [ ] A written file reads back into the same Conversation (round-trip), including code fences, lines that look like headings but are not in the exact form, emoji, and an empty Conversation
- [ ] Markdown files without `platform` and `chat_id` front matter are not treated as Conversations
- [ ] `status` prints the Conversation count per Platform
- [ ] Tests use temporary folders and small synthetic fixtures only, never real chats
