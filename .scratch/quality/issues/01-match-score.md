# 01: Match Score on the pack result

**What to build:** Every Context Pack result tells the user how much of their Request their chats answered: needs covered ÷ total needs as a whole percentage, with the uncovered needs named, for example "60%: missing the hosting choice". The command line prints it on standard error after the pack; it is never inside the pack. See the spec: `.scratch/quality/spec.md` (Solution 1; Implementation Decisions, Modules 1).

**Blocked by:** spec 3 ticket 05 (`.scratch/context-pack/issues/05-needs-coverage.md`)

**Status:** resolved

- [ ] `PackResult` carries a Match Score: percentage (rounded to the nearest whole number) and the list of missing needs, plus its short text form (`"60%: missing X"`, `"100%"`, several missing needs joined with commas)
- [ ] Only program-verified coverage counts (spec 3's rule); a need the writer claims covered with an unverified quote is missing
- [ ] No Match Score when the result is `nothing_found`
- [ ] `pack` prints the Match Score line on standard error after the needs listing; the pack text on standard output never contains it
- [ ] Tests at the `pack` seam with the scripted fake writer: 2 of 3 needs covered gives 67% naming the missing need; all covered gives "100%"; unverified cover counts as missing; `nothing_found` has none; pack text has no Match Score
