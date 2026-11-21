import json
import math

import pytest

from memoryforall.chunk import chunk
from memoryforall.cli import main
from memoryforall.kb import Conversation, KnowledgeBase, Message


def conv(msgs, **kw):
    d = dict(platform="claude", chat_id="abc", title="Trip", created="2026-10-02T00:00:00Z",
             updated="2026-10-03T00:00:00Z", messages=[Message(s, t, x) for s, t, x in msgs])
    d.update(kw)
    return Conversation(**d)


def test_units_and_labels(fake):
    c = conv([("assistant", None, "welcome"),
              ("user", "2026-10-02T09:00:00Z", "q1"), ("assistant", None, "a1"), ("assistant", None, "a2"),
              ("user", None, "q2")])
    cs = chunk(c, "", fake)
    assert [x.text for x in cs] == [
        "Chat: Trip\nAssistant: welcome",
        "Chat: Trip\nUser: q1\nAssistant: a1\nAssistant: a2",
        "Chat: Trip\nUser: q2"]
    assert [x.id for x in cs] == ["claude:abc:0", "claude:abc:1", "claude:abc:2"]
    assert [x.date for x in cs] == ["2026-10-03T00:00:00Z", "2026-10-02T09:00:00Z", "2026-10-03T00:00:00Z"]
    assert cs[1].kind == "exchange" and cs[1].platform == "claude" and cs[1].title == "Trip"
    assert cs[1].position == 1 and cs[1].vector == fake.embed([cs[1].text])[0]


def test_cap_never_exceeded(fake):
    cs = chunk(conv([("user", None, "q" * 2500), ("assistant", None, "a" * 5000)]), "", fake)
    assert len(cs) > 1 and all(len(x.text) <= 1800 and x.text.startswith("Chat: Trip\n") for x in cs)


def test_kb_reindex_and_cli_smoke(tmp_path, capsys, fake):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.json").write_text(json.dumps({
        "platform": "chatgpt", "chat_id": "x1", "title": "T", "created": "2026-10-02T00:00:00Z",
        "updated": "2026-10-02T00:00:00Z",
        "messages": [{"sender": "user", "text": "hi"}, {"sender": "assistant", "text": "yo"},
                     {"sender": "user", "text": "bye"}]}))
    kb = tmp_path / "kb"
    assert main(["import", str(src), "--kb", str(kb)], embedder=fake) == 0
    assert main(["status", "--kb", str(kb)], embedder=fake) == 0
    assert "chunks: 0" in capsys.readouterr().out
    assert main(["reindex", "--kb", str(kb)], embedder=fake) == 0
    assert "chunks: 2" in capsys.readouterr().out
    assert main(["status", "--kb", str(kb)], embedder=fake) == 0
    out = capsys.readouterr().out
    assert "chunks: 2" in out and "last refreshed: 20" in out
    cs = KnowledgeBase(kb, fake).chunks()
    assert [c.id for c in cs] == ["chatgpt:x1:0", "chatgpt:x1:1"]
    assert cs[0].vector == pytest.approx(fake.embed([cs[0].text])[0], abs=1e-6)


@pytest.mark.slow
def test_real_model():
    from memoryforall.embed import FastEmbedder
    e = FastEmbedder()
    cs = chunk(conv([("user", None, "Where should we stay in Lisbon?"), ("assistant", None, "Alfama.")]), "", e)
    assert e.dimension == 384 and len(cs) == 1 and len(cs[0].vector) == 384
    assert math.isclose(sum(x * x for x in cs[0].vector), 1, abs_tol=1e-3)
