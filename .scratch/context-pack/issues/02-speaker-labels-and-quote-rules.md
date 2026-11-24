# 02: Speaker labels and quote rules

**What to build:** Every quote in the pack says who said it (**You:**, **ChatGPT:** or **Claude:**), and the program, not the model, decides this. Quotes that could mislead are rejected: too short, spanning two messages, or found only in the "Chat:" title line. A quote found in several sources cites all of them. The user sees which quotes were dropped and why. See the spec: `.scratch/context-pack/spec.md` (Pipeline: Quote verification).

**Blocked by:** 01 (Pack end-to-end with the local writing model)

**Status:** ready-for-agent

- [ ] Chunk text is split into messages at lines starting `User: ` / `Assistant: `; a quote must lie inside one message, otherwise it is dropped with reason "spans two messages"
- [ ] `User:` lines and notes Chunks give **You**; `Assistant:` gives the Chunk's Platform (**ChatGPT** / **Claude**)
- [ ] A quote found only in the `Chat:` title line is dropped with reason "from the title line"
- [ ] A quote under 12 normalised characters is dropped with reason "too short"
- [ ] A quote held by several sources cites every one; the best-ranked source decides the speaker and date
- [ ] Each rendered quote carries its speaker label and date
- [ ] CLI prints dropped quotes with their reasons on stderr
- [ ] Tests at the `pack` seam: each drop reason; multi-source citation; notes labelled You; a wrong speaker implied by the fake makes no difference
