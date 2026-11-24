# 13: Report this

**What to build:** From the degraded banner, the user presses "Report this" and sees a short report of what broke: field names and error codes only, none of their chat text. They can read it, then copy it or save it as a file. Nothing is ever sent. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Banner, guided export, report": Report this; stories 50 to 53).

**Blocked by:** 09 (Loud failure: degraded, logged out, banner and badge)

**Status:** ready-for-agent

- [ ] A "Report this" button on the degraded banner
- [ ] The report is built in memory as JSON: Platform, failed step, request path with ids replaced by placeholders, HTTP status, missing fields, the response outline (keys and value types, arrays trimmed to their first element, no values), extension and Reader versions, time
- [ ] It is shown in a read-only box with Copy and Save buttons; nothing is sent anywhere
- [ ] Vitest: a degraded run's report names the step, status and missing fields, and contains no string value from the fixture's chat text, titles or ids
