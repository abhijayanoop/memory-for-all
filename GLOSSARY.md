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

**API**:
In hosted Mode, which company's API (OpenAI or Claude) the user's own key is for, for example the one that writes Context Packs (`--api openai|claude`). Not a Platform: it is the model service the program calls, not a chat service the user talks to.
_Avoid_: Provider, vendor

**Test Set**:
A fixed list of questions from the user's real Conversations, each with the right Chunks marked, used to measure quality after every change. It includes questions whose answer is not in the Knowledge Base.
_Avoid_: Benchmark, eval data

**Hallucination**:
A Context Pack saying something the user's Conversations do not: a wrong fact, a wrong link between true facts (for example swapping which product is the guitar and which is the amp), or an assistant's suggestion shown as the user's decision. The target is zero.
_Avoid_: Error, inaccuracy

**Abstention**:
Saying "nothing found", or naming a need as missing, instead of answering. A correct Abstention is one where the answer really is not in the Knowledge Base. A wrong Abstention is one where the answer is there but the pack leaves it out or the Match Score marks it missing. Kept apart from Hallucination because the two fail in opposite directions.
_Avoid_: Refusal, miss
