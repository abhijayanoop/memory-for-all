# 04: Size limit

**What to build:** A pack is never more than 9,500 characters while any source still has full text, so it stays plain text when pasted into ChatGPT. When it is too long, the lowest-ranked sources are cut first, down to their title line marked "(text left out for length)", so every [n] still resolves. Key decisions are never cut. If the pack is still too long, the user is told. See the spec: `.scratch/context-pack/spec.md` (Pipeline: Size limit).

**Blocked by:** 01 (Pack end-to-end with the local writing model)

**Status:** ready-for-agent

- [ ] `PACK_LIMIT = 9500` named constant
- [ ] While over the limit, the lowest-ranked source with full text is cut to `[n] <title> (<Platform>, <date>) (text left out for length)`
- [ ] Header, Request, In short (once it exists) and Key decisions are never cut
- [ ] `PackResult.over_limit` is set when still over after every source is cut; CLI prints a notice on stderr
- [ ] Tests at the `pack` seam: long sources give a pack of at most 9,500 characters, cut lowest rank first, every [n] still resolves, key decisions intact; key decisions alone over the limit set `over_limit`
