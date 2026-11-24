# 03: finish and the sync state

**What to build:** When a Sync run ends, the program records how it went. It advances the "synced through" watermark only after a completed run, marks chats deleted on the Platform as gone (and returning ones as present) when the run saw the whole list, and records or clears a degraded state. The user sees each Platform's last good Sync or degraded reason in `memoryforall status`. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Handshake" item 3, the state endpoint, "Sync state", the `status` line; stories 8, 15, 27 to 29, 37, 41).

**Blocked by:** 02 (`memoryforall serve` with the needs and save handshake)

**Status:** ready-for-agent

- [ ] **finish**: `{platform, outcome: ok|degraded|interrupted|logged_out, reason?, watermark?, full_list?}` → the stored sync state
- [ ] `ok` with a watermark records it; no other outcome moves the watermark
- [ ] `full_list` marks every saved chat of that Platform not in the list as gone (noticed now), and every listed chat marked gone as present again; notes are kept
- [ ] `degraded` records the reason and when it started; a later `ok` clears it
- [ ] A read-only state endpoint returns per Platform: last good Sync, watermark, last counts, degraded reason and since when
- [ ] The state is a small JSON file in a hidden folder inside the Knowledge Base folder, separate from `.index/`; a missing or damaged file is treated as a first run, never a crash
- [ ] `status` prints one line per Platform: last good Sync, or `sync degraded since <date>: <reason>`
- [ ] pytest through the real server: gone then back again with notes kept, watermark only on ok, degraded set then cleared, missing or damaged state file, the `status` line; new handshake examples added to the shared fixtures
