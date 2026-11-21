# Markdown files are the source of truth; the search index is disposable

The Knowledge Base is a folder of Markdown files (Obsidian-compatible). The search index (embeddings and keyword index) is derived from those files and can be rebuilt at any time, for example when the user switches embedding model or edits a note by hand. We chose this over a database as the truth because the user owns and can read, edit and back up their data, and nothing is locked into an index format.

## Consequences

- Rebuilding the index is a first-class operation, and the old index stays live until the new one is ready.
- Anything that must survive (Conversations, Chunk labels) lives in the files, never only in the index.
