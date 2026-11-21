"""PROTOTYPE: compare Chunk size caps on the user's 5 real test questions. Prints only ranks and scores, no chat text."""
import re, sys, pipeline
Q = [("final submission deadline Kiroween 2026 hackathon", r"dec(ember)?\.? 4"),
     ("final recommendation guitar and amp combo for a beginner rock player", r"blackstar"),
     ("which AI coding tool is the daily driver for inline coding and quick changes", r"daily driver"),
     ("Career3 AI interview agent name and what it looks like", r"vinee"),
     ("what car does the user drive", None)]
convs = pipeline.load("data-real/md")
for cap in (800, 1800):
    pipeline.MAX = cap
    chunks = pipeline.chunk(convs)
    print(f"\ncap {cap}: {len(chunks)} Chunks")
    for q, kw in Q:
        hits = pipeline.search(q, chunks, k=3)
        rank = next((i + 1 for i, (c, _) in enumerate(hits) if kw and re.search(kw, c["text"], re.I)), None)
        print(f"  {q[:55]:55} top score {hits[0][1]:.0%} | answer-bearing Chunk rank: {rank if kw else 'n/a (should be not found)'}")
