# claude-org-and-edge-chats

Type: grilling
Status: resolved
Blocked by: -

## Question

Your Claude account has two organizations. How does the Claude Reader pick the right one? What happens with archived, branched and project-linked chats?

## Answer

Settled by grilling (2026-11-22).

- **Organization:** on the first Claude sync, if `/api/organizations` returns more than one, the extension lists them by name and the user picks one. The choice is saved and can be changed later. With one organization there is nothing to pick.
- **Archived chats** (both Platforms): synced like any other chat, and marked as archived in the chat's file.
- **Project chats** (both Platforms): synced, with the project name stored in the chat's file. The folder layout stays Platform/month. The project's own files and instructions are not synced.
- **Branched chats:** active branch only (already settled in ticket 09).
- **Chats deleted on the Platform:** the file stays in the Knowledge Base unchanged. Deleting and forgetting chats is not in v1.
