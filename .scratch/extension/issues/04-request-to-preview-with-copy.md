# 04: Request to preview, with Copy

**What to build:** In the side panel the user types a Request and presses Enter or "Get context", sees "Working… Ns" while the pack is written, then a preview: the Match Score line, notices, the exact pack text (read-only), its size against the limit, the sources and the time taken. "Copy" puts the exact pack on the clipboard, or shows it selected for Ctrl+C if the clipboard fails. "Nothing found" and errors are shown with no way to insert or copy an empty or partial pack. See the spec: `.scratch/extension/spec.md` (Implementation Decisions, "Side panel flow": working indicator, preview, Copy; stories 25, 26, 29, 30, 34 to 42, 51, 53, 55 to 58).

**Blocked by:** 02 (Pack endpoint), 03 (Side panel: connecting and pairing)

**Status:** ready-for-agent

- [ ] A Request box; Enter or "Get context" sends it; an empty Request is refused with no program call
- [ ] `ready` → `working`: "Working… Ns", updated each second from the clock, with "Get context" disabled
- [ ] `working` → `preview` showing, in order: Match Score text, notices, the pack text read-only and scrollable, `chars / limit` (for example "8,612 / 9,500 characters"), sources (title, Platform, date), time taken, Insert and Copy buttons (Insert wired in ticket 06)
- [ ] `nothing_found` shows only "Nothing found in your chats for this", with no Insert or Copy
- [ ] `error` shows the program's message and a "Try again" button that keeps the Request; no Insert or Copy
- [ ] Copy writes exactly the pack text; if the clipboard throws → `manual_copy`: the pack shown selected in a box with "Press Ctrl+C to copy"
- [ ] The Request, preview and state live only in the panel's memory
- [ ] Vitest with fakes: empty Request refused; elapsed seconds from the fake clock and Get context disabled; preview fields shown and pack text unchanged; copied text equals the pack and never contains the Match Score; `nothing_found` and each error kind have no Insert or Copy; a throwing clipboard → manual copy box
- [ ] The TypeScript fake program answers the shared pack fixtures exactly as the Python server does
