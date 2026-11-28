# 05: Current Decision check

**What to build:** For questions where the user changed their mind, the program judges the Current Decision check itself, with no hand mark: the pack must lead a subject with the newest choice and list the replaced one under it. See the spec: `.scratch/quality/spec.md` (User Story 31; Checks: Current Decision).

**Blocked by:** 03 (Quality run end to end), spec 3 ticket 03 (`.scratch/context-pack/issues/03-current-decision-and-suggestions.md`)

**Status:** resolved

- [ ] A changed-mind question passes when some subject in `PackResult.decisions` has a leading quote containing the `current` phrase and a replaced quote containing the `replaced` phrase (normalised containment); pass = 100%
- [ ] The result shows in the review file's automatic line, in `quality run`'s printout and in `quality score`
- [ ] A changed-mind question that got "Nothing found" or a writing-model failure fails the check
- [ ] Tests with the scripted fake writer and a fixture with an older and a newer Chunk: newer leads with older replaced passes; phrases absent fails; reversed (old leading) fails
