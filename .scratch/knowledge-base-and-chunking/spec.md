# Spec 1: Knowledge Base and Chunking

Status: ready-for-agent

Source decisions: `docs/spec-plan.md` (spec 1), `.scratch/memory-for-all-v1/issues/09-kb-file-layout.md`, `.scratch/memory-for-all-v1/issues/03-chunk-rules.md`, `docs/adr/0001-markdown-source-of-truth.md`. Vocabulary: `GLOSSARY.md`.

## Problem Statement

My Conversations are scattered across ChatGPT and Claude, locked inside each Platform. If my subscription ends or I switch Platforms, that history is gone or out of reach. Before anything can be searched or handed to another Platform, I need my Conversations stored somewhere I own: plain files I can read, edit, back up and open in Obsidian. They also need to be cut into Chunks that a search model can actually read. A whole Conversation can run to 90,000 characters, but the search model only sees about the first 2,000.

## Solution

A local Python program keeps my Knowledge Base as a folder of Markdown files, one per Conversation, outside the code repository. It accepts Conversations in a plain, Platform-neutral form, writes or updates their files, never deletes a file, and never touches my own notes. From those files it builds a hidden, disposable index of Chunks. Each Chunk is a question with its answer, at most 1,800 characters, labelled with its chat title, Platform and date, and stored with its meaning-vector. When files change (a re-sync, a hand edit, a deleted file), refreshing the index redoes only what changed. Deleting the index entirely is always safe, because it rebuilds from the files.

I use it from the command line: import a folder of Conversation files, refresh the index, see a status summary. Later specs plug in on top: Search (spec 2) reads the Chunks, and Sync (spec 5) calls the same save action the import uses.

## User Stories

### Setting up

1. As a user, I want to install and run the program with one command, so that I don't have to wire up anything by hand.
2. As a user, I want to choose where my Knowledge Base folder lives, so that it sits where I keep my other personal files.
3. As a user, I want the Knowledge Base folder path to work even when it contains spaces, so that a path like `...\personal\knowledge base` just works.
4. As a user, I want the program to create the Knowledge Base folder if it does not exist, so that first run needs no manual setup.
5. As a user, I want the Knowledge Base folder to live outside the code repository by default, so that my private chats can never be committed by accident.
6. As a developer, I want a working test setup from the first commit, so that every later ticket can be built test-first.

### Saving Conversations

7. As a user, I want each Conversation saved as its own Markdown file, so that I can open, read and back up any single chat.
8. As a user, I want files grouped by Platform and then by month, so that I can browse my history like a diary.
9. As a user, I want each file name to start with the date and include the chat title, so that I can recognise a chat by its name.
10. As a user, I want the Platform's chat ID in each file name, so that a file stays tied to its chat even if the title changes.
11. As a user, I want titles with characters Windows forbids (such as `?`, `:` or `/`) to still produce a valid file name, so that no chat fails to save.
12. As a user, I want very long titles shortened in the file name, so that paths never exceed Windows limits.
13. As a user, I want a chat with no title saved as "untitled", so that it still has a readable name.
14. As a user, I want each file to start with a header (Platform, chat ID, title, created, updated, on-platform status), so that the key facts are visible at a glance and readable by Obsidian.
15. As a user, I want messages written in order, each marked with who sent it and when, so that the file reads like the original chat.
16. As a user, I want message text kept exactly as written, including line breaks, code blocks and lists, so that nothing is mangled.
17. As a user, I want attachments recorded as a line such as `attachment: report.pdf (not saved)`, so that I know a file was shared even though v1 keeps text only.
18. As a user, I want a Conversation with no messages (for example a chat that only errored) still saved, so that my record of chats is complete.
19. As a user, I want only the active branch of a branched chat saved, so that the file shows the conversation as I last saw it.

### Re-saving and updates

