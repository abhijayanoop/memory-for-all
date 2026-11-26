# Spec 3: Context Pack

Status: ready-for-agent

Source decisions: `docs/spec-plan.md` (spec 3), `.scratch/memory-for-all-v1/issues/04-context-pack-format.md` (pack format, size limit, model calls, quote checks), `.scratch/memory-for-all-v1/issues/05-match-score-and-checks.md` (needs, floor, Hallucination), `.scratch/memory-for-all-v1/issues/08-local-models.md` (local writing model), spec 2 (`.scratch/search-and-modes/spec.md`). Throwaway prototype: `prototype/packproto.py`. Vocabulary: `GLOSSARY.md`.

## Problem Statement

I can now search my Conversations (spec 2), but a list of search hits is not something I can hand to a new chat. When I continue my work on ChatGPT or Claude, I want to paste one block that tells the model what I decided before, what the facts were, and where each came from, so the new chat starts from where I left off.

That block must not lie. In the prototype, a small local model's summary swapped which product was the guitar and which was the amp, even though every word was in my chats, and it cited the wrong source. An assistant's suggestion can easily be shown as my decision. If I changed my mind, the block must lead with what I decided last, not what I said first. And if my chats do not hold the answer, I want to be told so, not handed a confident block built from weak matches.

## Solution

The program gains a `pack "<request>"` action. For a Request it:

1. searches the Knowledge Base for up to 8 Chunks and keeps only those that pass the "not found" floor. If none pass, it says "Nothing found in your chats for this" and writes no pack;
2. asks the writing model (local by default, or hosted with my own OpenAI or Claude key, per the pack-writing Mode from spec 2) to **choose and order exact quotes** from those Chunks, grouped by subject, marking which choice replaced which;
3. checks every quote word for word against the sources, finds each quote's source and speaker itself, and drops any quote it cannot find;
4. asks the writing model, in a second call, to split the Request into needs and say which needs the verified quotes cover (for the Match Score in spec 4);
5. renders one plain Markdown block, at most 9,500 characters: a header line, my Request, **In short** (the Current Decisions as exact quotes), **Key decisions and facts** (exact quotes, each labelled You / ChatGPT / Claude with source numbers, the newest choice leading each subject and noting what it replaced and when), and **Sources** (the numbered Chunks).

The pack contains no model-written prose, so it can only say what my chats say. If the writing model fails, I get a clear error telling me how to fix it, and no pack.

## User Stories

### Getting a pack

1. As a user, I want to type a Request and get one Context Pack block back, so that I can paste my past context into any new chat.
2. As a user, I want the pack to be plain Markdown in one block, so that it pastes cleanly into ChatGPT, Claude or anywhere else.
3. As a user, I want the pack to open with the line "Context from my past chats (Memory for All):", so that the new chat's model knows what the block is.
4. As a user, I want my Request repeated in the pack, so that the new chat's model knows what the context was gathered for.
5. As a user, I want an **In short** section with my Current Decisions as exact quotes, so that the most important facts are seen first.
6. As a user, I want a **Key decisions and facts** section of exact quotes, so that every fact in the pack is something I or an assistant actually said.
7. As a user, I want a **Sources** section listing the Chunks the pack is built from, each with chat title, Platform, date and text, so that I and the new chat's model can check every quote in context.
8. As a user, I want each quote to carry its source numbers like [2], so that I can see where it came from.
9. As a user, I want the pack to contain no instructions to the new chat's model, so that it does not override what I am asking in that chat.
10. As a user, I want the pack printed to standard output and any notices printed separately, so that I can pipe or copy the pack alone.
11. As a developer of spec 6, I want the pack to be a single action returning a structured result (pack text or "nothing found", plus needs coverage and dropped quotes), so that the extension can show a preview and insert the text.

### Not making things up

