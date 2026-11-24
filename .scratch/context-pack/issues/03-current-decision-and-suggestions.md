# 03: Current Decision, In short, and suggested vs accepted

**What to build:** When the user changed their mind, the pack leads with the newest choice and notes what it replaced and when, for example `Changed from "<old>" [5] (2026-01-04)`. The program enforces this from each Chunk's date, whatever order the model gives. An **In short** section repeats the Current Decisions. An assistant's suggestion is shown as "<Platform> suggested" unless the user accepted it later in the same chat. See the spec: `.scratch/context-pack/spec.md` (Pipeline: Current Decision, Suggested vs accepted, Rendering).

**Blocked by:** 02 (Speaker labels and quote rules)

**Status:** ready-for-agent

- [ ] Within a subject, verified `quotes` and `replaces` are ordered by source Chunk date; the newest leads and each older one is shown as replaced with its date. Ties keep the model's order
- [ ] A subject with no `replaces` is a plain list of facts with no "changed from" note
- [ ] **In short:** lists the leading quote of each subject that has a replaced quote; if there is none, it shows the first subject's leading quote
- [ ] An assistant leading quote is labelled "**<Platform> suggested:**" unless `accepted_by` is verified, spoken by You, in the same Conversation, and later (Chunk position, then position in the text). If so, the suggestion is followed by the acceptance quote labelled **You:**
- [ ] Tests at the `pack` seam: newer quote leads even when the fake orders it last, and it appears in In short; several facts without `replaces` get no note; unaccepted suggestion is labelled "suggested"; a later same-chat acceptance counts; an acceptance from another Conversation, or earlier in the chat, does not