20. As a user, I want re-saving a Conversation with a newer update time to rewrite its file, so that my Knowledge Base stays current.
21. As a user, I want re-saving a Conversation whose update time is the same or older to change nothing, so that repeated syncs are cheap and harmless.
22. As a user, I want a renamed chat's file renamed to match, keeping its chat ID, so that names stay accurate without creating duplicates.
23. As a user, I want a chat whose start date changes (it should not, but might) to still map to one file, so that I never get two files for one chat.
24. As a user, I want everything below a `## My notes` heading kept untouched when a file is rewritten, so that my own notes survive every re-sync.
25. As a user, I want every new file to come with an empty `## My notes` section, so that I know where my notes go.
26. As a user, I want to know that my edits to the messages themselves are replaced on the next re-sync, so that I put lasting notes in the notes section.
27. As a user, I want files written safely, so that a crash or power cut mid-write never leaves a half-written or empty file.

### Chats that disappear

28. As a user, I want a Conversation deleted on its Platform kept locally, so that my Knowledge Base remains a real backup.
29. As a user, I want such a file's header marked "no longer on the Platform" with the date it was noticed, so that I know it only exists locally.
30. As a user, I want a chat that reappears on its Platform to have its status set back, so that the header stays truthful.

### Importing

31. As a user, I want to import a folder of Conversation files in the plain Platform-neutral form, so that I can load data before automatic Sync exists.
32. As a user, I want an import to tell me how many Conversations were new, updated, unchanged or rejected, so that I know what happened.
33. As a user, I want a malformed import file rejected with a clear reason while the rest continue, so that one bad file does not stop the whole import.

### Chunks

34. As a user, I want my Conversations cut into Chunks that keep each question with its answer, so that a search result carries both what I asked and what I was told.
35. As a user, I want a question followed by several assistant replies kept as one unit, so that a split reply is not separated from its question.
36. As a user, I want a question that never got an answer kept as its own Chunk, so that what I asked is still findable.
37. As a user, I want no Chunk longer than 1,800 characters, so that the search model reads all of it.
38. As a user, I want long answers split at paragraph breaks first, then line breaks, then sentence ends, so that each piece reads naturally.
39. As a user, I want a hard cut only when a piece has no break at all, so that meaning is lost as little as possible.
40. As a user, I want every piece of a split answer to repeat its question (up to the first 300 characters) as a heading, so that each piece makes sense alone.
41. As a user, I want small neighbouring units on the same subject merged into one Chunk up to the size cap, so that short back-and-forths are not scattered across many tiny Chunks.
42. As a user, I want units on different subjects never merged, so that a Chunk stays about one thing.
43. As a user, I want Chunks never to mix two Conversations, so that each Chunk has one clear source.
44. As a user, I want every Chunk to start with `Chat: <title>`, so that search can tell which chat a Chunk belongs to (in testing this fixed a missed answer).
45. As a user, I want each Chunk labelled with its Platform, chat ID, chat title and its question's time, so that later a Context Pack can cite its source and order decisions by date.
46. As a user, I want the text in my `## My notes` section chunked too, labelled as my notes, so that my own notes can be found by search.
47. As a user, I want each Chunk to have a stable ID, so that later features (the Test Set, citations) can point at it.

### The index

48. As a user, I want the index kept in a hidden `.index` folder inside the Knowledge Base, so that it stays out of my way.
49. As a user, I want refreshing the index to redo only the files that are new, changed or deleted, so that refreshing a large Knowledge Base is fast.
50. As a user, I want my hand edits picked up on the next refresh, so that what search sees matches my files.
51. As a user, I want a file I deleted by hand to have its Chunks removed on the next refresh, so that search never returns something I removed.
52. As a user, I want to delete the whole index and have it rebuilt from my files, so that a broken index is never a disaster.
53. As a user, I want the index fully rebuilt when the chunk rules or the embedding model change, so that old and new Chunks are never mixed.
54. As a user, I want the old index to keep working until a rebuilt one is complete, so that an interrupted rebuild never leaves me with nothing.
55. As a user, I want a file I broke by hand (for example a damaged header) skipped with a warning and never deleted or rewritten, so that my mistakes never cost me data.
56. As a user, I want Markdown files in the folder that are not Conversations (my own Obsidian notes) left alone, so that I can keep other notes in the same folder.

