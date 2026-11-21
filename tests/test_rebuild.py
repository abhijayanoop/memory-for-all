import sqlite3

import pytest

from memoryforall import kb as kbmod
from memoryforall.kb import KnowledgeBase, validate


def conv(i):
    return validate({"platform": "claude", "chat_id": f"c{i}", "title": f"T{i}", "created": "2025-01-01T00:00:00Z",
                     "updated": "2025-01-01T00:00:00Z",
                     "messages": [{"sender": "user", "text": f"hello {i}"}, {"sender": "assistant", "text": "reply"}]})


def built(tmp_path, fake):
    kb = KnowledgeBase(tmp_path, fake)
    for i in range(2):
        kb.save(conv(i))
    kb.refresh_index()
    return kb


def snapshot(kb):
    return [(c.id, c.text, c.kind, c.title, c.date) for c in kb.chunks()]


def add_marker(kb):
    db = sqlite3.connect(kb.index_path)
    db.execute("insert into chunks values ('marker','x','claude','zz','t','d',0,'stale',x'')")
    db.commit()
    db.close()


def has_marker(kb):
    return any(c.id == "marker" for c in kb.chunks())


def test_deleted_index_folder_rebuilds_same_chunks(tmp_path, fake):
    kb = built(tmp_path, fake)
    before = snapshot(kb)
    kb.index_path.unlink()
    kb.index_path.parent.rmdir()
    kb.refresh_index()
    assert snapshot(kb) == before and before


def test_unreadable_index_rebuilds(tmp_path, fake):
    kb = built(tmp_path, fake)
    before = snapshot(kb)
    kb.index_path.write_bytes(b"not a database" * 100)
    kb.refresh_index()
    assert snapshot(kb) == before


@pytest.mark.parametrize("attr,value", [("name", "other"), ("dimension", 9), ("RULES_VERSION", 99)])
def test_changed_settings_rebuild(tmp_path, fake, monkeypatch, attr, value):
    kb = built(tmp_path, fake)
    add_marker(kb)
    monkeypatch.setattr(kbmod if attr == "RULES_VERSION" else fake, attr, value)
    kb.refresh_index()
    assert not has_marker(kb)


def test_same_settings_refresh_in_place(tmp_path, fake):
    kb = built(tmp_path, fake)
    add_marker(kb)
    kb.refresh_index()
    assert has_marker(kb)


def test_interrupted_rebuild_keeps_old_index(tmp_path, fake, monkeypatch):
    kb = built(tmp_path, fake)
    before = snapshot(kb)
    monkeypatch.setattr(kbmod, "RULES_VERSION", 99)
    monkeypatch.setattr(fake, "embed", lambda texts: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        kb.refresh_index()
    assert snapshot(kb) == before
