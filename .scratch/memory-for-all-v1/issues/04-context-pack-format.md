# context-pack-format

Type: prototype
Status: resolved
Blocked by: 03

## Question

Try the real Context Pack format and size limits per Platform. What does a pack include so nothing needed is missing?

## Answer

Settled by grilling and a prototype (2026-11-22 to 2026-11-24). Prototype: `prototype/packproto.py`, run on the 7 real chats with Qwen3-4B-Instruct through Ollama, temperature 0.

**Size limits (researched):**
- ChatGPT turns a paste over 10,000 characters into an attachment, on every plan (official release notes).
- Claude turns long pastes into a "Pasted text" attachment. No threshold is published, and one informal test found it near 3,860 characters.
- Either way the model still reads it, so an attachment is a normal result, not an error.
- **One pack limit: 9,500 characters.** That's plain text on ChatGPT and may become an attachment on Claude.

**Pack format** (plain Markdown, one block):
1. The line "Context from my past chats (Memory for All):".
2. **Request:** the user's Request.
3. **In short:** the Current Decision(s), as exact quotes. No model-written summary: in the prototype the 4B model's summary swapped which product was the guitar and which was the amp, even though every word was in the chats.
4. **Key decisions and facts:** exact quotes only, each labelled **You:**, **ChatGPT:** or **Claude:**, with its source numbers [n]. A Current Decision leads its subject and notes what it replaced and when. Something the assistant suggested counts as the user's decision only if the user accepted it later in the chat; otherwise it's shown as "<Platform> suggested".
5. **Sources:** numbered Chunks, each with chat title, Platform, date and text.
- The pack contains no other instructions for the model. The Match Score is shown only in the extension preview, not in the pack.

**What the program does:**
- Search returns up to 8 Chunks, and **each** source must pass the "not found" floor. If none passes, it shows "Nothing found in your chats for this" and writes no pack.
- The writing model only **chooses and orders** quotes. It never rewords them.
- The program checks every quote word for word (ignoring case and punctuation) against the sources, and finds each quote's source itself rather than trusting the model's numbers (the model cited the wrong source in the prototype). Unverified quotes are dropped.
- Over the size limit, the lowest-ranked source Chunks are cut first, down to their title line so [n] still resolves. Key decisions are never cut.
- The model works out the Current Decision from each Chunk's date (the message time, already stored per Chunk).
- Two model calls per pack: (1) choose quotes; (2) split the Request into needs from the Request alone, then mark which needs a verified quote covers.
- If the writing model fails (for example Ollama is not running), show a clear error saying how to fix it. No fallback pack.
- Speed budget: 30 s per pack, raised to 60 s for local Mode only if spec 3's measurement misses it. The prototype took 15 to 76 s with four calls.

**Found in the prototype, decided for other specs:**
- ChatGPT stores rich-UI markup in answers (`<badge>`, `<Entity value="...">`), so exact quotes were impossible. The Reader (spec 5) turns this markup into the visible plain text before saving.

**Caveats:**
- Only 7 chats, so the Current Decision rule (newest first, notes what it replaced) is untested.
- The live paste test is not done yet. The first try attached the file instead of pasting its text. Check it in spec 6: paste a ~8,600-character pack as text into ChatGPT and Claude, followed by a question, and record whether it stays as text and whether the answer is right.
