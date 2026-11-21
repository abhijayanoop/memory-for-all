# 02: Re-saving, renames, kept notes, gone and back

**What to build:** Saving a Conversation that already exists behaves like Sync will need. A newer update time rewrites the file. The same or an older time changes nothing. A title or date change moves the file without duplicating it. The user's `## My notes` section always survives. A chat can be marked "no longer on the Platform" and back again. Import reports what happened to each file. See the spec (File layout and format, save rule; user stories 20-33).

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] The Knowledge Base `save` returns `created`, `updated`, `renamed+updated` or `unchanged`
- [ ] Re-saving with a newer `updated` rewrites the file; the same or an older `updated` leaves the file byte-for-byte unchanged
- [ ] The existing file is found by its chat ID at the end of the name within the Platform folder; if the computed path differs (title or created date changed) it is moved, then rewritten, and only one file remains
- [ ] Everything from the `## My notes` heading down is kept byte-for-byte across rewrites, renames and status changes
- [ ] `mark_gone(platform, chat_id, noticed_at)` sets status `no longer on the Platform` and `gone_since`; `mark_present` sets it back and removes `gone_since`; only the front matter changes and the file is never deleted
- [ ] A simulated failure during a rewrite leaves the previous file intact
- [ ] `import` prints counts of new, updated, unchanged and rejected files
