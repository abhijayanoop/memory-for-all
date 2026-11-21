"""PROTOTYPE: does putting the chat title in front of every Chunk help? Prints ranks only."""
import re, pipeline
Q = [("final submission deadline Kiroween 2026 hackathon", r"dec(ember)?\.? 4", "kiroween"),
     ("final recommendation guitar and amp combo for a beginner rock player", r"blackstar", "guitar"),
     ("which AI coding tool is the daily driver for inline coding and quick changes", r"daily driver", "copilot"),
     ("Career3 AI interview agent name and what it looks like", r"vinee", "career3"),
     ("what car does the user drive", None, None)]
convs = pipeline.load("data-real/md"); pipeline.MAX = 1800
ch = pipeline.chunk(convs)
def run(label, chunks):
    print(label)
    for q, kw, conv in Q:
        h = pipeline.search(q, chunks, k=3)
        r = next((i + 1 for i, (c, _) in enumerate(h) if kw and re.search(kw, c["text"], re.I)), None)
        rc = next((i + 1 for i, (c, _) in enumerate(h) if conv and conv in c["title"].lower()), None)
        print(f"  {q[:45]:45} score {h[0][1]:.0%} | answer-bearing rank {r} | right-chat rank {rc}")
run("no title", ch)
for c in ch: c["text"] = f"Chat: {c['title']}\n{c['text']}"
for c, v in zip(ch, pipeline.emb.embed([c["text"] for c in ch])): c["vec"] = v
run("title prefixed", ch)
