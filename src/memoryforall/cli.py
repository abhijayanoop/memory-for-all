import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

from .embed import EMBEDDERS, KEYS, SEARCH_EMBEDDER
from .kb import KnowledgeBase, validate


def settings_file() -> Path:
    d = os.environ.get("MEMORYFORALL_CONFIG_DIR")
    return (Path(d) if d else Path(os.environ.get("APPDATA") or Path.home() / ".config") / "memoryforall") / "settings.json"


# Allowed values per setting; the first is the default.
MODES = {"search_mode": ("local", "hosted"), "pack_mode": ("local", "hosted"), "pack_api": ("openai", "claude")}


def load_settings(sf: Path) -> dict:
    """The settings file with Mode defaults filled in. ValueError names the file on a corrupt file or unknown value."""
    s = {}
    if sf.exists():
        try:
            s = json.loads(sf.read_text(encoding="utf-8"))
        except ValueError:
            s = None
        if not isinstance(s, dict):
            raise ValueError(f"Settings file {sf} is corrupt; delete it or run: memoryforall set-kb <folder>")
    for k, allowed in MODES.items():
        v = s.setdefault(k, allowed[0])
        if v not in allowed:
            raise ValueError(f"Settings file {sf} has unknown {k} {v!r}; expected one of: {', '.join(allowed)}")
    return s


def save_settings(sf: Path, s: dict) -> None:
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(s), encoding="utf-8")


def modes_text(s: dict) -> str:
    pack = s["pack_mode"] + (f" ({s['pack_api']})" if s["pack_mode"] == "hosted" else "")
    return f"search: {s['search_mode']}\npack: {pack}"


def set_mode(sf: Path, s: dict, which: str, value: str, api: str | None) -> int:
    if which == "search":
        if value == "hosted":
            if not os.environ.get(KEYS["openai"]):
                print(f"Hosted search needs {KEYS['openai']} in the environment (Claude offers no embeddings).",
                      file=sys.stderr)
                return 2
            print("Chunks (on reindex) and Requests (on search) will be sent to OpenAI. Run reindex to re-embed.")
        s["search_mode"] = value
    else:
        api = api or s["pack_api"]
        if value == "hosted" and not os.environ.get(KEYS[api]):
            print(f"Hosted pack-writing with {api} needs {KEYS[api]} in the environment.", file=sys.stderr)
            return 2
        s["pack_mode"], s["pack_api"] = value, api
    save_settings(sf, s)
    print(modes_text(s))
    return 0


