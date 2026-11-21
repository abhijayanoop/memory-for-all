"""Chunker: (Conversation, notes, embedder) -> Chunks. Pure."""
from dataclasses import dataclass

CAP = 1800


@dataclass
class Chunk:
    id: str
    kind: str
    platform: str
    chat_id: str
    title: str
    date: str
    position: int
    text: str
    vector: list[float]


def _units(c):
    """Yield (question time or None, text) per unit."""
    unit = None
    for m in c.messages:
        if m.sender == "user":
            if unit:
                yield unit
            unit = [m.time, f"User: {m.text}"]
        else:
            if unit is None:
                unit = [None, ""]
            unit[1] += ("\n" if unit[1] else "") + f"Assistant: {m.text}"
    if unit:
        yield unit


def chunk(c, notes, embedder) -> list[Chunk]:
    prefix = f"Chat: {c.title}\n"
    room = CAP - len(prefix)
    items = [("exchange", t, x) for t, x in _units(c)]
    if notes.strip():
        items.append(("notes", None, "My notes:\n" + notes.strip()))
    rows = []
    for kind, time, body in items:
        # shortcut: plain cut every `room` characters, ticket 04 adds paragraph/line/sentence splitting
        for i in range(0, max(len(body), 1), room):
            rows.append((kind, time or c.updated, prefix + body[i:i + room]))
    vectors = embedder.embed([r[2] for r in rows]) if rows else []
    return [Chunk(f"{c.platform}:{c.chat_id}:{n}", k, c.platform, c.chat_id, c.title, d, n, t, v)
            for n, ((k, d, t), v) in enumerate(zip(rows, vectors))]
