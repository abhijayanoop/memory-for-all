# 07: Claude inserter and the live paste test

**What to build:** "Insert into chat" also works on claude.ai, and both inserters are proven live in Chrome and one other Chrome-family browser with a full-size pack: the user knows whether each site keeps the pack as text or makes an attachment, and whether the model's answer actually used it. See the spec: `.scratch/extension/spec.md` (Implementation Decisions, "Platform inserters"; Testing Decisions, "Manual live check"; Further Notes; stories 54, 63).

**Blocked by:** 06 (Insert into chat, with the ChatGPT inserter)

**Status:** ready-for-agent

- [ ] Claude inserter with the same steps as ChatGPT's, its contenteditable composer selector settled during the live check
- [ ] Manual live check in Chrome plus Edge or Brave (listed in the PR):
  - insert a ~8,600-character pack into an empty ChatGPT box and an empty Claude box, type a question and send; record text vs attachment and whether the answer used the pack correctly (the paste test moved here from ticket 04)
  - insert after an existing draft on each site; the draft is kept
  - break a selector on purpose; the clipboard fallback message appears
  - nothing is ever sent automatically
- [ ] If neither paste nor `execCommand` works on a site, the clipboard fallback ships for that site and this is recorded
- [ ] If Claude's auto-made attachment reaches the model empty (the open bug report from the research), record it and mention it in the attachment note
- [ ] Results recorded in `.scratch/memory-for-all-v1/research/07-insert-text-into-chats.md`: per site and browser, the selector, which insert path worked, text vs attachment, and whether the answer used the pack
