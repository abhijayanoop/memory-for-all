"""Knowledge Base: Conversation validation, Markdown file format, atomic save."""
import json
import array
import hashlib
import os
import re
import sqlite3
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

RULES_VERSION = 3  # 3: adds the chunks_fts keyword table
# untuned, to be tuned against the Test Set (spec 4)
KEYWORD_TOP = 50
MEANING_TOP = 50
FUSION_K = 60  # reciprocal rank fusion: score = sum of 1 / (FUSION_K + rank)
RERANK_TOP = 20  # fused Chunks the re-ranker re-scores
PLATFORMS = ("chatgpt", "claude")
NOTES = "## My notes\n"
_HEADING = re.compile(r"^### (User|Assistant)(?: · (\S+))?$", re.M)
_ATTACH = re.compile(r"^attachment: (.*) \(not saved\)$")


@dataclass
class Message:
    sender: str
    time: str | None
    text: str
    attachments: list[str] = field(default_factory=list)


@dataclass
class Conversation:
    platform: str
    chat_id: str
    title: str
    created: str
    updated: str
    messages: list[Message]


def _utc(value) -> str:
    try:
        d = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"not an ISO time: {value!r}") from None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate(data) -> Conversation:
    """Raise ValueError with a reason if data is not a Platform-neutral Conversation."""
    if not isinstance(data, dict):
        raise ValueError("not a JSON object")
    if data.get("platform") not in PLATFORMS:
        raise ValueError(f"platform must be one of {PLATFORMS}")
    chat_id = data.get("chat_id")
    if not isinstance(chat_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", chat_id):
        raise ValueError("chat_id must be non-empty and only contain letters, digits, - and _")
    title = data.get("title")
    if title is not None and not isinstance(title, str):
        raise ValueError("title must be a string or null")
    msgs = data.get("messages")
    if not isinstance(msgs, list):
        raise ValueError("messages must be a list")
    out = []
    for m in msgs:
        if not isinstance(m, dict) or m.get("sender") not in ("user", "assistant"):
            raise ValueError("message sender must be user or assistant")
        text, atts = m.get("text", ""), m.get("attachments", [])
        if not isinstance(text, str) or not isinstance(atts, list) or not all(isinstance(a, str) for a in atts):
            raise ValueError("message text must be a string and attachments a list of strings")
        if not text and not atts:
            continue
        t = m.get("time")
        out.append(Message(m["sender"], None if t is None else _utc(t), text, atts))
    return Conversation(data["platform"], chat_id, title or "untitled",
                        _utc(data.get("created")), _utc(data.get("updated")), out)


def slug(title: str) -> str:
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)
    s = re.sub(r" +", "-", s)
    return s[:60].strip(". -") or "untitled"


def render(c: Conversation, notes: str = "") -> str:
    out = (f"---\nplatform: {c.platform}\nchat_id: {json.dumps(c.chat_id)}\n"
           f"title: {json.dumps(c.title, ensure_ascii=False)}\n"
           f"created: {c.created}\nupdated: {c.updated}\nstatus: on platform\n---\n\n")
    for m in c.messages:
        head = f"### {m.sender.capitalize()}" + (f" · {m.time}" if m.time else "")
        out += head + "\n" + m.text + "\n" + "".join(f"attachment: {a} (not saved)\n" for a in m.attachments) + "\n"
    return out + NOTES + notes


def parse(text: str) -> tuple[Conversation, str] | None:
    """Return (Conversation, notes), or None if the file is not a Conversation."""
    if not text.startswith("---\n") or "\n---\n" not in text:
        return None
    front, body = text[4:].split("\n---\n", 1)
    meta = dict(line.split(": ", 1) for line in front.split("\n") if ": " in line)
    if "platform" not in meta or "chat_id" not in meta:
        return None
    # shortcut: first "## My notes" line ends the messages, so a message containing it breaks round-trip
    body = "\n" + body
    i = body.find("\n" + NOTES)
    machine, notes = (body[1:], "") if i < 0 else (body[1:i + 1], body[i + 1 + len(NOTES):])
    msgs = []
    hs = list(_HEADING.finditer(machine))
    for k, h in enumerate(hs):
        end = hs[k + 1].start() if k + 1 < len(hs) else len(machine)
        lines = machine[h.end() + 1:end][:-1].split("\n")[:-1]
        atts = []
        while lines and (a := _ATTACH.match(lines[-1])):
            atts.insert(0, a.group(1))
            lines.pop()
        msgs.append(Message(h.group(1).lower(), h.group(2), "\n".join(lines), atts))
    return Conversation(meta["platform"], json.loads(meta["chat_id"]), json.loads(meta["title"]),
                        meta["created"], meta["updated"], msgs), notes


@dataclass
class Hit:
    chunk: "object"  # chunk.Chunk
    rank: int  # 1 = best
    score: float | None = None  # raw re-ranker score, filled by the re-ranker (ticket 03)


