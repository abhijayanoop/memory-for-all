# Spec 6: Extension

Status: ready-for-agent

Source decisions: `docs/spec-plan.md` (spec 6), `.scratch/memory-for-all-v1/issues/06-extension-local-link.md` (127.0.0.1 link, one-time pairing key, user starts the program, one request and one answer per pack, "working" indicator, Chrome-family), `07-insert-text-into-chats.md` and `research/07-insert-text-into-chats.md` (paste event then `execCommand` fallback, read-back check, clipboard fallback, fragility ranking), `04-context-pack-format.md` (9,500-character limit, Match Score only in the preview, the live paste test moved here). Builds on spec 3 (`.scratch/context-pack/spec.md`: `pack` and `PackResult`), spec 4 (`.scratch/quality/spec.md`: `match_score` on the result) and spec 5 (`.scratch/sync/spec.md`: the extension, `memoryforall serve`, the `chrome-extension://` Origin check). Vocabulary: `GLOSSARY.md` (Platform, Request, Context Pack, Match Score, Mode). ADR 0001 applies.

Seams settled with the user (2026-11-24): one seam per language, as in spec 5. (A) TypeScript: one extension action `packFlow` with a fake program, fake inserter, fake clipboard and fake clock. (B) Python: the real `serve` HTTP server in-process. The per-Platform inserters are checked only by the manual live check and a read-back check at runtime. The Request box and the preview live in Chrome's side panel.

## Problem Statement

Sync fills my Knowledge Base and `pack` can write a Context Pack, but only from the command line. When I'm in the middle of a ChatGPT or Claude chat and want my past context, I have to switch to a terminal, type the Request, wait, copy the output and paste it back into the chat box. That's too many steps to do it every time, so I won't.

The local program is also reachable by anything on my computer. Spec 5 only checks that a request comes from some browser extension. Any other extension, or any local program that fakes the header, could read my Context Packs (and through them my chats) or write Conversations into my Knowledge Base.

Putting text into ChatGPT's and Claude's chat boxes from code is fragile. Their editors ignore ordinary value changes, they turn long pastes into attachments, and they can change their markup with any release. If insertion silently fails, I get an empty box and no idea why.

## Solution

The Chrome extension gets a **side panel** that opens next to the chat. I type a Request and press "Get context". The panel shows a **working** indicator with the seconds elapsed while the program writes the pack. Then it shows a **preview**: the Match Score line ("60%: missing the hosting choice"), the exact pack text, its size against the 9,500-character limit, the sources (chat title, Platform, date) and any notices. From the preview I press **Insert into chat** or **Copy**.

**Insert into chat** puts the pack into the open ChatGPT or Claude chat box after any draft I already typed. It never presses send. The extension reads the box back to check it worked. If it didn't, it copies the pack to the clipboard and tells me to press Ctrl+V. If the site turned the pack into an attachment, the panel tells me that's normal.

The program and the extension are **paired** once. I run `memoryforall pair`, which prints a short one-time code, and type it into the extension. The program swaps the code for a long secret key that the extension keeps. From then on the program refuses every request without that key, including spec 5's sync requests. If the program isn't running, the extension says "App not running. Start it with `memoryforall serve`".

## User Stories

### Pairing

