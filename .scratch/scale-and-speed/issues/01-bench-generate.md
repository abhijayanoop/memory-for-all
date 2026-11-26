# 01: Bench: generate changed copies of real Conversations

**What to build:** The user makes a large Knowledge Base of generated Conversations with one command, so speed can be measured at sizes their real history hasn't reached. Copies are made from their real Conversations with changes, saved through the same save action Sync uses, repeatable from a seed, and never written inside the real Knowledge Base or the repo. See the spec: `.scratch/scale-and-speed/spec.md` (Implementation Decisions, "Bench module": `generate`, "Command line"; stories 1 to 7).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `generate(source, dest, count, seed) -> counts` reads Conversations from the source Knowledge Base and saves `count` changed copies into the destination through the existing `save` action
- [ ] Each copy gets a new chat id from the seed and copy number, a title with a short suffix, created and updated dates shifted so copies spread over several years of month folders, and a seeded light rewording (swapping or dropping a few words, dropping or repeating a message)
- [ ] A destination that already holds generated Conversations gets new copies added after them, never overwritten
- [ ] A destination inside the source folder, or inside a folder holding a `.git` folder, is refused with a clear message
- [ ] Returns counts saved and the save rate (Conversations per second)
- [ ] `bench generate --from <kb> --to <folder> --count N [--seed S]` runs it, prints progress and the counts
- [ ] Tests from a small fixture Knowledge Base with the fake embedder: the requested count is saved; every file parses; chat ids are distinct from the source and each other; dates spread across months; text differs from the source; the same seed gives identical output; a second run adds; both refusals
- [ ] Command-line smoke test (config directory in a temporary folder, as in the existing mode tests): `bench generate` makes the files and prints counts