class KnowledgeBase:
    def __init__(self, folder, embedder=None, embedders=None, reranker=None):
        """embedder: the target (search Mode's) embedder. embedders: name -> constructor, used to embed
        the Request with the live index's model while a re-embed is pending."""
        from .embed import EMBEDDERS, FastEmbedder
        self.folder = Path(folder)
        self.embedder = embedder or FastEmbedder()
        self.embedders = EMBEDDERS if embedders is None else embedders
        if reranker is None:
            from . import rerank
            reranker = rerank.FastReranker()
        self.reranker = reranker
        self.index_path = self.folder / ".index" / "index.sqlite"

    def _find(self, platform: str, chat_id: str) -> Path | None:
        for p in sorted((self.folder / platform).glob(f"*/*-{chat_id}.md")):
            r = parse(p.read_text(encoding="utf-8"))  # glob also matches ids ending in -<chat_id>
            if r and r[0].chat_id == chat_id:
                return p
        return None

    @staticmethod
    def _write(dest: Path, text: str) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=dest.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            os.replace(tmp, dest)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def _set_status(self, platform: str, chat_id: str, gone_since: str | None) -> None:
        path = self._find(platform, chat_id)
        if not path:
            raise KeyError(chat_id)
        front, rest = path.read_text(encoding="utf-8").split("\n---\n", 1)
        lines = [l for l in front.split("\n") if not l.startswith(("status: ", "gone_since: "))]
        lines += (["status: no longer on the Platform", f"gone_since: {gone_since}"] if gone_since
                  else ["status: on platform"])
        self._write(path, "\n".join(lines) + "\n---\n" + rest)

    def mark_gone(self, platform: str, chat_id: str, noticed_at: str) -> None:
        self._set_status(platform, chat_id, noticed_at)

    def mark_present(self, platform: str, chat_id: str) -> None:
        self._set_status(platform, chat_id, None)

    def save(self, c: Conversation) -> str:
        """Return 'created', 'updated', 'renamed+updated' or 'unchanged'."""
        path = self._find(c.platform, c.chat_id)
        notes = ""
        if path:
            old = parse(path.read_text(encoding="utf-8"))
            if old and old[0].updated >= c.updated:
                return "unchanged"
            notes = old[1] if old else ""
        dest = self.folder / c.platform / c.created[:7] / f"{c.created[:10]}-{slug(c.title)}-{c.chat_id}.md"
        self._write(dest, render(c, notes))
        if not path:
            return "created"
        if path == dest:
            return "updated"
        path.unlink()
        return "renamed+updated"

    def conversations(self) -> list[Conversation]:
        out = []
        for p in sorted(self.folder.rglob("*.md")):
            r = parse(p.read_text(encoding="utf-8"))
            if r:
                out.append(r[0])
        return out

    def refresh_index(self) -> dict:
        """Re-chunk only new or changed Conversation files and drop Chunks of removed ones."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        rebuild = not self._index_current()
        target = self.index_path.with_name("index.sqlite.new") if rebuild else self.index_path
        if rebuild:
            target.unlink(missing_ok=True)
        db = sqlite3.connect(target)
        try:
            return self._refresh(db, target, rebuild)
        except BaseException:
            db.close()
            if rebuild:
                target.unlink(missing_ok=True)  # old index stays live
            raise

    def _index_current(self) -> bool:
        """True if the index exists, is readable and was built with the current embedder and rules."""
        if not self.index_path.exists():
            return False
        try:
            db = sqlite3.connect(self.index_path)
            try:
                return db.execute("select embedder, dimension, rules_version from meta").fetchall() == [
                    (self.embedder.name, self.embedder.dimension, RULES_VERSION)]
            finally:
                db.close()
        except sqlite3.Error:
            return False

    def _refresh(self, db, target, rebuild) -> dict:
        import sys
        from .chunk import chunk
        try:
            db.execute("select platform from files limit 1")  # old or missing schema: start fresh
        except sqlite3.OperationalError:
            db.executescript("""drop table if exists meta; drop table if exists files; drop table if exists chunks;
                drop table if exists chunks_fts;
                create table meta(embedder, dimension, rules_version, last_refreshed);
                create table files(path, fingerprint, chat_id, platform);
                create table chunks(id, kind, platform, chat_id, title, date, position, text, vector);
                create virtual table chunks_fts using fts5(id unindexed, text);""")
        known = {r[0]: r[1:] for r in db.execute("select path, fingerprint, chat_id, platform from files")}
        n = {"added": 0, "changed": 0, "removed": 0, "skipped": 0}

        def drop(path):
            _, chat_id, platform = known[path]
            db.execute("delete from files where path=?", (path,))
            # a renamed Conversation's new file already holds this key: keep its Chunks
            if not db.execute("select 1 from files where platform=? and chat_id=?", (platform, chat_id)).fetchone():
                db.execute("delete from chunks_fts where id in (select id from chunks where platform=? and chat_id=?)",
                           (platform, chat_id))
                db.execute("delete from chunks where platform=? and chat_id=?", (platform, chat_id))

        seen, keys = set(), set()
        for p in sorted(self.folder.rglob("*.md")):
            rel = p.relative_to(self.folder).as_posix()
            raw = p.read_bytes()
            try:
                text = raw.decode("utf-8")
                r = parse(text)
                if r is None and rel in known:
                    raise ValueError("no longer parses as a Conversation")
                if r is None and text.startswith("---\n") and re.search(
                        r"^(platform|chat_id|title): ", text.split("\n---\n")[0], re.M):
                    raise ValueError("damaged header")
            except (ValueError, KeyError) as e:
                print(f"warning: skipped {rel}: {e}", file=sys.stderr)
                n["skipped"] += 1
                seen.add(rel)  # keep its previous Chunks
                continue
            if r is None:
                continue  # not a Conversation
            seen.add(rel)
            if (r[0].platform, r[0].chat_id) in keys:
                print(f"warning: skipped {rel}: duplicate of another file for this chat", file=sys.stderr)
                n["skipped"] += 1
                continue
            keys.add((r[0].platform, r[0].chat_id))
            fp = hashlib.sha256(raw).hexdigest()
            if rel in known:
                if known[rel][0] == fp:
                    continue
                drop(rel)
                n["changed"] += 1
            else:
                n["added"] += 1
            c, notes = r
            db.execute("insert into files values (?,?,?,?)", (rel, fp, c.chat_id, c.platform))
            for k in chunk(c, notes, self.embedder):
                db.execute("insert into chunks values (?,?,?,?,?,?,?,?,?)",
                           (k.id, k.kind, k.platform, k.chat_id, k.title, k.date, k.position, k.text,
                            array.array("f", k.vector).tobytes()))
                db.execute("insert into chunks_fts values (?,?)", (k.id, k.text))
        for rel in set(known) - seen:
            drop(rel)
            n["removed"] += 1
        db.execute("delete from meta")
        db.execute("insert into meta values (?,?,?,?)", (self.embedder.name, self.embedder.dimension, RULES_VERSION,
                                                         datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        n["chunks"] = db.execute("select count(*) from chunks").fetchone()[0]
        db.commit()
        db.close()
        if rebuild:
            os.replace(target, self.index_path)  # swap in only when complete
        return n

    def _query(self, sql, params=()):
        if not self.index_path.exists():
            return []
        db = sqlite3.connect(self.index_path)
        try:
            return db.execute(sql, params).fetchall()
        finally:
            db.close()

    @staticmethod
    def _chunk(r):
        from .chunk import Chunk
        return Chunk(*r[:8], list(array.array("f", r[8])))

    def chunks(self) -> list:
        return [self._chunk(r) for r in self._query("select * from chunks order by platform, chat_id, position")]

    def search(self, request: str, k: int = 5) -> list[Hit]:
        """Chunks matching the Request by keyword and by meaning, fused, best first. Never refreshes the index."""
        if not request.strip():
            raise ValueError("Request is empty; type some words to search for")
        rows = {r[0]: r for r in self._query("select * from chunks")}
        if not rows:
            return []
        keyword = []
        words = re.findall(r"\w+", request)
        if words:
            # each word a quoted literal term, so user text is never read as FTS5 syntax
            match = " OR ".join('"' + w.replace('"', '""') + '"' for w in words)
            try:
                keyword = [r[0] for r in self._query("select id from chunks_fts where chunks_fts match ? "
                                                     "order by bm25(chunks_fts) limit ?", (match, KEYWORD_TOP))]
            except sqlite3.OperationalError:
                pass  # index from before the keyword table: reindex rebuilds it
        q = self._request_vector(request)
        # vectors are unit length, so cosine similarity is a dot product
        sim = {} if q is None else {i: sum(a * b for a, b in zip(q, array.array("f", r[8]))) for i, r in rows.items()}
        meaning = sorted(sim, key=sim.get, reverse=True)[:MEANING_TOP]
        fused = {}
        for ranking in (keyword, meaning):
            for rank, i in enumerate(ranking, 1):
                fused[i] = fused.get(i, 0) + 1 / (FUSION_K + rank)
        best = sorted(fused, key=fused.get, reverse=True)[:RERANK_TOP]
        scores = dict(zip(best, self.reranker.rerank(request, [rows[i][7] for i in best])))
        best.sort(key=scores.get, reverse=True)  # stable: ties keep fused order
        return [Hit(self._chunk(rows[i]), n, scores[i]) for n, i in enumerate(best[:k], 1)]

    def _request_vector(self, request: str):
        """The Request embedded with the live index's model, or None (keyword only) if that model is unusable."""
        live = self.index_embedder()
        if live in (None, self.embedder.name):
            return self.embedder.embed([request])[0]
        try:
            return self.embedders[live]().embed([request])[0]
        except (KeyError, RuntimeError) as e:  # unknown name, or a hosted model whose key is gone
            import sys
            print(f"warning: the index's model {live} cannot be used ({e}); keyword search only. "
                  "Run: memoryforall reindex", file=sys.stderr)
            return None

    def index_embedder(self) -> str | None:
        """Name of the embedder the live index was built with; differs from embedder.name while a re-embed is pending."""
        r = self._query("select embedder from meta")
        return r[0][0] if r else None

    def last_refreshed(self) -> str | None:
        r = self._query("select last_refreshed from meta")
        return r[0][0] if r else None
