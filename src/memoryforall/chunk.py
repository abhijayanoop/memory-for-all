"""Chunker: (Conversation, notes, embedder) -> Chunks. Pure."""
import re
from dataclasses import dataclass

CAP = 1800
MERGE_SIMILARITY = 0.72  # untuned, to be tuned against the Test Set (spec 4)
_BREAKS = [r"(?<=\n\n)", r"(?<=\n)", r"(?<=[.!?] )"]  # blank line, line break, sentence end


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
    """Yield (question time, question or None, [answers]) per unit."""
    unit = None
    for m in c.messages:
        if m.sender == "user":
            if unit:
                yield unit
            unit = (m.time, m.text, [])
        else:
            if unit is None:
                unit = (None, None, [])
            unit[2].append(m.text)
    if unit:
        yield unit


def _pieces(text, room, level=0):
    """Break text into pieces of at most room chars: coarsest break first, packed greedily."""
    if len(text) <= room:
        return [text]
    if level == len(_BREAKS):  # hard cut
        return [text[i:i + room] for i in range(0, len(text), room)]
    out, cur = [], ""
    for seg in re.split(_BREAKS[level], text):
        for part in _pieces(seg, room, level + 1):
            if len(cur) + len(part) > room:
                out.append(cur)
                cur = ""
            cur += part
    return out + [cur] if cur else out


def _split(prefix, head, label, body):
    """Pieces of one over-cap unit; head is the repeated heading line (or None)."""
    room = CAP - len(prefix) - (len(head) + 1 if head else 0) - len(label)
    return [prefix + (head + "\n" if head else "") + label + p.rstrip() for p in _pieces(body, room)]


def _cos(a, b):
    return sum(x * y for x, y in zip(a, b))


def chunk(c, notes, embedder) -> list[Chunk]:
    prefix = f"Chat: {c.title}\n"
    rows = []  # [kind, date, piece texts, body if the unit is unsplit (mergeable) else None]
    for time, q, answers in _units(c):
        date = time or c.updated
        body = "\n".join(([f"User: {q}"] if q is not None else []) + [f"Assistant: {a}" for a in answers])
        answer = "\n".join(answers)
        if len(prefix) + len(body) <= CAP:
            rows.append(["exchange", date, [prefix + body], body])
        elif q is not None and len(prefix) + len(q) + 6 > CAP:  # question alone too big
            texts = _split(prefix, None, "User: ", q) + _split(prefix, f"User: {q[:300]}", "Assistant: ", answer)
            rows.append(["exchange", date, texts, None])
        else:
            head = f"User: {q[:300]}" if q is not None else None
            rows.append(["exchange", date, _split(prefix, head, "Assistant: ", answer), None])
    # merge small same-subject neighbours; split units never merge
    vecs = embedder.embed([r[2][0] for r in rows]) if rows else []
    merged, last = [], None
    for r, v in zip(rows, vecs):
        m = merged[-1] if merged else None
        if m and r[3] and m[3] and _cos(last, v) > MERGE_SIMILARITY and len(m[2][0]) + 1 + len(r[3]) <= CAP:
            m[2][0] += "\n" + r[3]
            m[3] += "\n" + r[3]
        else:
            merged.append(r)
        last = v
    if notes.strip():
        merged.append(["notes", c.updated, _split(prefix, None, "My notes:\n", notes.strip()), None])
    flat = [(k, d, t) for k, d, texts, _ in merged for t in texts]
    vectors = embedder.embed([r[2] for r in flat]) if flat else []
    return [Chunk(f"{c.platform}:{c.chat_id}:{n}", k, c.platform, c.chat_id, c.title, d, n, t, v)
            for n, ((k, d, t), v) in enumerate(zip(flat, vectors))]
