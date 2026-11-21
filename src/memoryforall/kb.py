"""Knowledge Base: Conversation validation, Markdown file format, atomic save."""
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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
    if not isinstance(chat_id, str) or not chat_id:
        raise ValueError("chat_id must be a non-empty string")
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
    machine, notes = body[1:i + 1], body[i + 1 + len(NOTES):]
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


class KnowledgeBase:
    def __init__(self, folder):
        self.folder = Path(folder)

    def _find(self, platform: str, chat_id: str) -> Path | None:
        return next((self.folder / platform).glob(f"*/*-{chat_id}.md"), None)

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
