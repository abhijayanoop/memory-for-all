import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

from .kb import KnowledgeBase, validate


def settings_file() -> Path:
    d = os.environ.get("MEMORYFORALL_CONFIG_DIR")
    return (Path(d) if d else Path(os.environ.get("APPDATA") or Path.home() / ".config") / "memoryforall") / "settings.json"


def main(argv=None, embedder=None) -> int:
    p = argparse.ArgumentParser(prog="memoryforall")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import").add_argument("folder")
    sub.add_parser("reindex")
    sub.add_parser("status")
    for s in sub.choices.values():
        s.add_argument("--kb")
    sub.add_parser("set-kb").add_argument("path")
    a = p.parse_args(argv)
    sf = settings_file()
    if a.cmd == "set-kb":
        path = Path(a.path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        sf.parent.mkdir(parents=True, exist_ok=True)
        sf.write_text(json.dumps({"kb": str(path)}), encoding="utf-8")
        print(f"Knowledge Base set to {path}")
        return 0
    kb_path = a.kb
    if not kb_path and sf.exists():
        kb_path = json.loads(sf.read_text(encoding="utf-8")).get("kb")
    if not kb_path:
        print("No Knowledge Base folder set. Run: memoryforall set-kb <folder> "
              f"(suggested: {Path.home() / 'Documents' / 'Memory for All'}), or pass --kb.", file=sys.stderr)
        return 2
    Path(kb_path).mkdir(parents=True, exist_ok=True)
    kb = KnowledgeBase(kb_path, embedder)
    if a.cmd == "import":
        counts = Counter()
        for f in sorted(Path(a.folder).glob("*.json")):
            try:
                counts[kb.save(validate(json.loads(f.read_text(encoding="utf-8")))).split("+")[-1]] += 1
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
