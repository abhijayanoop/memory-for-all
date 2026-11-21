# chatgpt-sync-check

Type: task
Status: resolved
Blocked by: -

## Question

Run the ChatGPT probe (prototype/probe/chatgpt-probe.js) in the logged-in chatgpt.com console and record the real list/fetch response shapes, whether order=updated works, and the right API path. Update docs/research/chat-export-mechanisms.md.

## Answer

Live probe on the user's own chatgpt.com session (2026-11-20): the working base path is `/backend-api` (`/backend-api/conversations?offset=0&limit=5` returned 200). Session token from `/api/auth/session` worked. List items carry `id`, `title`, `create_time`, `update_time` (ISO strings), `is_archived`, `is_starred`, `snippet`, `current_node`, `gizmo_id` (projects). `order=updated` is accepted and gave the same order as the default, so the list is already newest-updated first: an incremental sync can stop at the first chat whose `update_time` is not newer than the saved one. Single chat at `/backend-api/conversation/{id}` returned `mapping` (tree, 11 nodes in the sample) and `current_node`. This account has only 6 chats (`total 6`), so speed and rate limits on a large history are still untested.
