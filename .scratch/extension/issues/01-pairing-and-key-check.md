# 01: Pairing and the key check (program)

**What to build:** The user runs `memoryforall pair`, gets a short one-time code, and the program swaps it for a long secret key that only the paired extension holds. From then on the program refuses every request without that key, including spec 5's sync requests, so other extensions and local programs can't read or write the Knowledge Base. `serve` and `status` tell the user whether an extension is paired. See the spec: `.scratch/extension/spec.md` (Implementation Decisions, "Pairing (program side, seam B)"; stories 1 to 3, 5 to 8, 10, 11, 13 to 20).

**Blocked by:** Sync 03 (`.scratch/sync/issues/03-finish-and-sync-state.md`)

**Status:** ready-for-agent

- [ ] `memoryforall pair` makes an 8-character code from an alphabet without look-alike characters (using `secrets`), writes it with a 10-minute expiry and a wrong-try counter to a pairing file in the config directory, and prints it; a second `pair` overwrites the file; works while `serve` runs in another process
- [ ] `POST /pair` `{code}`: a matching, unexpired code generates a 32-byte random URL-safe key, saves it to a key file in the config directory (user-only permissions where the OS supports them), deletes the pairing file and returns `{key}`; any earlier key is replaced
- [ ] Wrong code adds one to the counter; at 5 wrong tries the pairing file is deleted; answers are `paired`, `wrong_code`, `expired_or_missing` (with "run `memoryforall pair`")
- [ ] Every endpoint except health and pair (needs, save, finish, sync state) requires `Authorization: Bearer <key>`, compared with `hmac.compare_digest`; a missing or wrong key gets 401 with kind `not_paired` (no key file) or `pairing_lost` (key exists, doesn't match)
- [ ] Spec 5's `chrome-extension://` Origin check runs first and stays; CORS preflight also allows the `Authorization` header
- [ ] `GET /health`: Origin-checked, no key; returns `{app: "memoryforall", version, paired}` where `paired` means a valid key was sent
- [ ] `serve` prints "Not paired yet: run `memoryforall pair`" when no key file exists; `status` prints `Extension: paired` / `Extension: not paired`; no command output or log line ever contains the key
- [ ] Shared JSON fixtures for the pair and health messages, alongside spec 5's handshake fixtures
- [ ] pytest through the real `serve` server in-process with the config directory in a temporary folder: code alphabet and single use; expired code, 5 wrong tries and a replaced code; re-pairing gives the old key `pairing_lost`; every keyed endpoint refuses missing and wrong keys; a non-extension Origin is refused before the key is looked at; preflight allows `Authorization`; health's `paired`; the `serve` notice and `status` line; the key never appears in output
