# insert-text-into-chats

Type: research
Status: resolved
Blocked by: -

## Question

How can the extension put a Context Pack into ChatGPT and Claude: type into the box, or attach a Markdown file? What works today, what are the size limits, and how fragile is it?

## Answer

Findings in `research/07-insert-text-into-chats.md`. Both sites accept file uploads (Claude 500MB/file, 20 files per chat, verified; ChatGPT 512MB/file, secondary since OpenAI pages returned 403), but `.md` is not on Claude's supported list, only TXT, so save the pack as `.txt` or test `.md`. No official per-message character cap found; both sites turn long pastes into attachments. ChatGPT's box is ProseMirror: a synthetic paste event works (secondary). No claude.ai insertion code found, and programmatic file attach has no source. Fragility, most to least: file attach, text insert, copy to clipboard and let the user paste. Needs a live test on each site.
