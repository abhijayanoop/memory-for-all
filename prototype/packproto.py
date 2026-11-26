"""PROTOTYPE (throwaway, ticket 04): build real Context Packs from the real chats with the local writing model.
Question: does the agreed format fit 9,500 characters, and can the program stop the writing model from adding
anything the chats do not say (every fact checked word for word against its source)?
Run: .venv/Scripts/python packproto.py <out_dir>"""
import json, re, sys, time, urllib.request
from pathlib import Path
import pipeline

BUDGET, MODEL, FLOOR = 9500, "qwen3:4b-instruct", 0.5  # shortcut: untuned floor, ticket 05 sets it from the Test Set
QS = ["final recommendation guitar and amp combo for a beginner rock player",
      "which AI coding tool is the daily driver for inline coding and quick changes",
      "Career3 AI interview agent name and what it looks like",
      "what car does the user drive"]  # not in any chat: must give "nothing found"


def ask(prompt):
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False, "format": "json",
                       "options": {"temperature": 0}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", body, {"Content-Type": "application/json"})
    return json.loads(json.loads(urllib.request.urlopen(req, timeout=600).read())["response"])


def norm(t):
    return re.sub(r"\W+", " ", str(t).lower()).strip()


def grounded(quotes, hits):
    """Source numbers holding each quote word for word (ignoring case and punctuation), or [] if any quote is
    in no source. The program finds the sources itself; the model's own source numbers are not trusted."""
    quotes = [quotes] if isinstance(quotes, str) else quotes or []
    if sum(len(norm(x)) for x in quotes) < 12:
        return []
    found = [next((i for i, (c, _) in enumerate(hits, 1) if norm(x) in norm(c["text"])), None) for x in quotes]
    return [] if None in found else sorted(set(found))


def write(q, hits):
    """Small separate calls; the program checks each answer against the sources instead of trusting it."""
    src = "\n\n".join(f"[{i}] {c['title']} ({c['platform']}, {c['date']})\n{c['text']}" for i, (c, _) in enumerate(hits, 1))
    needs = ask(f"""Split this Request into 1 to 4 short things it asks for. Use only the Request's own meaning; add nothing.
Return JSON: {{"needs": ["..."]}}
Request: {q}""").get("needs", [])
    raw = ask(f"""List the decisions and facts in the sources that answer the Request.
Rules: every item must copy the exact words (one or more short pieces) that show it, as "quotes".
Do not judge, compare prices, give advice or draw conclusions. If sources disagree, list both; the newer date is the Current Decision.
Return JSON: {{"decisions": [{{"text": "<the fact, in plain words>", "quotes": ["<exact words from the source>"]}}]}}

Request: {q}

Sources:
{src}""").get("decisions", [])
    for d in raw:
        d["sources"] = grounded(d.get("quotes"), hits)
    kept = [d for d in raw if d["sources"]]
    dropped = [d for d in raw if d not in kept]
    cover = ask(f"""For each need, say if the sources answer it. If yes, copy the exact words (one or more short pieces) from the sources as "quotes".
If the sources do not answer it, set "covered": false and leave quotes empty. Never guess.
Return JSON: {{"needs": [{{"need": "...", "covered": true, "quotes": ["..."]}}]}}
Needs: {json.dumps(needs)}

Sources:
{src}""").get("needs", [])
    for x in cover:  # covered only if the program finds the quote in the cited source
        x["covered"] = bool(x.get("covered")) and bool(grounded(x.get("quotes"), hits))
    facts = "\n".join(f"- {d['text']}" for d in kept)
    summary = ask(f"""Rewrite these facts as a summary of at most 4 sentences. Use only these facts; add no new names,
numbers, judgements or advice. Return JSON: {{"summary": "..."}}
Facts:
{facts}""").get("summary", "") if kept else ""
    # second guard: drop summary sentences naming a number or capitalised word that is in no source
    vocab = norm(src)
    sents = [x for x in re.split(r"(?<=[.!?])\s+", summary) if x]
    names = lambda x: re.findall(r"\b[A-Z][\w-]+|\S*\d\S*", x)[1:]  # skip the sentence's first word
    bad = [x for x in sents if any(norm(w) and norm(w) not in vocab for w in names(x))]
    return {"summary": " ".join(x for x in sents if x not in bad),
            "decisions": [{"text": d["text"], "quotes": d["quotes"], "sources": d["sources"]} for d in kept],
            "needs": cover, "dropped": dropped, "dropped_summary": bad}


def render(q, out, hits):
    head = ["Context from my past chats (Memory for All):", f"**Request:** {q}", "", "## Summary", out["summary"],
            "", "## Key decisions and facts"]
    head += [f"- {d['text']} " + "".join(f"[{n}]" for n in d["sources"]) for d in out["decisions"]]
    head += ["", "## Sources"]
    srcs = [f"[{i}] {c['title']} ({c['platform']}, {c['date']})\n{c['text']}" for i, (c, _) in enumerate(hits, 1)]
    while True:  # drop lowest-ranked full Chunks first; keep their title line so [n] still resolves
        text = "\n".join(head) + "\n" + "\n\n".join(srcs)
        full = [i for i, s in enumerate(srcs) if "\n" in s]
        if len(text) <= BUDGET or not full:
            return text
        srcs[full[-1]] = srcs[full[-1]].split("\n", 1)[0] + " (text left out for length)"


out_dir = Path(sys.argv[1]); out_dir.mkdir(parents=True, exist_ok=True)
convs = pipeline.load("data-real/md"); pipeline.MAX = 1800


def plain(t):
    """ChatGPT stores rich-UI markup in answers; keep only what the user saw as text."""
    t = re.sub(r'<Entity\s+value="([^"]*)"[^>]*/>', r"\1", t)
    return re.sub(r"</?[A-Za-z][^<>]*>", " ", t)


for c in convs:
    c["msgs"] = [(role, plain(text)) for role, text in c["msgs"]]
chunks = pipeline.chunk(convs)
for c in chunks:
    c["text"] = f"Chat: {c['title']}\n{c['text']}"  # title prefix from ticket 03
for c, v in zip(chunks, pipeline.emb.embed([c["text"] for c in chunks])):
    c["vec"] = v
for n, q in enumerate(QS, 1):
    hits = pipeline.search(q, chunks, k=8)
    print(f"\nQ{n}: {q}\n  top scores: {[round(s, 2) for _, s in hits]}")
    hits = [h for h in hits if h[1] >= FLOOR]  # Q21: every source must pass the floor
    if not hits:
        print("  -> Nothing found in your chats for this"); continue
    t = time.time()
    out = write(q, hits)
    print(f"  writing took {time.time() - t:.0f}s, {len(hits)} sources")
    need = out["needs"]
    score = round(100 * sum(x["covered"] for x in need) / len(need)) if need else 0
    text = render(q, out, hits)
    (out_dir / f"pack{n}.md").write_text(text, encoding="utf-8")
    for d in out["dropped"]: print(f"  DROPPED (quote not in source): {d.get('text')!r} quotes={d.get('quotes')!r}")
    for x in out["dropped_summary"]: print(f"  DROPPED summary sentence: {x!r}")
    print(f"  -> pack{n}.md: {len(text)} chars, Match Score {score}%, needs: {[(x.get('need'), x['covered']) for x in need]}")