### Status and running locally

57. As a user, I want a status command that shows how many Conversations per Platform, how many Chunks, and when the index was last refreshed, so that I can check everything is healthy.
58. As a user, I want everything (saving, chunking, embedding) to run on my own computer by default, so that my chats never leave it.
59. As a user, I want the embedding model downloaded once and reused, so that later runs work offline.

## Implementation Decisions

### Project skeleton

- The local program is a Python package (Python 3.12) in its own folder in the repo, separate from the throwaway prototype and the future TypeScript extension. Dependencies and the virtual environment are managed with `uv`; tests run with `pytest`.
- One run command: `uv run memoryforall <command>`. Commands in this spec: `import <folder>`, `reindex`, `status`. The command line is a thin wrapper over the Knowledge Base module.
- Embeddings use `fastembed` with `BAAI/bge-small-en-v1.5` (local, 384 dimensions, 512-token limit). Switching models and hosted Mode belong to spec 2.
- Settings: the Knowledge Base folder path is stored in a small settings file in the user's config directory. A command-line flag overrides it, so tests and one-off runs can point elsewhere. The default suggested path is a folder in the user's Documents. The author's own path, `...\personal\knowledge base`, is set on first run, not hard-coded.
- The real Knowledge Base folder must not be inside the repository. Tests always use temporary folders.

### Modules

1. **Knowledge Base** (main seam): owns the folder.
   - `save(conversation) -> result`. Result is one of `created`, `updated`, `renamed+updated`, `unchanged`.
   - `mark_gone(platform, chat_id, noticed_at)`.
   - `mark_present(platform, chat_id)`.
   - `conversations()`: read every Conversation back from its file, with notes.
   - `refresh_index() -> summary`: counts of files added, changed, removed and skipped.
   - `chunks()`: every Chunk with its labels and vector.
   - Constructed with a folder path and an embedder.
2. **Conversation file format**: turns a Conversation (plus kept notes) into Markdown, and parses a file back. Lives inside the Knowledge Base and is not a public seam. It must round-trip: write, then read back, gives the same Conversation and notes.
3. **Chunker** (second seam): a pure function `(conversation, notes, embedder) -> list of Chunks`. It applies the rules below. No files, no index.
4. **Index store**: one SQLite file in the hidden `.index` folder. It is used only by the Knowledge Base module.
5. **Embedder interface**: `name`, `dimension`, `embed(list of texts) -> list of unit-length vectors`. The real version wraps fastembed; tests use a deterministic fake.
6. **Command line**: parses arguments, loads settings, calls the Knowledge Base, prints summaries.

### The Platform-neutral Conversation (input contract)

Import reads it from JSON files. Sync (spec 5) will send exactly this shape. Validated at the boundary, and invalid input is rejected with a reason.

```
Conversation {
  platform: "chatgpt" | "claude"
  chat_id: string            # the Platform's own ID; non-empty
  title: string | null       # null -> "untitled"
  created: ISO 8601 datetime
  updated: ISO 8601 datetime
  messages: [ { sender: "user" | "assistant", time: ISO 8601 | null, text: string, attachments: [string] } ]
}
```

Messages are in display order and hold the active branch only. Messages whose text is empty and that have no attachments are dropped. All times are stored in UTC.

### File layout and format

