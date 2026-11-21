import json

from memoryforall.cli import main
from memoryforall.kb import KnowledgeBase, parse, render, validate


def conv(**kw):
    d = {"platform": "claude", "chat_id": "abc", "title": "Why? A: B/C", "created": "2026-10-02T11:14:00+02:00",
         "updated": "2026-10-03T00:00:00Z",
         "messages": [
             {"sender": "user", "time": "2026-10-02T09:14:00Z", "text": "hi\n```\n### User x\n#### User · x\n```\n## Not notes 😀", "attachments": ["r.pdf"]},
             {"sender": "assistant", "time": None, "text": "", "attachments": []},
             {"sender": "assistant", "time": None, "text": "ok", "attachments": []}]}
    d.update(kw)
    return d


def test_import_writes_file_and_status(tmp_path, capsys, fake):
    src, kb = tmp_path / "src", tmp_path / "kb"
    src.mkdir()
    (src / "a.json").write_text(json.dumps(conv(title=None)))
    (src / "b.json").write_text(json.dumps(conv(chat_id="")))
    (src / "c.json").write_text("{nope")
    assert main(["import", str(src), "--kb", str(kb)]) == 0
    assert "created: 1, updated: 0, unchanged: 0, rejected: 2" in capsys.readouterr().out
    f = kb / "claude" / "2026-10" / "2026-10-02-untitled-abc.md"
    text = f.read_text(encoding="utf-8")
    assert text.startswith("---\nplatform: claude\n") and "status: on platform" in text
    assert "### User · 2026-10-02T09:14:00Z\n" in text and "attachment: r.pdf (not saved)" in text
    assert text.endswith("## My notes\n") and text.count("### Assistant") == 1
    (kb / "claude" / "plain.md").write_text("# just a note\n")
    main(["status", "--kb", str(kb)], embedder=fake)
    assert capsys.readouterr().out.split()[:4] == ["chatgpt:", "0", "claude:", "1"]


def test_round_trip_and_notes_kept(tmp_path, fake):
    c = validate(conv(title='a<>:"/\\|?*b ' + "x" * 80 + "..."))
    kb = KnowledgeBase(tmp_path, fake)
    assert kb.save(c) == "created"
    assert kb.conversations() == [c]
    assert kb.save(c) == "unchanged"
    p = next(tmp_path.rglob("*.md"))
    assert len(p.name) < 100 and not any(ch in p.name for ch in '<>:"|?*')
    p.write_text(p.read_text(encoding="utf-8") + "my note\n", encoding="utf-8")
    c.updated = "2027-01-01T00:00:00Z"
    assert kb.save(c) == "updated"
    assert p.read_text(encoding="utf-8").endswith("## My notes\nmy note\n")


def test_resave_rename_and_older_unchanged(tmp_path):
    kb = KnowledgeBase(tmp_path)
    kb.save(validate(conv()))
    p = next(tmp_path.rglob("*.md"))
    p.write_text(p.read_text(encoding="utf-8") + "mine\n", encoding="utf-8")
    before = p.read_bytes()
    assert kb.save(validate(conv(updated="2026-10-01T00:00:00Z", title="other"))) == "unchanged"
    assert p.read_bytes() == before
    r = validate(conv(title="New title", created="2026-11-05T00:00:00Z", updated="2026-12-01T00:00:00Z"))
    assert kb.save(r) == "renamed+updated"
    (q,) = tmp_path.rglob("*.md")
    assert q.name == "2026-11-05-New-title-abc.md" and q.read_text(encoding="utf-8").endswith("## My notes\nmine\n")
    r.updated = "2026-12-02T00:00:00Z"
    assert kb.save(r) == "updated"


def test_mark_gone_and_present_keep_notes(tmp_path):
    kb = KnowledgeBase(tmp_path)
    kb.save(validate(conv()))
    p = next(tmp_path.rglob("*.md"))
    p.write_text(p.read_text(encoding="utf-8") + "mine\n", encoding="utf-8")
    orig = p.read_text(encoding="utf-8")
    kb.mark_gone("claude", "abc", "2026-11-01T00:00:00Z")
    t = p.read_text(encoding="utf-8")
    assert "status: no longer on the Platform\ngone_since: 2026-11-01T00:00:00Z\n" in t and t.endswith("mine\n")
    kb.mark_present("claude", "abc")
    assert p.read_text(encoding="utf-8") == orig


def test_failed_rewrite_leaves_previous_file(tmp_path, monkeypatch):
    kb = KnowledgeBase(tmp_path)
    c = validate(conv())
    kb.save(c)
    p = next(tmp_path.rglob("*.md"))
    before = p.read_bytes()

    def boom(*a):
        raise OSError("disk")
    monkeypatch.setattr("memoryforall.kb.os.replace", boom)
    c.updated = "2027-01-01T00:00:00Z"
    try:
        kb.save(c)
    except OSError:
        pass
    assert p.read_bytes() == before and list(tmp_path.rglob("*.tmp")) == []


def test_empty_conversation_round_trip():
    c = validate(conv(messages=[]))
    assert parse(render(c)) == (c, "")
