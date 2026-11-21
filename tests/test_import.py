import json

from memoryforall.cli import main
from memoryforall.kb import KnowledgeBase, parse, render, validate


def conv(**kw):
    d = {"platform": "claude", "chat_id": "abc", "title": "Why? A: B/C", "created": "2026-10-02T11:14:00+02:00",
         "updated": "2026-10-03T00:00:00Z",
         "messages": [
             {"sender": "user", "time": "2026-10-02T09:14:00Z", "text": "hi\n```\n### User · x\n```\n## Not notes 😀", "attachments": ["r.pdf"]},
             {"sender": "assistant", "time": None, "text": "", "attachments": []},
             {"sender": "assistant", "time": None, "text": "ok", "attachments": []}]}
    d.update(kw)
    return d


def test_import_writes_file_and_status(tmp_path, capsys):
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
    main(["status", "--kb", str(kb)])
    assert capsys.readouterr().out.split() == ["chatgpt:", "0", "claude:", "1"]


def test_round_trip_and_notes_kept(tmp_path):
    c = validate(conv(title='a<>:"/\\|?*b ' + "x" * 80 + "..."))
    kb = KnowledgeBase(tmp_path)
    assert kb.save(c) == "created"
    assert kb.conversations() == [c]
    assert kb.save(c) == "unchanged"
    p = next(tmp_path.rglob("*.md"))
    assert len(p.name) < 100 and not any(ch in p.name for ch in '<>:"|?*')
    p.write_text(p.read_text(encoding="utf-8") + "my note\n", encoding="utf-8")
    c.updated = "2027-01-01T00:00:00Z"
    assert kb.save(c) == "updated"
    assert p.read_text(encoding="utf-8").endswith("## My notes\nmy note\n")


def test_empty_conversation_round_trip():
    c = validate(conv(messages=[]))
    assert parse(render(c)) == (c, "")
