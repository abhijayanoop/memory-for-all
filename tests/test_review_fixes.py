import pytest

from memoryforall import cli
from memoryforall.chunk import chunk
from memoryforall.kb import KnowledgeBase, parse, validate


def data(cid="c1", title="T", updated="2025-01-01T00:00:00Z", text="hello"):
    return {"platform": "claude", "chat_id": cid, "title": title, "created": "2025-01-01T00:00:00Z",
            "updated": updated, "messages": [{"sender": "user", "text": text}, {"sender": "assistant", "text": "r"}]}


def test_rename_keeps_chunks(tmp_path, fake):
    kb = KnowledgeBase(tmp_path, fake)
    kb.save(validate(data()))
    kb.refresh_index()
    assert kb.save(validate(data(title="New", updated="2025-02-01T00:00:00Z"))) == "renamed+updated"
    kb.refresh_index()
    assert len(kb.chunks()) > 0


@pytest.mark.parametrize("bad", ["a/b", "..", "a b", "a*", "é"])
def test_bad_chat_id_rejected(bad):
    with pytest.raises(ValueError, match="chat_id"):
        validate(data(cid=bad))


def test_suffix_id_does_not_collide(tmp_path, fake):
    kb = KnowledgeBase(tmp_path, fake)
    kb.save(validate(data(cid="x-1", title="same")))
    assert kb.save(validate(data(cid="1", title="same"))) == "created"
    assert len(kb.conversations()) == 2


def test_no_notes_heading_keeps_messages():
    text = '---\nplatform: claude\nchat_id: "c"\ntitle: "t"\ncreated: a\nupdated: b\n---\n\n### User\nhi\n\n'
    c, notes = parse(text)
    assert [m.text for m in c.messages] == ["hi"] and notes == ""


def test_long_title_chunks(fake):
    c = validate(data(title="x" * 5000, text="q" * 3000))
    assert chunk(c, "", fake)


def test_duplicate_files_dont_wipe_chunks(tmp_path, fake):
    kb = KnowledgeBase(tmp_path, fake)
    kb.save(validate(data()))
    p = next(tmp_path.rglob("*.md"))
    (p.parent / "copy.md").write_bytes(p.read_bytes())
    kb.refresh_index()
    n = len(kb.chunks())
    assert n > 0
    p.write_bytes(p.read_bytes() + b"more notes\n")
    kb.refresh_index()
    assert len(kb.chunks()) >= n


def test_corrupt_settings(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MEMORYFORALL_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text("{nope", encoding="utf-8")
    assert cli.main(["status"]) != 0
    assert "settings" in capsys.readouterr().err