def main(argv=None, embedder=None, embedders=EMBEDDERS, writer=None) -> int:
    p = argparse.ArgumentParser(prog="memoryforall")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import").add_argument("folder")
    sub.add_parser("reindex")
    sub.add_parser("status")
    sub.add_parser("pack").add_argument("request")
    search_p = sub.add_parser("search")
    search_p.add_argument("request")
    search_p.add_argument("-k", type=int, default=5)
    quality_p = sub.add_parser("quality")
    quality_sub = quality_p.add_subparsers(dest="quality_cmd", required=True)
    add_p = quality_sub.add_parser("add")
    add_p.add_argument("question")
    add_p.add_argument("--label", required=True, choices=("answerable", "partly", "unanswerable"))
    add_p.add_argument("--changed-mind", action="store_true")
    add_p.add_argument("--kb")
    run_p = quality_sub.add_parser("run")
    run_p.add_argument("--kb")
    score_p = quality_sub.add_parser("score")
    score_p.add_argument("review", nargs="?")
    score_p.add_argument("--kb")
    for cmd_p in sub.choices.values():
        cmd_p.add_argument("--kb")
    sub.add_parser("set-kb").add_argument("path")
    m = sub.add_parser("mode")
    m.add_argument("which", nargs="?", choices=("search", "pack"))
    m.add_argument("value", nargs="?", choices=("local", "hosted"))
    m.add_argument("--api", choices=tuple(KEYS))
    a = p.parse_args(argv)
    sf = settings_file()
    if a.cmd == "set-kb":
        path = Path(a.path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        try:
            s = load_settings(sf)
        except ValueError:
            s = {}  # set-kb is the advertised fix for a corrupt file, so it starts fresh
        s["kb"] = str(path)
        save_settings(sf, s)
        print(f"Knowledge Base set to {path}")
        return 0
    try:
        s = load_settings(sf)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    if a.cmd == "mode":
        if a.which and a.value:
            return set_mode(sf, s, a.which, a.value, a.api)
        if a.which or a.api:
            p.error("usage: mode [search local|hosted | pack local|hosted [--api openai|claude]]")
        print(modes_text(s))
        return 0
    if a.cmd == "pack" and s["pack_mode"] == "hosted" and not os.environ.get(KEYS[s["pack_api"]]):
        api = s["pack_api"]
        print(f"Hosted pack-writing with {api} needs {KEYS[api]} in the environment.", file=sys.stderr)
        return 2
    kb_path = a.kb or s.get("kb")
    if not kb_path:
        print("No Knowledge Base folder set. Run: memoryforall set-kb <folder> "
              f"(suggested: {Path.home() / 'Documents' / 'Memory for All'}), or pass --kb.", file=sys.stderr)
        return 2
    Path(kb_path).mkdir(parents=True, exist_ok=True)
    kb = KnowledgeBase(kb_path, embedder or embedders[SEARCH_EMBEDDER[s["search_mode"]]](), embedders)
    if a.cmd == "quality":
        from .quality import add, load_test_set, run, score, write_review, read_review
        from .pack import HostedWriter, LocalWriter, WritingModelError, NOT_FOUND_FLOOR
        from .chunk import MERGE_SIMILARITY, CAP
        try:
            if a.quality_cmd == "add":
                add(kb, a.question, a.label, a.changed_mind)
                return 0
            if a.quality_cmd == "run":
                test_set = load_test_set(kb.folder / "quality" / "test-set.json")
                pack_writer = writer or (HostedWriter(s["pack_api"]) if s["pack_mode"] == "hosted" else LocalWriter())
                report = run(kb, test_set, pack_writer)
                report.settings = {"search Mode": s["search_mode"], "pack Mode": s["pack_mode"],
                                   "pack API": s["pack_api"], "writing model": getattr(pack_writer, "name", type(pack_writer).__name__),
                                   "re-ranker": getattr(kb.reranker, "name", type(kb.reranker).__name__),
                                   "floor": NOT_FOUND_FLOOR, "merge cutoff": MERGE_SIMILARITY, "Chunk cap": CAP}
                path = write_review(report, kb.folder / "quality" / "runs")
                print(f"Review: {path}")
                if test_set.shortfalls:
                    print("Test Set shortfall: " + ", ".join(test_set.shortfalls))
            else:
                paths = sorted((kb.folder / "quality" / "runs").glob("*.md"))
                if not a.review and not paths:
                    raise ValueError("No review file found; run: memoryforall quality run")
                report = read_review(a.review or paths[-1])
            checks = score(report)
            for check in checks:
                print(f"{check.name}: {check.value} {'PASS' if check.passed else 'FAIL'}")
                for question in check.failures:
                    print(f"  {question}")
            return 0 if all(check.passed for check in checks) else 1
        except (ValueError, OSError, WritingModelError) as e:
            print(e, file=sys.stderr)
            return 2
    if a.cmd in ("search", "status", "pack"):  # not for reindex: it must still recover a damaged index file
        live, pending = kb.index_embedder(), kb.reembed_pending()
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
        try:
            n = kb.refresh_index()
        except RuntimeError as e:  # hosted embedder failures; the old index stays live
            print(f"reindex failed, old index kept: {e}", file=sys.stderr)
            return 1
        print(", ".join(f"{k}: {n[k]}" for k in ("added", "changed", "removed", "skipped", "chunks")))
    elif a.cmd == "pack":
        from .pack import HostedWriter, LocalWriter, WritingModelError, pack
        try:
            result = pack(kb, a.request, writer or (HostedWriter(s["pack_api"]) if s["pack_mode"] == "hosted" else LocalWriter()))
        except ValueError as e:
            print(e, file=sys.stderr)
            return 2
        except WritingModelError as e:
            print(e, file=sys.stderr)
            return 1
        if pending:
            print(f"note: re-embed pending; searching the index built with {live} until the next reindex", file=sys.stderr)
        print(f"Pack took {result.seconds:.2f} seconds", file=sys.stderr)
        if result.over_limit:
            print("Pack exceeds 9,500 characters after shortening all sources.", file=sys.stderr)
        for d in result.dropped:
            print(f"Dropped: {d.quote} ({d.reason})", file=sys.stderr)
        if result.nothing_found:
            if not kb.chunks():
                print("The index is empty or missing. Run: memoryforall reindex", file=sys.stderr)
            print("Nothing found in your chats for this")
        else:
            print(result.text)
            for need in result.needs:
                print(f"{need.need}: {'covered' if need.covered else 'missing'}", file=sys.stderr)
            if result.match_score:
                print(f"Match Score: {result.match_score.text}", file=sys.stderr)
    elif a.cmd == "search":
        try:
            hits = kb.search(a.request, a.k)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 2
        if pending:
            print(f"note: re-embed pending; searching the index built with {live} until the next reindex")
        idx = kb.index_path
        if idx.exists() and any(p.stat().st_mtime > idx.stat().st_mtime for p in kb.folder.rglob("*.md")
                                if p.relative_to(kb.folder).parts[0] != "quality"):
            print("note: files changed since the last reindex; run: memoryforall reindex")
        if not hits:
            print("No matches." if kb.chunks() else "The index is empty or missing. Run: memoryforall reindex")
        for h in hits:
            c = h.chunk
            print(f"{h.rank}. {c.title} · {c.platform} · {c.date[:10]} · {c.id}" + (" · notes" if c.kind == "notes" else "")
                  + f" · score {h.score:.3f}")
            print("   " + c.text[:200].replace("\n", " "))
    else:
        by = Counter(c.platform for c in kb.conversations())
        for pl in ("chatgpt", "claude"):
            print(f"{pl}: {by[pl]}")
        print(f"chunks: {len(kb.chunks())}")
        print(f"last refreshed: {kb.last_refreshed() or 'never'}")
        print(modes_text(s))
        print(f"index model: {live or 'none'}" + (f" (re-embed pending to {kb.embedder.name})" if pending else ""))
        for key in sorted(set(KEYS.values())):
            print(f"{key}: {'present' if os.environ.get(key) else 'missing'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
