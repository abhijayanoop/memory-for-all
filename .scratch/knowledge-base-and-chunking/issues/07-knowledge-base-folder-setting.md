# 07: Knowledge Base folder setting

**What to build:** The user chooses where their Knowledge Base lives once, and every command uses it after that. The program creates the folder if needed. A command-line flag still overrides it for one-off runs and tests. See the spec (Project skeleton: settings; user stories 2-5).

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] The Knowledge Base path is stored in a small settings file in the user's config directory, and a command sets it
- [ ] Commands use the saved path when no `--kb` flag is given; the flag overrides it
- [ ] Running with no saved path and no flag gives a clear message suggesting a default folder in the user's Documents
- [ ] The folder is created on first use; paths containing spaces work
- [ ] Tests use a temporary config directory and never touch the real one
