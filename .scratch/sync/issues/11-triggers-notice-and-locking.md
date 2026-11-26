# 11: Triggers, first-run notice and locking

**What to build:** Sync keeps the Knowledge Base current without the user having to remember. After the user accepts a one-time notice, opening a ChatGPT or Claude tab starts a Sync, at most once an hour per Platform. Only one Sync per Platform runs at a time across tabs, and the popup shows when each Platform last synced and what changed, or why nothing happened. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Sync run": Locking, Triggers; stories 2, 4 to 6, 8 to 10).

**Blocked by:** 05 (Extension skeleton and a first Claude Sync, end to end)

**Status:** ready-for-agent

- [ ] A one-time notice before the first Sync: it reads chats from the user's own logged-in tab, slowly, keeps everything local, and both Platforms' terms restrict automated access; automatic Sync stays off until it is accepted
- [ ] Opening a Platform tab starts a Sync at most once an hour per Platform, only after the notice is accepted and auto-sync is on
- [ ] An auto-sync on/off switch in options
- [ ] One run per Platform at a time across all tabs, held by the background worker
- [ ] "Open claude.ai to sync Claude" (or chatgpt.com) when no tab of that Platform is open
- [ ] "App not running, start it with `memoryforall serve`" when the program cannot be reached
- [ ] The popup shows each Platform's last good Sync and its new/updated/unchanged counts, from the program's state
- [ ] Vitest with the fake clock: no auto-sync before the notice; at most one auto-sync per hour; a second run of the same Platform is refused while one runs
