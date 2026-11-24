# 02: `memoryforall serve` with the needs and save handshake

**What to build:** The user starts the program with `memoryforall serve`. It listens only on 127.0.0.1 and answers only browser-extension origins. Through it, an extension can ask which chats it needs and save a chat with the existing save rules. The handshake messages are defined once as shared JSON fixtures that both test suites use. See the spec: `.scratch/sync/spec.md` (Implementation Decisions, "Handshake" items 1 and 2, "The bare local link"; stories 13, 20, 54 to 57, 61, 62).

**Blocked by:** 01 (Archived and project marks on a Conversation)

**Status:** ready-for-agent

- [ ] `serve` binds 127.0.0.1 on a fixed default port (a setting, overridable by a flag) using the standard library's threaded HTTP server; no new dependency
- [ ] Requests whose `Origin` is not `chrome-extension://…` are refused; CORS preflight is answered for extension origins
- [ ] **needs**: `{platform, items: [{chat_id, updated, archived, project}]}` → `{needed: [chat_id]}`; a chat is needed when it has no file, the incoming `updated` is newer, or `archived`/`project` differ
- [ ] **save**: `{conversation}` → `{result: created|updated|renamed+updated|unchanged}`, or a rejection carrying the validation reason; it calls the existing save action
- [ ] Shared handshake fixtures (example requests and expected answers) live in one place outside both code trees
- [ ] pytest starts the real server in-process on a free port with the fake embedder: needs (new, newer, same, older, marks changed), save results and rejections, origin refusal, preflight, and the shared fixtures replayed with matching answers
