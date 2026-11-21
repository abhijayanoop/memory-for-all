# 07: Putting a Context Pack into ChatGPT and Claude

Question: type/paste into the message box, or attach a Markdown file? What works, size limits, how rich inputs handle programmatic insertion, how fragile?

Tags: verified = fetched and read on the owning page this session; secondary = from a search-result summary or third-party page, not read in full; inferred = my reasoning.
Limitation: OpenAI help pages returned HTTP 403 to the fetcher, so ChatGPT limits are secondary (search snippets of the official page).

## 1. File attach: size limits

- Claude chat uploads: 500MB per file, up to 20 files per chat. Project files: 30MB per file. [verified] https://support.claude.com/en/articles/8241126-uploading-files-to-claude
  - Older snapshots of the same article said 30MB for chat; search results show both. Either is far above any Context Pack. [secondary]
- Claude supported types: TXT listed; Markdown (.md) is NOT listed on that page. [verified, same URL]. Inferred: save the pack as .txt (or test .md) to be safe.
- Claude: extracted file content still counts toward the context window ("additional token limits may apply"). [verified, same URL]
- ChatGPT: 512MB hard cap per file; text/document files capped at 2M tokens per file (spreadsheets exempt); images 20MB; spreadsheets ~50MB. [secondary] https://help.openai.com/en/articles/8555545-file-uploads-faq
- ChatGPT: 80 files per 3 hours; free users 3 uploads per day; limits may drop at peak; storage 25GB per user. [secondary, same URL via search summary]. Inferred: one pack = one file per new chat is well inside these.

## 2. Message-box text: limits

- No official published per-message character limit found for either site on the pages read. Claude's upload article states none. [verified for Claude article; not found for ChatGPT]
- Both sites turn long pasted text into an attachment ("pasted.txt" in ChatGPT; "pasted text" in Claude). Reported Claude threshold varies from ~3.9k to ~20k characters in informal tests; no official number. [secondary] https://scrapbox.io/evergreens/Claude%E3%81%AB%E9%95%B7%E6%96%87%E3%82%92%E8%B2%BC%E3%82%8A%E4%BB%98%E3%81%91%E3%82%8B%E3%81%A8%E3%80%81pasted_text%E3%81%A8%E3%81%AA%E3%82%8B%E7%8F%BE%E8%B1%A1%E3%81%AE%E8%AA%BF%E6%9F%BB ; ChatGPT: https://community.openai.com/t/chatgpt-converts-pasted-text-to-file-attachment/1369430
- Open bug reports say a Claude auto-converted paste can reach the model empty (desktop/CLI contexts). [secondary] https://claudeissues.com/issue/77946-long-text-pasted-into-input-auto-converts-to-paste-attachment-with-no-content-on
- Inferred: a Context Pack of any real size will hit the auto-attachment path when pasted as a ClipboardEvent, so the "text vs file" choice may be made by the site, not us. Needs a live test per site.

## 3. How the rich inputs take programmatic insertion

- ChatGPT's composer is a ProseMirror contenteditable: `div#prompt-textarea.ProseMirror[contenteditable=true]`; send button `button#composer-submit-button`. [secondary] https://greasyfork.org/scripts/561517-chatgpt-message-queue/code (userscript source, read in full by fetcher)
- That userscript inserts by (1) clearing, (2) dispatching a synthetic `ClipboardEvent('paste')`, (3) falling back to `document.execCommand('insertText', false, text)`, then (4) dispatching `beforeinput` and `input` events; it confirms success by counting a `prosemirrorDispatchTransaction` event and then clicks the send button with synthetic mouse events. [secondary, same URL]
- Setting `.value`/`innerHTML` or plain `dispatchEvent` of input fails on ProseMirror; `execCommand('insertText')` works because it behaves like real typing. One author's single-site experience (Gumroad), explicitly unverified beyond that. [secondary] https://dev.to/vesper_finch/how-i-defeated-prosemirror-the-only-way-to-programmatically-insert-text-into-rich-text-editors-1208
- Some editors reject execCommand; a synthetic paste with a DataTransfer is the usual alternative. [secondary] https://groups.google.com/a/chromium.org/g/chromium-extensions/c/4U0Zcmf85ak
- Claude.ai's editor: no read source showing selectors or code. Open-source candidates to read next: https://github.com/morninj/precog (claude.js, 404 on my guessed raw URL, not read) and https://github.com/PromptEditor/browser-extension. [unverified]
- Extension mechanics: content scripts run in an isolated world by default; `world: "MAIN"` in the manifest `content_scripts` entry runs in the page's world, where the page's CSP applies. [verified for isolated world and `world` field; MAIN semantics partly inferred] https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts
  - Inferred: DOM events and execCommand from the isolated world are enough for the userscript pattern; reaching ProseMirror's own view object would need MAIN world.

## 4. Attaching a file programmatically

- No primary source found. Inferred two routes, both untested: (a) dispatch a `paste` event whose DataTransfer holds a `File`; (b) set `files` on the site's hidden `input[type=file]` via a DataTransfer and fire `change`. Both rely on the site's own handlers and are as fragile as (3).

## 5. Fragility ranking (all inferred from the above)

1. Insert text via paste event, fallback execCommand: moderate. Depends on the editor being ProseMirror-like and the selector `#prompt-textarea`; site can change either with any release. Mitigate: one small per-Platform inserter with a verify step (read text back) and a clipboard-copy fallback telling the user to press paste.
2. Attach file programmatically: higher. Relies on hidden input or drop/paste handlers and a type allowlist (.md not listed for Claude).
3. Clipboard-only fallback (extension writes the pack to the clipboard, user presses Ctrl+V): lowest fragility, one manual step; still subject to the auto-attachment conversion.

## Gaps

- Official OpenAI pages unreadable by the tool (403); ChatGPT numbers need a manual look.
- No code read for claude.ai insertion; no official message character cap for either site.