1. As a user, I want to pair the extension with the program once, so that only my extension can talk to my Knowledge Base.
2. As a user, I want `memoryforall pair` to print a short one-time code, so that pairing needs no copying of long secrets.
3. As a user, I want the code to be easy to type (no look-alike characters such as 0/O or 1/l), so that I get it right first time.
4. As a user, I want the extension to ask for the code the first time I use it, so that I know pairing is the first step.
5. As a user, I want the code to work once and expire after 10 minutes, so that an old code lying in my terminal can't be used later.
6. As a user, I want the code cancelled after 5 wrong tries, so that nobody can guess it.
7. As a user, I want running `memoryforall pair` again to replace any unused code, so that only the newest code works.
8. As a user, I want pairing to work while `memoryforall serve` is already running in another terminal, so that I don't have to restart it.
9. As a user, I want the extension to show "Paired" after a correct code and a clear message after a wrong or expired one, so that I know where I stand.
10. As a user, I want the secret key never printed by any command, so that it can't leak from my terminal history.
11. As a user, I want pairing again to replace the old key, so that I can recover if the extension was reinstalled or the key leaked.
12. As a user, I want an extension using a replaced key to say "Pairing lost: run `memoryforall pair` and enter the new code", so that I know how to fix it.
13. As a user, I want `memoryforall serve` to print "Not paired yet: run `memoryforall pair`" when no key exists, so that I'm told at start-up.
14. As a user, I want `memoryforall status` to show whether an extension is paired, so that I can check from the command line.

### Keeping the local link safe

15. As a user, I want the program to refuse every request without the right key (sync, sync state and packs), so that other extensions and local programs can't read or write my Knowledge Base.
16. As a user, I want spec 5's check that requests come from a `chrome-extension://` origin kept as well, so that ordinary websites are still refused before the key is even looked at.
17. As a user, I want the program to keep listening only on 127.0.0.1, so that other machines can't reach it.
18. As a user, I want the key compared in a way that leaks nothing through timing, so that it can't be guessed bit by bit.
19. As a user, I want the key file readable only by my own account where the system allows it, so that other users on the computer can't read it.
20. As a user, I want Sync to use the same pairing, so that I pair once for everything.

### App not running

21. As a user, I want the extension to say "App not running. Start it with `memoryforall serve`" when it can't reach the program, so that I know what to do.
22. As a user, I want a "Try again" button next to that message, so that I can continue once I've started it.
23. As a user, I want the extension to tell "not running", "not paired" and "pairing lost" apart, so that each message gives the right fix.

### Asking for a Context Pack

24. As a user, I want a side panel I can open next to my ChatGPT or Claude chat, so that I can ask for context without leaving the chat.
25. As a user, I want to type my Request in the side panel and press Enter or "Get context", so that asking is quick.
26. As a user, I want an empty Request refused in the panel, so that I don't wait for nothing.
27. As a user, I want the pack written by the program with my saved pack-writing Mode (spec 2), so that the extension adds no new settings for where models run.
28. As a user, I want the panel to stay open while I click in the chat, so that I can read the chat while the pack is being written.

### Working indicator

29. As a user, I want a "Working…" indicator with the seconds elapsed while the pack is being written, so that I know it hasn't frozen during a wait of up to 30 seconds.
30. As a user, I want the "Get context" button disabled while a pack is being written, so that I don't start two by accident.
31. As a user, I want a Cancel button while working, so that I can give up on a Request I typed wrong.
32. As a user, I want the extension to give up after 2 minutes with "This took too long", so that a stuck model never leaves the indicator spinning forever.
33. As a user, I want the program to answer "a pack is already being written" if a second pack request arrives while one is running, so that two local model runs never compete and both get slow.

### Preview

34. As a user, I want to see the Match Score line (for example "60%: missing the hosting choice", or "100%") at the top of the preview, so that I know how much my chats covered before I use the pack.
35. As a user, I want to see the exact pack text that will be inserted, so that nothing reaches the chat that I didn't see.
36. As a user, I want the pack text shown read-only, so that what I insert is always what the program checked (editing comes later).
37. As a user, I want the pack's size shown against the limit (for example "8,612 / 9,500 characters"), so that I know if it may become an attachment.
38. As a user, I want the sources listed with chat title, Platform and date, so that I can see where the context came from at a glance.
39. As a user, I want the notices from the program (re-embed pending, keyword-only search, still over the limit) shown in the preview, so that I know when the sources may be weaker.
40. As a user, I want "Nothing found in your chats for this" shown with no Insert or Copy buttons, so that I can't insert an empty pack.
41. As a user, I want the Match Score shown only in the preview and never in the inserted text, so that the new chat's model isn't given a number about my search.
42. As a user, I want the time the pack took shown, so that I can see whether the speed budget holds.

