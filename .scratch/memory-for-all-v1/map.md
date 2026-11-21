# Map: Memory for All, v1

## Destination

A build-ready v1 spec for Memory for All: every open design question settled, ready to hand to `/to-spec` and `/to-tickets`. No code is written on this map.

## Notes

- Use the Matt Pocock skills only. Ask questions in plain words, no jargon.
- Use the vocabulary in `GLOSSARY.md`; ADR `docs/adr/0001-markdown-source-of-truth.md` is settled.
- Starting point: `docs/research/chat-export-mechanisms.md` (export and sync research, with live Claude probe results) and the throwaway `prototype/`.
- Syncing from the logged-in tab is a user-triggered, throttled, local-only gray area; both platforms' terms forbid automated access.
- Settled earlier: one user first; ChatGPT and Claude in v1; Markdown Knowledge Base; hybrid search with re-ordering; Context Pack = summary + key decisions + source Chunks; Current Decision wins and notes what it replaced; hosted or local Mode per job; Python local program, TypeScript extension; Test Set with four checks; loud-failure banner, guided export fallback, "Report this" button, one Reader per Platform.

## Decisions so far

<!-- one line per closed ticket: [title](link): gist -->

- [chunk-rules](issues/03-chunk-rules.md): 1,800-character cap, split long answers at paragraph/sentence ends, merge small same-subject neighbours, prefix every Chunk with the chat title (fixed the one miss); tested on only 5 questions
- [extension-local-link](issues/06-extension-local-link.md): private local address with a one-time secret key; user starts the program; list-then-send sync; one request, one answer for packs; Chrome-family; sync only in an open tab
- [kb-file-layout](issues/09-kb-file-layout.md): one Markdown file per chat under Platform/month in a folder outside the repo; sync owns everything above "My notes"; index in .index/; text only, active branch only

- [chatgpt-sync-check](issues/01-chatgpt-sync-check.md): `/backend-api/conversations` works, newest-updated first, has update_time, so sync can stop early; large-history speed untested

- [insert-text-into-chats](issues/07-insert-text-into-chats.md): text insert is possible but fragile; files need .txt for Claude; fallback is copy-to-clipboard; live test needed
- [local-models](issues/08-local-models.md): keep bge-small + MiniLM re-ranker locally; 3-4B 4-bit model for summaries; speed unmeasured

## Not yet specified

- Gemini support
- Choosing the Current Decision when chats disagree in subtle ways
- Saving non-active chat branches and attachment files
- Deleting and forgetting chats (privacy)
- Packaging so other people can install it
- Telling the user when a Platform's sync is stale

## Out of scope

- More than one user
- The scheduled test-account check and the agent that drafts fixes when a site changes
- A hosted online version
