# 05: Cancel, timeout and busy

**What to build:** While a pack is being written the user can press Cancel to give up on a Request they typed wrong. The panel gives up by itself after 2 minutes with "This took too long", so a stuck model never leaves it spinning, and a "pack already being written" answer is shown plainly. See the spec: `.scratch/extension/spec.md` (Implementation Decisions, "Side panel flow": states; stories 31 to 33).

**Blocked by:** 04 (Request to preview, with Copy)

**Status:** ready-for-agent

- [ ] A Cancel button while `working` returns to `ready`; an answer arriving after Cancel is ignored
- [ ] After `PACK_TIMEOUT_MS` (2 minutes, a constant) `working` returns to `ready` with "This took too long"; a late answer is ignored
- [ ] A `busy` answer shows "A pack is already being written"
- [ ] Vitest with the fake clock: Cancel then a late answer stays in `ready`; the 2-minute timeout shows its message; `busy` shows its message