### Inserting into the chat

43. As a user, I want an "Insert into chat" button that puts the pack into the chat box of the tab I'm looking at, so that I don't have to copy and paste.
44. As a user, I want any draft I already typed kept, with the pack added after it on a new paragraph, so that I never lose what I was writing.
45. As a user, I want the message never sent automatically, so that I can add my question and decide when to send.
46. As a user, I want the chat box focused with the cursor after the pack, so that I can type my question straight away.
47. As a user, I want the extension to check the chat box after inserting, so that a silent failure is caught.
48. As a user, I want the panel to say "Inserted" when the pack is in the box as text, so that I know it worked.
49. As a user, I want the panel to say "ChatGPT turned the pack into an attachment; the model still reads it" (or Claude) when the site did that, so that I'm not worried by the attachment.
50. As a user, when insertion fails, I want the pack copied to my clipboard and the message "Couldn't insert automatically. The pack is copied: click in the chat box and press Ctrl+V (⌘V on Mac)", so that I'm one key press from done.
51. As a user, when even the clipboard write fails, I want the pack shown selected in a box with "Press Ctrl+C to copy", so that there's always a way to get it out.
52. As a user, I want "Insert into chat" disabled with "Open a ChatGPT or Claude chat to insert" when the active tab isn't one, so that I know why it can't insert.
53. As a user, I want a "Copy" button that always works, so that I can paste the pack anywhere, including other apps.
54. As a user, I want insertion into ChatGPT and Claude to work in Chrome, Edge and Brave, so that I can use the browser I already have.

### Failures from the program

