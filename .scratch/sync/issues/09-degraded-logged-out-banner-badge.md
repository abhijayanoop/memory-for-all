# 09: Loud failure: degraded, logged out, banner and badge

**What to build:** When a Platform's responses no longer look as expected, Sync stops that Platform instead of quietly skipping chats. The user sees a "sync degraded" banner (which Platform, since when, what went wrong in plain words) and a badge on the extension icon. A logged-out user is told to log in, not that Sync is broken. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Sync run": Errors; "Banner, guided export, report": degraded state; stories 34 to 41).

**Blocked by:** 05 (Extension skeleton and a first Claude Sync, end to end)

**Status:** ready-for-agent

- [ ] Every response is checked against the Reader's required fields; a missing field, an unexpected status (404, or 5xx after one retry) or a conversion error → `finish` with `degraded` and a plain reason naming the step and fields
- [ ] Unknown extra fields are ignored
- [ ] A failing chat stops the run; chats already saved stay saved
- [ ] 401/403 or a login page → `logged_out`, shown as "please log in to <Platform>", not degraded
- [ ] The popup banner and the icon badge are driven by the program's sync state, so they agree with `memoryforall status`; the next `ok` clears both
- [ ] Vitest through `syncPlatform`: a missing required field → degraded with the field named and earlier saves kept; 401 → logged_out; an extra field is ignored