12. As a user, I want the pack never to contain model-written summaries or rewording, so that the model cannot swap facts or add ones my chats do not hold.
13. As a user, I want every quote checked word for word (ignoring case and punctuation) against the source Chunks, so that a quote the model invented or altered never reaches the pack.
14. As a user, I want quotes the program cannot find in any source dropped, so that the pack only says what my chats say.
15. As a user, I want the program, not the model, to decide which source a quote came from, so that source numbers are always right even when the model cites the wrong one.
16. As a user, I want the program, not the model, to decide who said each quote (You, ChatGPT or Claude), so that a speaker label is never wrong.
17. As a user, I want very short quotes rejected, so that a matching fragment like "yes" cannot pass as evidence.
18. As a user, I want a quote that runs across two messages (part mine, part the assistant's) dropped, so that its speaker is never ambiguous.
19. As a user, I want quotes from the "Chat:" title line not counted as evidence, so that a chat's title is never shown as something said in it.
20. As a user, I want something an assistant suggested shown as "<Platform> suggested" unless I accepted it later in the same chat, so that a suggestion is never shown as my decision.
21. As a user, I want an assistant suggestion I did accept shown together with my acceptance quote, so that the pack shows why it counts as my decision.
22. As a user, I want quotes from my own notes (`## My notes`) labelled as mine, so that what I wrote myself counts as my words.
23. As a user, I want to be able to see which quotes were dropped and why, so that I can tell when the writing model is struggling.

### Current Decision

24. As a user, I want the newest choice on each subject to lead that subject, so that the pack reflects what I decided last.
25. As a user, I want the pack to note what the Current Decision replaced and when (for example "changed from X (January) to Y (March)"), so that the new chat knows I changed my mind and does not bring back the old choice.
26. As a user, I want "newest" decided by each Chunk's stored message date, checked by the program, so that a model mixing up order cannot make an old choice lead.
27. As a user, I want facts that are not changes of mind (several facts on one subject) listed without any "replaced" note, so that the pack does not invent a change of mind.
28. As a user, I want the Current Decisions repeated in **In short**, so that they stand out even in a long pack.

### Nothing found

29. As a user, I want every source Chunk to pass the "not found" floor, so that weak matches never become evidence in my pack.
30. As a user, I want "Nothing found in your chats for this" and no pack when no Chunk passes the floor, so that I am not handed a pack built from nothing.
31. As a user, I want "Nothing found in your chats for this" when every quote the model chose was dropped, so that an empty pack is never presented as an answer.
32. As a user, I want the writing model not called at all when nothing passes the floor, so that "nothing found" is fast and costs nothing in hosted Mode.

### Size

33. As a user, I want the pack kept to at most 9,500 characters, so that it stays plain text on ChatGPT (which turns pastes over 10,000 characters into an attachment).
34. As a user, I want the lowest-ranked source Chunks cut first when the pack is too long, down to their title line marked "(text left out for length)", so that every [n] still points somewhere.
35. As a user, I want key decisions never cut for size, so that the most important content always arrives.
36. As a user, I want a notice if the pack is still over the limit after every source is cut to its title line, so that I know it may arrive as an attachment.

### Needs coverage (feeds the Match Score)

37. As a user, I want my Request split into 1 to 4 needs from the Request alone, so that what counts as "needed" does not depend on what was found.
38. As a user, I want a need counted as covered only if a quote the program verified covers it, so that coverage can't be claimed without evidence.
39. As a user, I want the needs and which are missing printed after the pack (not inside it), so that I can see gaps now, before spec 4 adds the Match Score.
40. As a developer of spec 4, I want needs coverage returned as structured data on the pack result, so that the Match Score and quality checks can be computed from it.

### Choosing where the writing model runs

41. As a user, I want packs written by a local model (Qwen3-4B-Instruct through Ollama) by default, so that my chats never leave my computer.
42. As a user, I want packs written by OpenAI or Claude with my own key when my pack-writing Mode is hosted, so that I can get faster or better packs.
43. As a user, I want the program to use the pack-writing Mode and API I already set with `mode pack ...` (spec 2), so that there is one place to choose.
44. As a user, I want my key read only from the environment and never saved or printed, so that it never leaks into files or output.
45. As a user, in hosted Mode, I want only my Request and the source Chunks sent to the API, so that nothing else of mine leaves my computer.
46. As a user, I want the writing model to run with temperature 0, so that the same Request on the same Knowledge Base gives the same pack as far as the model allows.

### Failures

47. As a user, I want a clear error saying how to fix it when Ollama is not running or the model is not pulled (for example "start Ollama, then run `ollama pull qwen3:4b-instruct`"), so that I can fix local Mode myself.
48. As a user, I want a clear error when the hosted key is missing or rejected, or the API fails, so that I know what went wrong.
49. As a user, I want no fallback pack (for example sources only) when the writing model fails, so that a failure is never mistaken for a real pack.
50. As a user, I want a model answer that is not valid JSON treated as a writing model failure, and missing fields treated as empty, so that a malformed answer never crashes the program or slips into the pack.
51. As a user, I want an empty Request rejected and an empty or missing index reported (run reindex), as search already does, so that pack behaves like search.
52. As a user, I want pack to warn, as search does, when a re-embed is pending or search fell back to keywords only, so that I know the sources may be weaker.

### Speed

53. As a user, I want a pack written within 30 seconds on my laptop in local Mode, so that it feels usable mid-conversation.
54. As a user, I want only two model calls per pack, so that local packs stay within budget.
55. As a user, I want the time a pack took reported, so that I can see whether the budget holds.

## Implementation Decisions

### Modules

1. **Context Pack writer** (new, the one seam): an action `pack(kb, request, writer) -> PackResult`. It uses the Knowledge Base's `search` from spec 2 and a writing model. `PackResult` holds:
   - `text`: the pack, or none when nothing was found;
   - `nothing_found`: true when no Chunk passed the floor or no quote survived;
   - `sources`: the hits used, in rank order (numbered from 1);
   - `decisions`: the rendered subjects, each with its leading quote, its replaced quotes, speaker labels, source numbers and dates;
   - `needs`: each need with `covered` (program-verified) and its verifying quote;
   - `dropped`: quotes the program rejected, each with a reason (not in any source, too short, spans two messages, from the title line);
   - `over_limit`: true if still over 9,500 characters after cutting every source;
   - `seconds`: wall time.
   Raises a clear error for an empty Request (as `search` does) and a writing-model error (below) when a call fails.
2. **Writing model interface:** `name`, `ask(prompt) -> dict` (one JSON object). Temperature 0, JSON output. Three real implementations, chosen from the settings saved in spec 2 (`pack_mode`, `pack_api`):
   - local: Qwen3-4B-Instruct-2507 through Ollama's local HTTP API (`qwen3:4b-instruct`), JSON format;
   - hosted OpenAI: a small current OpenAI chat model, key from `OPENAI_API_KEY`;
   - hosted Claude: a small current Claude model (for example `claude-haiku-5-5`), key from `ANTHROPIC_API_KEY`.
   Model names are named constants. Each implementation turns connection failures, missing models, missing or rejected keys and non-JSON answers into one writing-model error type with a fix-it message. Tests use a scripted fake.
3. **Command line:** `pack "<request>"` builds the Knowledge Base as `search` does and the writer from the pack-writing Mode. It prints the pack text to standard output; to standard error it prints the needs (covered / missing), dropped quotes with reasons, the time taken, the over-limit notice, and spec 2's pending re-embed / keyword-only notices. On "nothing found" it prints "Nothing found in your chats for this" and exits 0. On a writing-model error it prints the message and exits non-zero. A hosted Mode with a missing key is refused before any work, with the same message `mode pack` gives.

### Pipeline

- **Search:** `search(request, k=8)`. Keep only hits whose re-ranker score is at or above `NOT_FOUND_FLOOR`, a named constant on the raw re-ranker score, untuned. Spec 4 sets it from the Test Set. If none remain, return `nothing_found` without calling the model.
- **Call 1, choose quotes:** the prompt gives the Request and the numbered sources (title, Platform, date, text) and asks only to choose and order exact quotes, grouped by subject. No judging, advice, comparing or conclusions; if sources disagree, list both. JSON shape (decision-rich part, adapted from the prototype):

  ```json
  {"subjects": [{"subject": "amp", "quotes": ["<exact words>"], "replaces": ["<exact words of an older choice>"],
                 "accepted_by": "<exact words where the user accepted an assistant suggestion, or empty>"}]}
  ```

  The model's own source numbers are not asked for and never trusted.
- **Quote verification (program):**
  - Normalise by lower-casing and turning every run of non-word characters into one space. A quote is verified if its normalised form is in a source's normalised text.
  - A quote under 12 normalised characters is rejected as too short.
  - The program finds every source holding the quote and cites all of them; the newest matching source decides the speaker and date; ties use the best-ranked source.
  - Speaker: the Chunk text is split into messages at lines starting `User: ` / `Assistant: ` (spec 1's Chunk text format). The quote must lie inside one message. `User:` and notes Chunks → **You**; `Assistant:` → the Chunk's Platform (**ChatGPT** or **Claude**). A quote found only in the `Chat:` title line is rejected.
  - A subject with no verified quote is dropped. If no subject survives, the result is `nothing_found`.
- **Current Decision (program):** within a subject, the verified `quotes` and `replaces` are ordered by their source Chunk's date. The newest leads. Every older quote that the model listed under `replaces`, or that the program moved down because it was older, is shown as replaced, with its date. Ties keep the model's order. A subject with no `replaces` is a list of facts with no "replaced" note.
- **Suggested vs accepted (program):** if a subject's leading quote is an assistant's, it is labelled "**<Platform> suggested:**" unless `accepted_by` is verified, spoken by You, in the same Conversation, and later than the suggestion (by Chunk position, then position in the text). Then the suggestion is shown followed by the acceptance quote, labelled **You:**.
- **Call 2, needs:** the prompt gives the Request alone and asks for 1 to 4 short needs, and, given the verified quotes (numbered), which quote covers each need, or none. A need is `covered` only if the program confirms the cited quote is one of the verified ones. This is one call (split plus cover), so a pack takes two model calls.
- **Rendering** (plain Markdown, one block, decided in ticket 04):

  ```
  Context from my past chats (Memory for All):
  **Request:** <request>

  **In short:**
  - <leading quote of each subject that has a replaced quote, or else the first subject's leading quote>

  **Key decisions and facts:**
  - **You:** "<quote>" [2] (2026-03-10). Changed from "<old quote>" [5] (2026-01-04).
  - **ChatGPT suggested:** "<quote>" [3]
  - **Claude:** "<quote>" [1]

  **Sources:**
  [1] <chat title> (Claude, 2026-03-10)
  <chunk text>
  ```

  Dates are shown as dates (no times). The Match Score is never in the pack.
- **Size limit:** `PACK_LIMIT = 9,500` characters. While over it, the lowest-ranked source with full text is cut to its title line plus "(text left out for length)". Header, Request, In short and Key decisions are never cut. If still over, `over_limit` is set and the pack is returned as is.

### Hosted Mode and privacy

- In hosted pack-writing Mode, the two prompts (Request, source Chunks, verified quotes) go to the chosen API and nothing else does. In local Mode nothing leaves the computer.
- Keys are read from the environment at call time, never stored or printed (spec 2's rule).

### What this spec does not change

- Search, the index, Chunks and the settings file format are unchanged. `pack_mode` and `pack_api` already exist from spec 2.
- ChatGPT's rich-UI markup (`<badge>`, `<Entity value="...">`) breaks exact quotes. Turning it into plain text is the Reader's job (spec 5). Until then, quotes from such answers may be dropped, which is safe.

## Testing Decisions

- A good test calls `pack` (or the command line) and checks what the user or a later spec sees: the pack text, `nothing_found`, needs coverage, dropped quotes and their reasons, exit codes and printed output. It does not check prompt wording, normalisation helpers or rendering internals. A refactor that keeps behaviour must not break tests.
- **The one seam, `pack(kb, request, writer)`:** a temporary Knowledge Base built from fixture Conversations, with spec 2's fake embedder and fake re-ranker, and a **scripted fake writer** that returns canned JSON per call (and records how many calls it got). Cases:
  - a quote present in a source appears in the pack with the right [n], speaker and date; a quote in multiple sources cites all of them and uses the newest matching source for its speaker and date (best rank breaks date ties); a quote the fake invents is dropped with reason "not in any source" and never appears;
  - a quote differing only in case and punctuation is accepted;
  - a too-short quote, a quote spanning a `User:` and an `Assistant:` line, and a quote only in the `Chat:` title line are each dropped with their reason;
  - a quote in two sources cites both; the speaker comes from the newest matching source, with rank breaking date ties;
  - the fake claiming a wrong source or speaker makes no difference: the program's own finding wins;
  - Current Decision: with an older and a newer Chunk on one subject, the newer quote leads and the older is noted as replaced with its date, even when the fake lists them the other way round; it also appears under In short;
  - a subject with several facts and no `replaces` has no "changed from" note;
  - an assistant quote with no acceptance is labelled "<Platform> suggested"; with a verified later user acceptance in the same Conversation it is shown with the acceptance; an acceptance from another Conversation, or earlier in the chat, does not count;
  - notes Chunks are labelled **You**;
  - no hit passes the floor → `nothing_found` and the fake writer was called zero times;
  - every quote dropped → `nothing_found`;
  - needs: a need covered by a verified quote is covered; a need the fake marks covered with an unverified or unknown quote is not;
  - size: with long sources, the pack is at most 9,500 characters, the lowest-ranked sources are cut to their title line first, every [n] still resolves, and key decisions are intact; with key decisions alone over the limit, `over_limit` is set;
  - the pack contains no Match Score and no text outside the agreed sections;
  - a fake writer that raises the writing-model error → the error reaches the caller and no pack is returned; a fake returning non-JSON is the same error; missing JSON fields are treated as empty;
  - an empty Request is rejected; an empty index gives `nothing_found` without calling the writer.
- **Command line:** smoke tests with the config directory pointed at a temporary folder and fakes injected, as in specs 1 and 2: pack text on standard output, needs and dropped quotes on standard error, "Nothing found in your chats for this" with exit 0, a writing-model error with a non-zero exit and its fix-it message, hosted Mode with a missing key refused before any model call.
- **Slow tests** (marked, skippable like spec 1's and 2's), skipped when Ollama is not reachable: an end-to-end pack on a small fixture with the real local models and Qwen3-4B through Ollama, checking the pack is well-formed, every quote is verified, and recording the time against the 30 s budget. No test calls OpenAI or Claude.
- **Prior art:** `tests/test_search.py` and `tests/test_model_switch.py` (Knowledge Base with fakes), `tests/test_modes.py` (command-line smoke tests and key checks), `tests/conftest.py` (fake embedder and re-ranker). `prototype/packproto.py` shows the quote check and size cutting to match, but it is not test code.

## Out of Scope

- The Match Score as a percentage and how it is shown, tuning the "not found" floor, the Test Set and the five quality checks: spec 4. This spec only returns needs coverage and uses an untuned floor constant.
- Turning ChatGPT rich-UI markup into plain text: the Reader, spec 5.
- The extension preview, inserting the pack into a chat, clipboard fallback and the live paste test (does an ~8,600-character pack stay as text on ChatGPT and Claude, and is the answer right): spec 6.
- Per-Platform size limits. There is one 9,500-character limit for both.
- Any model-written summary or rewording, and any fallback pack when the model fails.
- Choosing the Current Decision when chats disagree subtly (later spec, per the spec plan).
- Saving packs to files, pack history, or editing a pack before use.
- Speed work beyond measuring: spec 7.
- Streaming output, or more than two model calls per pack.

## Further Notes

- The prototype ran on only 7 chats, so the Current Decision rule is untested on real data. Spec 4's Test Set (at least 3 changed-mind questions) is where it gets measured.
- The prototype took 15 to 76 s with four calls. Two calls should fit 30 s. If the slow test misses it on the user's laptop in local Mode, the budget for local Mode may be raised to 60 s (ticket 04). Do not add a summary call to compensate for anything.
- In the prototype the 4B model cited the wrong source and swapped facts in its summary. That is why the program finds sources and speakers itself and the pack holds only exact quotes.
- `GLOSSARY.md` still defines the Context Pack as "a short summary, a list of key decisions and facts, and the original Chunks". Ticket 04 replaced the summary with **In short** (Current Decisions as exact quotes). The glossary entry should be updated to match.
- Claude's paste-to-attachment threshold is unpublished (one informal test: about 3,860 characters). A 9,500-character pack may arrive on Claude as an attachment. The model still reads it, so this is not an error.
