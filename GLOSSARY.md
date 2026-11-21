# Memory for All

A personal knowledge base that gathers a user's chats from many AI platforms, so relevant past context can be handed to any platform when the user continues their work.

## Language

**Platform**:
An AI chat service the user talks to, such as ChatGPT or Claude.
_Avoid_: Provider, vendor, AI app

**Conversation**:
One chat thread on a Platform, from the first message to the last.
_Avoid_: Chat history, session, thread

**Knowledge Base**:
The user's single, combined collection of all their Conversations from every Platform, kept as Markdown files in a local folder.
_Avoid_: Memory store, database, vault

**Sync**:
Automatically pulling the user's recent Conversations from a Platform into the Knowledge Base.
_Avoid_: Import, upload, scrape

**Reader**:
The small piece of the extension that knows how to read Conversations from one specific Platform, so a change on one Platform only affects its own Reader.
_Avoid_: Scraper, connector, adapter

**Chunk**:
A small piece of a Conversation that keeps a question with its answer and groups nearby messages on the same subject, labelled with its Platform and date.
_Avoid_: Snippet, segment, passage

**Request**:
What the user types to say which past context they want to carry into the current chat, about anything from any Conversation.
_Avoid_: Query, search, project

**Context Pack**:
The block put into a new chat on any Platform for a Request: a short summary, a list of key decisions and facts, and the original Chunks that back them, each marked with its source.
_Avoid_: Prompt, memory dump, summary

**Match Score**:
The percentage shown to the user telling how much of what their Request needs was found in the Knowledge Base, with any missing pieces named.
_Avoid_: Confidence, accuracy, similarity

**Current Decision**:
The user's most recent choice on a subject. The Context Pack leads with it and notes what it replaced and when, for example "changed from X to Y between January and March".
_Avoid_: Latest answer, final decision

**Mode**:
The user's choice of where the AI models run: hosted (using their own OpenAI or Claude key) or fully local (open-source models on their computer).
_Avoid_: Provider, backend

**Test Set**:
A fixed list of questions from the user's real Conversations, each with the right Chunks marked, used to measure quality after every change. It includes questions whose answer is not in the Knowledge Base.
_Avoid_: Benchmark, eval data
