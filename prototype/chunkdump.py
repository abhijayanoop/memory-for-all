"""PROTOTYPE: show how real chats get cut into Chunks. Usage: python chunkdump.py [dir]  (default data-real/md)"""
import sys, pipeline
chunks = pipeline.chunk(pipeline.load(sys.argv[1] if len(sys.argv) > 1 else "data-real/md"))
for c in chunks:
    print(f"[{c['conv'][:18]} {c['platform']} {c['date']}] {len(c['text'])} chars | {c['text'][:110]!r}")
print(len(chunks), "Chunks; sizes (chars):", sorted(len(c["text"]) for c in chunks))
