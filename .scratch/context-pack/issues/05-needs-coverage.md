# 05: Needs coverage

**What to build:** After a pack is written, the user sees which parts of their Request their chats cover and which are missing. A second model call splits the Request into 1 to 4 needs from the Request alone and says which verified quote covers each. The program counts a need as covered only if that quote is one it verified. This is printed after the pack, never inside it, and returned on the result for spec 4's Match Score. See the spec: `.scratch/context-pack/spec.md` (Pipeline: Call 2, needs; Modules 1 and 3).

**Blocked by:** 01 (Pack end-to-end with the local writing model)

**Status:** ready-for-agent

- [ ] Call 2 takes the Request alone plus the numbered verified quotes and returns needs with a covering quote number or none; there are exactly two model calls per pack
- [ ] `PackResult.needs`: each need with `covered` (program-confirmed) and its verifying quote
- [ ] Call 2 is not made when the result is `nothing_found`
- [ ] CLI prints the needs as covered / missing on stderr; the pack text has no needs and no Match Score
- [ ] Tests at the `pack` seam: a need covered by a verified quote is covered; a need the fake marks covered with an unknown or unverified quote is not; the fake writer gets exactly 2 calls on a normal pack
