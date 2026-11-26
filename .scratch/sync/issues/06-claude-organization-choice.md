# 06: Choosing the Claude organization

**What to build:** A user in more than one Claude organization picks which one to sync the first time, from a list of names, and can change it later in the extension's options. A user with one organization is never asked. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Claude organization"; stories 31 to 33).

**Blocked by:** 05 (Extension skeleton and a first Claude Sync, end to end)

**Status:** ready-for-agent

- [ ] With more than one organization, the popup lists them by name and Sync waits for a choice
- [ ] The choice is saved in extension storage and used by every later run
- [ ] An options page lets the user change it
- [ ] A saved organization that no longer exists asks again
- [ ] With one organization nothing is asked
- [ ] Vitest through `syncPlatform`: several organizations ask, one does not, the saved one is used, a vanished one asks again