55. As a user, I want a writing model failure shown with the program's fix-it message (for example "start Ollama, then run `ollama pull qwen3:4b-instruct`"), so that I can fix it myself.
56. As a user, I want a missing hosted key shown with the same message `mode pack` gives, so that the fix is the same everywhere.
57. As a user, I want an empty or missing index reported as "Your index is empty: run `memoryforall reindex`", so that I know why nothing came back.
58. As a user, I want no partial or fallback pack offered after an error, so that a failure is never mistaken for a real pack (spec 3's rule).

### Developer

59. As a developer, I want the whole side-panel flow testable through one action with a fake program, a fake inserter, a fake clipboard and a fake clock, so that working, preview, insert, fallback, timeout and errors are tested in milliseconds without a browser.
60. As a developer, I want each Platform's chat-box selectors and insertion steps kept in that Platform's own inserter, so that a site change touches one small file.
61. As a developer, I want the pairing and pack messages defined once as shared fixtures used by both the TypeScript and Python tests, so that the two sides can't drift apart.
62. As a developer, I want the pack endpoint to call spec 3's `pack` action unchanged, so that the command line and the extension write the same pack.
63. As a developer, I want the live paste test's results recorded in the insertion research doc, so that the next person knows what each site does with a ~8,600-character paste.
64. As a developer of spec 7, I want the pack endpoint to return the pack's `seconds`, so that the extension path can be timed like the command line.

## Implementation Decisions

### Two parts, one contract (as in spec 5)

- **Extension (TypeScript, Manifest V3, Chrome-family):** spec 5's extension folder gains:
  - a side panel page (pairing box, Request box, working indicator, preview);
  - one content-script inserter per Platform;
  - a pairing check shared by the popup, the options page and the side panel.
  - The side panel opens from the toolbar icon or the popup, on chatgpt.com and claude.ai tabs. It makes the pack request itself, so closing the panel abandons the request.
- **Program (Python):** spec 5's `serve` gains pairing, the key check, a health endpoint and a pack endpoint. There is a new `pair` command, and `status` gains a pairing line.
- **Contract:** the pair, health and pack messages, kept as shared JSON fixtures (as spec 5 does for the handshake).

### Pairing (program side, seam B)

- **`memoryforall pair`:**
  - makes an 8-character code from an alphabet without look-alike characters, using the `secrets` module;
  - writes it to a pairing file in the config directory with its expiry (10 minutes) and a wrong-try counter, then prints it;
  - a second `pair` overwrites the file.
  - Using a file means it works while `serve` runs in another process, with no talking between processes.
- **`POST /pair`:**
  - in `{code}`; out `{key}`.
  - On a match that hasn't expired: generate a 32-byte random key (URL-safe text), save it to a key file in the config directory (user-only permissions where the OS supports them), delete the pairing file and return the key. Any earlier key is replaced.
  - On a wrong code: add one to the counter. At 5 wrong tries, delete the file.
  - Answers are `paired`, `wrong_code`, `expired_or_missing` (with "run `memoryforall pair`").
  - Only one paired extension at a time.
- **Key check:**
  - Every endpoint except health and pair requires `Authorization: Bearer <key>`. This covers spec 5's needs, save, finish and sync state.
  - The comparison uses `hmac.compare_digest`.
  - A missing or wrong key gets 401 with kind `not_paired` (no key file exists) or `pairing_lost` (a key exists but doesn't match).
  - Spec 5's `chrome-extension://` Origin check runs first and stays. CORS preflight also allows the `Authorization` header.
- **`GET /health`:** Origin-checked, no key. Returns `{app: "memoryforall", version, paired}`, where `paired` means a valid key was sent with the request. The extension uses it to tell "not running" (connection fails) from "not paired" from "pairing lost" from "ok".
- `serve` prints the not-paired notice at start when there's no key file. `status` adds `Extension: paired` / `Extension: not paired`. No command ever prints the key.

### Pack endpoint (program side, seam B)

- **`POST /pack`:**
  - in `{request}`.
  - It builds the Knowledge Base and the writer exactly as the `pack` command does (spec 3: settings, pack-writing Mode, hosted-key check before any work) and calls `pack(kb, request, writer)` unchanged.
- **Answer** (JSON form of `PackResult`, only what the preview needs):
  - `text`, `nothing_found`;
  - `match_score` (`percent`, `missing`, `text`);
  - `sources` (`n`, `title`, `platform`, `date`);
  - `notices` (re-embed pending, keyword-only, over limit), each a plain sentence;
  - `chars`, `limit` (9,500), `seconds`.
  - Chunk texts aren't repeated: they're already in `text`.
- **Errors:** one shape, `{error: {kind, message}}`, where `message` is the same fix-it text the command line prints:
  - `empty_request` 400;
  - `busy` 409 ("a pack is already being written");
  - `index_empty` 409;
  - `hosted_key_missing` 400;
  - `writer_failed` 502.
- **One pack at a time:** a non-blocking lock around the pack call. A second request gets `busy` and doesn't wait. If the extension cancels or times out, the running pack finishes and its result is thrown away. The lock is released when the pack finishes.
- The threaded server from spec 5 keeps health and sync answering while a pack runs.

### Side panel flow (extension side, seam A)

One action: `packFlow(deps)`, a small state machine driven by user events. `deps = {program, inserter, clipboard, clock, activeTab}`. Everything below sits behind it.

- **States:** `checking` → `not_running` | `not_paired` | `pairing_lost` | `ready` → `working` → `preview` | `nothing_found` | `error` → (insert) `inserted` | `attached` | `copied` | `manual_copy`. From `working`, Cancel or the 2-minute timeout (`PACK_TIMEOUT_MS`, a constant) returns to `ready` (with "This took too long" on timeout). A 401 at any point moves to `pairing_lost`, and a connection failure moves to `not_running`.
- **Working indicator:** while `working`, the panel shows "Working… Ns", updated each second from the clock, and disables "Get context".
- **Preview:** shows, in this order:
  - the Match Score text;
  - notices;
  - the pack text, read-only and scrollable;
  - `chars / limit`;
  - sources;
  - time taken;
  - Insert and Copy buttons.
  - `nothing_found` shows only "Nothing found in your chats for this". An error shows its message and a "Try again" button that keeps the Request.
- **Insert:**
  - The Platform comes from the active tab's address (chatgpt.com → ChatGPT, claude.ai → Claude). Any other address disables Insert with the message from story 52.
  - The panel sends the pack text to that tab's content script, which runs the Platform's inserter. The inserter returns `text`, `attachment` or `failed` with a reason (for example "chat box not found").
  - `failed` writes the pack to the clipboard (→ `copied`). If that throws, it goes to → `manual_copy`, which shows the pack selected in a box.
  - Copy uses the same clipboard path.
- The Request, the preview and the state live only in the panel's memory. Nothing is stored.

### Platform inserters (content scripts)

Each inserter is one small module per Platform. Selectors and steps live only there, like spec 5's Readers. Steps, from the research:

1. **Find the composer.** ChatGPT: the ProseMirror box `#prompt-textarea`. Claude: its contenteditable composer, with the selector settled during the live check and noted in the research doc.
2. **Prepare.** Count the existing attachment chips, focus the box, move the cursor to the end, and add a blank line if the box already has text.
3. **Insert.** Dispatch a synthetic `paste` event whose `DataTransfer` holds the pack as `text/plain`. If the box text didn't change, fall back to `document.execCommand('insertText', false, pack)`.
4. **Read back.**
   - If the box text now contains the pack's first line and its last 40 characters, the result is `text`.
   - Otherwise, if the attachment chips grew by one, the result is `attachment`.
   - Otherwise the result is `failed`.
   - A short wait (up to 1 s, polling) allows the site to finish processing.
5. **Never send.** Don't click the send button or press Enter.

- Content scripts run in the default isolated world: DOM events and `execCommand` are enough, per the research. They're declared only for chatgpt.com and claude.ai.
- File attach is not used, because the research ranks it the most fragile.

### Unchanged

- `pack`, `PackResult`, the Match Score, the pack format and the 9,500-character limit (specs 3 and 4).
- Spec 5's sync handshake messages, except that they now carry the key.

## Testing Decisions

- **Good tests** check behaviour at the two seams only:
  - what the panel shows and does, given program answers and inserter results;
  - what the server answers, given requests.
  - They don't test inserter internals, private helpers, DOM layout or prompt wording.
- **Seam A (TypeScript, Vitest):** `packFlow` with:
  - a fake program (scripted answers for health, pair and pack, including delays, 401s and connection failures);
  - a fake inserter returning `text`, `attachment` or `failed`;
  - a fake clipboard that can throw;
  - a fake clock;
  - a fake active tab.

  Cases:
  - connection failure → "App not running" with the `serve` command, and Try again recovers;
  - no key → pairing box; right code → paired and ready; wrong and expired codes → their messages;
  - 401 on pack or sync → pairing lost;
  - empty Request refused, with no program call;
  - working shows elapsed seconds from the fake clock, and Get context is disabled;
  - Cancel returns to ready and a late answer is ignored;
  - after 2 minutes, "This took too long";
  - `busy` → its message;
  - preview shows the Match Score text, the notices, the pack text unchanged, `chars / limit`, sources and seconds;
  - the inserted or copied text equals the pack text exactly and never contains the Match Score;
  - `nothing_found` → no Insert or Copy;
  - each program error kind shows its message, with no Insert or Copy;
  - insert result `text` → "Inserted"; `attachment` → the attachment note naming the Platform; `failed` → clipboard written and the Ctrl+V message; `failed` with a throwing clipboard → manual copy box;
  - a non-Platform active tab → Insert disabled and Copy works;
  - Platform picked from chatgpt.com vs claude.ai addresses.
- **Seam B (Python, pytest):** the real `serve` server on a free port in-process (as in spec 5), with the config directory in a temporary folder, the fake embedder and re-ranker from `tests/conftest.py`, and spec 3's scripted fake writer injected.
  - Pairing:
    - `pair` prints a code with no look-alike characters, and the code works once;
    - an expired code (fake time or edited expiry), 5 wrong tries, and a second `pair` replacing the first each give the right answer;
    - pairing again replaces the key and the old key gets `pairing_lost`.
  - Key check:
    - every non-health, non-pair endpoint (needs, save, finish, sync state, pack) refuses a missing key (`not_paired`) and a wrong key (`pairing_lost`);
    - a non-extension Origin is refused before the key is looked at;
    - preflight allows `Authorization`;
    - health reports `paired` correctly.
  - Pack endpoint:
    - it returns the same pack text as calling `pack` directly with the same fakes;
    - `nothing_found`, Match Score, sources, notices, `chars` and `seconds` are present;
    - each error kind has its status and message;
    - a second request while the fake writer blocks gets `busy`;
    - the lock is released after a writer failure.
  - Printing:
    - `serve` prints the not-paired notice;
    - `status` prints the pairing line;
    - no command output or log line contains the key.
- **Contract:** the shared pair, health and pack fixtures are used by the TypeScript fake program and replayed against the Python server, asserting the same answers (spec 5's pattern).
- **Inserters:** no automated tests (settled with the user). The read-back check at runtime and the clipboard fallback are the safety net.
- **Manual live check** (not automated, listed in the PR, results recorded in `.scratch/memory-for-all-v1/research/07-insert-text-into-chats.md`). In Chrome, plus one of Edge or Brave:
  - pair from scratch;
  - get a pack with the program stopped, then started;
  - insert a ~8,600-character pack into an empty ChatGPT box and an empty Claude box, then type a question and send. Record whether each site kept it as text or made an attachment, and whether the answer used the pack correctly. This is the paste test moved here from ticket 04;
  - insert after an existing draft and check the draft is kept;
  - break a selector on purpose and check the clipboard fallback message;
  - check that nothing is ever sent automatically.
- **Prior art:**
  - spec 5's Vitest setup and `syncPlatform` fake-deps tests (fake fetch, fake program, fake clock);
  - spec 5's in-process `serve` tests and shared handshake fixtures;
  - spec 3's `pack` tests with the scripted fake writer;
  - `tests/test_modes.py` (command-line smoke tests, key-missing messages);
  - `tests/conftest.py` (fakes).

## Out of Scope

- Auto-starting the program at login, native messaging, and packaging for the Chrome Web Store.
- Attaching the pack as a file, and per-Platform size limits (one 9,500-character limit, spec 3).
- Sending the message automatically, or a button inside the Platform's page next to the chat box.
- Editing the pack before inserting, pack history, and saving packs to files.
- Streaming pack progress (the indicator shows elapsed time only, from one request and one answer).
- More than one paired extension at a time, and an `unpair` command (pairing again replaces the key).
- A "Report this" button for insertion failures (spec 5's report covers Sync only).
- Firefox, Safari, Gemini and other Platforms.
- Speed work on packs: spec 7.

## Further Notes

- **Depends on specs 3, 4 and 5 being built first:** `pack`, `match_score`, `serve`, the extension skeleton and its test runner. If spec 4 isn't in yet, the preview shows spec 3's needs coverage in place of the Match Score text.
- Ticket 06 said the pack request carries the target Platform. Spec 3 settled one limit and one format for both Platforms, so the program doesn't need it. The extension uses the Platform only to pick the inserter.
- The research could only confirm ChatGPT's insertion details from a third-party userscript, and found no source for claude.ai. The live check settles the Claude selector and whether the paste event or `execCommand` path works on each site. If neither works on a site, the clipboard fallback is what ships for that site, and no spec change is needed.
- The insertion research found an open bug report where Claude's auto-made paste attachment reached the model empty. The live check's "is the answer right" step is there to catch this. If it happens, record it and tell users in the attachment note.
- Pairing closes the gap spec 5's Further Notes left open: other local programs could call the link. After this spec, a caller needs both an extension Origin and the key.