- Path: `<platform>/<YYYY-MM of created>/<YYYY-MM-DD of created>-<title slug>-<chat_id>.md`.
- **Title slug:** remove characters Windows forbids (`<>:"/\|?*` and control characters), collapse spaces to `-`, trim dots and spaces, cap at 60 characters, and use "untitled" if empty.
- **Finding a file:** a Conversation's file is found by `<chat_id>.md` at the end of its name, searched within the Platform folder. If its computed path differs (title or date changed), the file is moved to the new path and then rewritten.
- **Writes are atomic:** write a temporary file in the same folder, then replace.
- **Front matter** is YAML, so Obsidian reads it: `platform`, `chat_id`, `title`, `created`, `updated`, `status` (`on platform` or `no longer on the Platform`), and `gone_since` (only when gone).
- **Message headings:** each message starts with `### User · <time>` or `### Assistant · <time>` (time omitted when unknown), and the text follows verbatim. Attachments follow the text as `attachment: <name> (not saved)` lines. Parsing recognises only headings in exactly this form.
- The machine-owned part ends at a `## My notes` heading. Everything from that heading down is kept byte-for-byte on rewrite. A new file ends with an empty `## My notes` section.
- **Save rule:** if a file exists and its `updated` is the same as or later than the incoming one, nothing changes. `mark_gone` and `mark_present` edit only the front matter and keep notes.
- Markdown files without the `platform` and `chat_id` front matter are not Conversations, and are ignored.

Example (shape only):

```
---
platform: claude
chat_id: 4f1c...
title: Career3 agent design
created: 2026-10-02T09:14:00Z
updated: 2026-11-18T21:40:00Z
status: on platform
---

### User · 2026-10-02T09:14:00Z
What should we call the agent?

### Assistant · 2026-10-02T09:14:20Z
...

## My notes
```

### Chunk rules (from ticket 03, prototype-tested)

- **Unit:** one user message plus every assistant message up to the next user message. Assistant messages before the first user message form their own unit, and so does a user message with no reply. Unit text is `User: <question>` then `Assistant: <answer>`.
- **Prefix:** every Chunk's text starts with `Chat: <title>` on its own line.
- **Size cap:** 1,800 characters for the entire Chunk text, prefix included. That is about 450 tokens, under the model's 512.
- **Splitting a unit** that would exceed the cap: each piece is `Chat: <title>`, then `User: <first 300 characters of the question>`, then `Assistant: <piece>`.
  - The answer is broken at blank lines first, then single line breaks (this keeps code and tables in whole lines), then sentence ends.
  - Pieces are packed greedily up to the cap.
  - A hard cut happens only when a single segment still exceeds the room left.
  - If the question alone exceeds the room, the question is split the same way, then each answer piece carries the 300-character heading.
- **Merging:** neighbouring units in the same Conversation are merged when the combined text stays within the cap and the cosine similarity of their vectors is above 0.72. Split pieces of one unit are never re-merged with each other. The 0.72 cutoff is a named constant, untuned (to be tuned against the Test Set in spec 4).
- **Vector:** each final Chunk is embedded from its full final text, prefix included.
- **Notes:** non-empty `## My notes` text becomes Chunks of kind `notes`, split by the same size rules with prefix `Chat: <title>` and heading `My notes:`. Notes are never merged with exchanges.
- **Chunk record:**
  - Stable ID: `<platform>:<chat_id>:<n>`, where n is its position in that Conversation.
  - Labels: kind (`exchange` or `notes`), Platform, chat ID, title, date (the time of the unit's question; for notes and units without a question time, the Conversation's `updated`), and the position.
  - Text and vector.
- A **rules version** constant is stored with the index. Changing any rule bumps it.

The prototype logic that encodes the split decision (trimmed; `prototype/pipeline.py`, before line-break splitting and the title prefix were added):

```
head = f"User: {question[:300]}"
if len(question) + len(answer) <= MAX: one piece
room = MAX - len(head) - overhead
for segment in split(answer, at paragraph | sentence end):
    while len(segment) > room: hard cut
    pack greedily into pieces up to room
each piece -> f"{head}\nAssistant: {piece}"
```

### Index

- **One SQLite file** with three tables:
  - `meta`: embedder name, dimension, rules version, last refreshed.
  - `files`: path relative to the Knowledge Base, fingerprint (content hash), chat ID.
  - `chunks`: ID, kind, Platform, chat ID, title, date, position, text, vector stored as bytes.
