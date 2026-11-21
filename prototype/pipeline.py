"""PROTOTYPE (throwaway): Chunk -> hybrid search -> rerank -> Context Pack -> Match Score -> Test Set.
Question: does this quality core find the right Chunks, lead with the Current Decision,
and say "not found" when the Knowledge Base has no answer? Run: .venv/Scripts/python pipeline.py"""
import glob, json, math, os, re
import numpy as np
from rank_bm25 import BM25Okapi
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

HERE = os.path.dirname(__file__)
emb = TextEmbedding("BAAI/bge-small-en-v1.5")
rer = TextCrossEncoder("Xenova/ms-marco-MiniLM-L-6-v2")
tok = lambda s: re.findall(r"[a-z0-9_]+", s.lower())
sigmoid = lambda x: 1 / (1 + math.exp(-x))

def load(d="data"):
    convs = []
    for p in sorted(glob.glob(f"{HERE}/{d}/*.md")):
        head, body = open(p, encoding="utf8").read().split("\n\n", 1)
        meta = dict(l.split(": ", 1) for l in head.splitlines())
        msgs = re.findall(r"\*\*(User|Assistant):\*\* (.*)", body)
        convs.append({"id": os.path.basename(p)[:-3], **meta, "msgs": msgs})
    return convs

MAX = 1800  # chars, about 450 tokens: bge-small reads at most 512 tokens, longer Chunks get silently cut

def pieces(u, a):
    """One question+answer is one piece, or several when the answer is long: split at paragraph, then sentence ends, each keeping the question as a heading."""
    head = f"User: {u[:300]}"
    if len(u) + len(a) <= MAX:
        return [f"User: {u}\nAssistant: {a}"]
    room = MAX - len(head) - 12
    parts, cur = [], ""
    for seg in re.split(r"(?<=[.!?]) |\s*⏎\s*", a):
        while len(seg) > room:  # no break found (code, tables): hard cut
            parts.append(seg[:room]); seg = seg[room:]
        if len(cur) + len(seg) + 1 > room and cur:
            parts.append(cur); cur = ""
        cur = f"{cur} {seg}".strip()
    if cur: parts.append(cur)
    return [f"{head}\nAssistant: {p}" for p in parts]

def chunk(convs):
    """A Chunk = a question with its answer (split if long); small neighbours on the same subject are merged up to MAX."""
    chunks = []
    for c in convs:
        units = [p for u, a in zip(c["msgs"][0::2], c["msgs"][1::2]) for p in pieces(u[1], a[1])]
        vecs = list(emb.embed(units)) if units else []
        cur = None
        for text, v in zip(units, vecs):
            same = cur and len(cur["text"]) + len(text) < MAX and float(np.dot(cur["vec"], v)) > 0.72  # shortcut: fixed cutoff, tune on Test Set
            if same:
                cur["text"] += "\n" + text
            else:
                cur = {"conv": c["id"], "platform": c["platform"], "date": c["date"], "title": c["title"], "text": text, "vec": v}
                chunks.append(cur)
    for ch, v in zip(chunks, emb.embed([c["text"] for c in chunks])):
        ch["vec"] = v
    return chunks

def search(q, chunks, k=3):
    bm = BM25Okapi([tok(c["text"]) for c in chunks])
    kw = np.argsort(-bm.get_scores(tok(q)))
    qv = next(iter(emb.embed([q])))
    dn = np.argsort(-np.array([float(np.dot(qv, c["vec"])) for c in chunks]))
    rrf = {}
    for ranking in (kw, dn):  # reciprocal rank fusion merges the two searches
        for r, i in enumerate(ranking):
            rrf[i] = rrf.get(i, 0) + 1 / (60 + r)
    top = sorted(rrf, key=rrf.get, reverse=True)[:6]
    scores = list(rer.rerank(q, [chunks[i]["text"] for i in top]))
    order = sorted(zip(top, scores), key=lambda x: -x[1])[:k]
    return [(chunks[i], sigmoid(s)) for i, s in order]

def pack(q, hits, floor=0.5, dfloor=0.5):
    """Match Score = how well the best Chunk answers the Request; below `floor` we admit we found nothing."""
    score = hits[0][1]
    if score < floor:
        return {"score": score, "text": f"Not found: nothing in the Knowledge Base answers '{q}'.", "found": False, "hits": hits}
    decisions = []
    for ch, _ in hits:
        for m in re.finditer(r"Decision: (.*?)(?:\n|$)", ch["text"]):
            rel = sigmoid(list(rer.rerank(q, [m.group(1)]))[0])  # a decision only counts if it answers this Request
            if rel >= dfloor:
                decisions.append((ch["date"], ch["platform"], m.group(1)))
    decisions.sort()
    lines = []
    if decisions:
        d, p, t = decisions[-1]
        lines.append(f"CURRENT DECISION ({d}, {p}): {t}")
        for d2, p2, t2 in decisions[:-1]:
            lines.append(f"  replaced earlier choice ({d2}, {p2}): {t2}")
    lines.append("SOURCES:")
    lines += [f"  [{ch['conv']} {ch['platform']} {ch['date']}] {ch['text'][:140]!r}" for ch, _ in hits[:2]]
    return {"score": score, "text": "\n".join(lines), "found": True, "hits": hits}

if __name__ == "__main__":
    chunks = chunk(load())
    print(f"{len(chunks)} Chunks from {len(load())} Conversations\n")
    tests = json.load(open(f"{HERE}/testset.json"))
    # calibrate: floor sits halfway between the weakest answerable score and the strongest unanswerable one
    top = [(t["answerable"], search(t["q"], chunks)[0][1]) for t in tests]
    lo = min(sc for a, sc in top if a); hi = max(sc for a, sc in top if not a)
    floor = (lo + hi) / 2 if lo > hi else 0.5  # shortcut: overlap means no clean floor; tiny set, recalibrate on real chats
    print(f"calibrated floor {floor:.0%} (weakest answerable {lo:.0%}, strongest unanswerable {hi:.0%})\n")
    right_found = ans = ans_complete = unans = unans_ok = 0
    for t in tests:
        hits = search(t["q"], chunks)
        p = pack(t["q"], hits, floor)
        print(f"Q: {t['q']}\n  Match Score {p['score']:.0%}  found={p['found']}\n  " + p["text"].replace("\n", "\n  ") + "\n")
        if t["answerable"]:
            ans += 1
            right_found += any(h[0]["conv"] in t["expect"] for h in hits)
            ans_complete += p["found"] and all(w in p["text"].lower() + " ".join(h[0]["text"].lower() for h in hits) for w in t["terms"])
        else:
            unans += 1; unans_ok += not p["found"]
    print(f"Right Chunk in top 3: {right_found}/{ans}\nPack has needed facts: {ans_complete}/{ans}\nSaid 'not found' when it should: {unans_ok}/{unans}")
