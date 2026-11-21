import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from .kb import KnowledgeBase, validate


def main(argv=None, embedder=None) -> int:
    p = argparse.ArgumentParser(prog="memoryforall")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import").add_argument("folder")
    sub.add_parser("reindex")
    sub.add_parser("status")
    for s in sub.choices.values():
        s.add_argument("--kb", required=True)
    a = p.parse_args(argv)
    kb = KnowledgeBase(a.kb, embedder)
    if a.cmd == "import":
        counts = Counter()
        for f in sorted(Path(a.folder).glob("*.json")):
            try:
                counts[kb.save(validate(json.loads(f.read_text(encoding="utf-8"))))] += 1
            except ValueError as e:  # JSONDecodeError is a ValueError
                counts["rejected"] += 1
                print(f"rejected {f.name}: {e}", file=sys.stderr)
        print(", ".join(f"{k}: {counts[k]}" for k in ("created", "updated", "unchanged", "rejected")))
    elif a.cmd == "reindex":
        n = kb.refresh_index()
        print(f"files: {n['files']}, chunks: {n['chunks']}, skipped: {n['skipped']}")
    else:
        by = Counter(c.platform for c in kb.conversations())
        for pl in ("chatgpt", "claude"):
            print(f"{pl}: {by[pl]}")
        print(f"chunks: {len(kb.chunks())}")
        print(f"last refreshed: {kb.last_refreshed() or 'never'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
