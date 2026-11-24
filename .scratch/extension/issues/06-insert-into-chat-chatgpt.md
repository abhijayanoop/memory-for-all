# 06: Insert into chat, with the ChatGPT inserter

**What to build:** From the preview the user presses "Insert into chat" and the pack goes into the open ChatGPT chat box after any draft they typed, with the cursor after it, and is never sent. The panel checks the box and says "Inserted", or explains that ChatGPT turned it into an attachment, or, if insertion failed, copies the pack and says to press Ctrl+V. On a tab that isn't ChatGPT or Claude, Insert is disabled with a reason. See the spec: `.scratch/extension/spec.md` (Implementation Decisions, "Side panel flow": Insert; "Platform inserters"; stories 43 to 50, 52, 60).

**Blocked by:** 04 (Request to preview, with Copy)

**Status:** ready-for-agent

- [ ] The Platform comes from the active tab's address (chatgpt.com → ChatGPT, claude.ai → Claude); any other address disables Insert with "Open a ChatGPT or Claude chat to insert", and Copy still works
- [ ] The panel sends the pack text to the tab's content script, which runs that Platform's inserter and returns `text`, `attachment` or `failed` with a reason
- [ ] `text` → `inserted` ("Inserted"); `attachment` → `attached` ("ChatGPT turned the pack into an attachment; the model still reads it", naming the Platform); `failed` → clipboard written → `copied` ("Couldn't insert automatically. The pack is copied: click in the chat box and press Ctrl+V (⌘V on Mac)"); a throwing clipboard → `manual_copy`
- [ ] Content scripts declared only for chatgpt.com and claude.ai, in the default isolated world; selectors and steps live only in each Platform's inserter
- [ ] ChatGPT inserter: find the ProseMirror composer; count attachment chips, focus, move to the end, add a blank line if there is a draft; dispatch a `paste` event with the pack as `text/plain`, falling back to `execCommand('insertText')` if the text didn't change; read back with polling up to 1 s (`text` if the box contains the pack's first line and last 40 characters, `attachment` if the chips grew by one, else `failed`); never click send or press Enter
- [ ] Vitest through `packFlow` with a fake inserter: each result gives its state and message; inserted or copied text equals the pack exactly; Platform picked from chatgpt.com vs claude.ai; a non-Platform tab disables Insert
- [ ] No automated inserter tests (settled in the spec)
- [ ] Manual live check on ChatGPT (listed in the PR): insert into an empty box and after a draft (draft kept); nothing is sent automatically
