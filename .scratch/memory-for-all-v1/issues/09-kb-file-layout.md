# kb-file-layout

Type: grilling
Status: resolved
Blocked by: -

## Question

What is the Knowledge Base folder layout: names, one file per chat, how re-syncs and hand edits are handled, and how the rebuildable index relates to it?

## Answer

- **Location:** `C:\Users\abhij\Documents\main-folder\personal\knowledge base` (created; outside the repo, so chats cannot be committed by accident; path is a setting, note it contains a space). 
- **Layout:** one Markdown file per Conversation, grouped by Platform then month, e.g. `chatgpt/2026-11/2026-11-19-<title>-<chat id>.md`; the Platform's chat ID in the name keeps it stable when the title changes.
- **File contents:** a header (Platform, chat ID, title, created, updated, on-platform status) then messages in order with sender and time. Chunks are not stored as files; they are re-created from the files, taking their labels from the header.
- **Re-sync:** same ID, same file, rewritten when the Platform's update time is newer than the one in the header.
- **Deleted on the Platform:** the local file is never deleted; the header is marked "no longer on the Platform".
- **Your notes:** everything above a `## My notes` heading is machine-owned and rewritten by sync; the notes section is never touched. Edits to the messages themselves are not kept.
- **Index:** hidden `.index/` folder inside the Knowledge Base folder, safe to delete and rebuild (ADR 0001).
- **Branched chats:** v1 saves only the active branch; other branches are a later spec.
- **Attachments and images:** text only, with a line like `attachment: report.pdf (not saved)`.