- **Refresh:** list Conversation files, then compare fingerprints with `files`. Re-chunk new and changed files, drop rows for removed files, and skip unparseable files with a warning (their old Chunks are kept).
- **Full rebuild:** if `meta` does not match the current embedder name, dimension or rules version, or the index is missing or unreadable, rebuild everything. A rebuild writes a new SQLite file beside the old one and swaps it in only when complete (ADR 0001).
- **Disposable:** nothing is stored only in the index. All of it can be recreated from the files.

## Testing Decisions

- A good test drives the public actions and checks what a user or a later spec would see: files on disk, their contents, and the Chunks returned. It does not check private helpers, SQL statements or internal data structures. A refactor that keeps behaviour must not break tests.
- **Seam 1, Knowledge Base:** tests use a temporary folder and the fake embedder. They cover:
  - save creates the path and name, re-save newer rewrites, re-save the same or older is unchanged, rename on title change, notes kept byte-for-byte across rewrites;
  - mark gone and present, atomic write (no partial file after a simulated failure), round-trip of tricky text (code fences, lines that look like headings but aren't in the exact form, emoji, Windows-forbidden title characters, very long titles, empty Conversation);
  - refresh picking up new, edited (including notes edits) and deleted files, broken files skipped and kept, non-Conversation Markdown ignored, full rebuild on rules-version or embedder change, and a deleted `.index` rebuilding to the same Chunks.
- **Seam 2, Chunker:** pure tests with the fake embedder. They cover:
  - the cap is never exceeded, including the prefix;
  - split order (paragraph, then line, then sentence, then hard cut), with every piece carrying the question heading and the title prefix;
  - multiple assistant replies kept in one unit, an unanswered question, assistant-before-user;
  - merge happens only above the cutoff and within the cap, never across Conversations, never notes with exchanges;
  - stable IDs and labels, and an oversized question.
- The **fake embedder** returns deterministic vectors (for example, derived from a hash of each text, or from a test-supplied table) so that tests can force "same subject" and "different subject".
- **One slow test**, marked so it can be skipped, uses the real bge-small model on a small fixture to confirm vectors are 384-dimensional and unit-length, and that chunking runs end to end.
- **Command line:** one smoke test runs `import` on a fixture folder into a temporary Knowledge Base, then `reindex` and `status`, checking exit codes and the summary counts.
- **Fixtures** are small synthetic Conversations written for the tests. Real chats (`prototype/data-real/`) are never used in committed tests.
- **Prior art:** none in the codebase yet. This spec sets the pattern. The prototype (`prototype/pipeline.py`, `chunkcompare.py`) shows the chunk behaviour to match, but it is not test code.

## Out of Scope

- Searching Chunks, keyword index, re-ordering, Match Score: specs 2 and 4.
- Switching embedding models in the background, hosted Mode, OpenAI embeddings: spec 2.
- Context Packs and the Current Decision rule: spec 3.
- Test Set and quality checks, including tuning the 0.72 merge cutoff: spec 4.
- Sync, Readers, the extension, the local network link and pairing key, and importing official Platform exports: specs 5 and 6.
- Claude organisation choice, and archived or project-linked chats (ticket 02): spec 5.
- Saving non-active branches and attachment files, deleting and forgetting chats, Gemini, packaging for other people.
- Watching the folder for changes automatically. Refresh runs when asked.

## Further Notes

- Chunk-rule evidence is thin: 5 questions on 7 real chats, "found" judged by a keyword in the top 3. The Test Set in spec 4 should re-check the 1,800 cap and the 0.72 cutoff.
- Splitting at line breaks before sentence ends is new relative to the prototype. The prototype flattened newlines, so it could not do this. It is meant to reduce the hard-cut damage to code and tables noted in ticket 03.
- Pasted files and image-only chats are untested. Image-only messages produce no text, so they are dropped unless they have attachment names.
- If wanted, `prototype/convert.py` can be changed (throwaway) to emit the Platform-neutral JSON from the downloaded real chats, so `import` can be tried on real data before Sync exists. Those files stay in the gitignored `prototype/data-real/`.
- Privacy: real Conversations live only in the Knowledge Base folder outside the repo, and nothing in this spec sends data off the computer.
