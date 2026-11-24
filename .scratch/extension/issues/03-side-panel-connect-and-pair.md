# 03: Side panel: connecting and pairing

**What to build:** The user opens the extension's side panel next to a ChatGPT or Claude chat. It tells them if the program isn't running (with a Try again button), asks for the pairing code the first time, says "Paired" or explains a wrong or expired code, and tells them when pairing was lost. Sync now uses the same pairing. See the spec: `.scratch/extension/spec.md` (Implementation Decisions, "Two parts, one contract", "Side panel flow": states; stories 4, 9, 12, 20 to 24, 28).

**Blocked by:** 01 (Pairing and the key check), Sync 05 (`.scratch/sync/issues/05-extension-and-first-claude-sync.md`)

**Status:** ready-for-agent

- [ ] A side panel page that opens from the toolbar icon or the popup on chatgpt.com and claude.ai tabs and stays open while the user clicks in the chat
- [ ] One action `packFlow(deps)` with `deps = {program, inserter, clipboard, clock, activeTab}`, starting with these states: `checking` → `not_running` | `not_paired` | `pairing_lost` | `ready`
- [ ] `not_running` (connection fails): "App not running. Start it with `memoryforall serve`" and a Try again button
- [ ] `not_paired`: a pairing box; a correct code stores the key in extension storage and shows "Paired"; `wrong_code` and `expired_or_missing` show their messages
- [ ] `pairing_lost`: "Pairing lost: run `memoryforall pair` and enter the new code"
- [ ] A pairing check shared by the popup, options page and side panel; spec 5's sync requests (needs, save, finish, sync state) now send the key, and a 401 anywhere moves to `pairing_lost`
- [ ] Vitest with fakes: connection failure → not running, and Try again recovers; no key → pairing box; right code → ready; wrong and expired codes → their messages; 401 on sync → pairing lost
- [ ] The TypeScript fake program answers the shared pair and health fixtures exactly as the Python server does
- [ ] Manual check (listed in the PR): pair from scratch; open the panel with the program stopped, then started
