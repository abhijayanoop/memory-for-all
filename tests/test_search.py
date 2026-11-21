import sqlite3

import pytest

from memoryforall import kb as kbmod
from memoryforall.cli import main
from memoryforall.kb import KnowledgeBase, render, validate


def conv(cid, *texts, title=None):
    msgs = []
    for t in texts:
        msgs += [{"sender": "user", "text": t}, {"sender": "assistant", "text": "ok"}]
    return validate({"platform": "claude", "chat_id": cid, "title": title or cid, "created": "2025-01-01T00:00:00Z",
                     "updated": "2025-01-01T00:00:00Z", "messages": msgs})


def make(tmp_path, fake, convs):
    kb = KnowledgeBase(tmp_path, fake)
    for c in convs:
        kb.save(c)
    kb.refresh_index()
    return kb


def ids(hits):
    return [h.chunk.chat_id for h in hits]


class TableEmbedder:
    """First rule whose word is in the text gives the vector; otherwise [0, 1]."""
    name, dimension = "table", 2
    rules = [("mixed", [0.6, 0.8]), ("purr", [1.0, 0.0]), ("kitten", [1.0, 0.0]), ("feline", [1.0, 0.0])]

    def embed(self, texts):
        return [next((v for w, v in self.rules if w in t), [0.0, 1.0]) for t in texts]


def test_no_shared_words_finds_meaning_match(tmp_path):
    kb = make(tmp_path, TableEmbedder(), [conv("a", "fix the boat engine"), conv("b", "my pet likes to purr")])
    assert ids(kb.search("feline"))[0] == "b"


def test_exact_word_found_even_when_vectors_unrelated(tmp_path):
    kb = make(tmp_path, TableEmbedder(), [conv(f"p{i}", f"purr number {i}") for i in range(8)]
              + [conv("d", "fix the docker compose file")])
    assert ids(kb.search("kitten docker"))[0] == "d"


def test_chunk_in_both_lists_outranks_one_list(tmp_path):
    # meaning order: b (exact vector), a, c; keyword: only a
    kb = make(tmp_path, TableEmbedder(), [conv("a", "mixed kitten"), conv("b", "purr"), conv("c", "boat")])
    assert ids(kb.search("kitten")) == ["a", "b", "c"]


def test_refresh_changes_seen_by_meaning_side(tmp_path):
    kb = make(tmp_path, TableEmbedder(), [conv("a", "purr"), conv("b", "purr too"), conv("x", "boat")])
    next(tmp_path.rglob("*-a.md")).write_bytes(render(conv("a", "engine")).encode())  # changed
    next(tmp_path.rglob("*-b.md")).unlink()  # removed
    kb.save(conv("c", "purr again"))  # added
    kb.refresh_index()
    got = ids(kb.search("feline"))
    assert got[0] == "c" and "b" not in got and sorted(got) == ["a", "c", "x"]


def test_exact_word_finds_its_chunk(tmp_path, fake):
    kb = make(tmp_path, fake, [conv("a", "how do I bake sourdough"), conv("b", "fix the docker compose file")])
    hits = kb.search("docker")
    assert ids(hits)[0] == "b"
    assert hits[0].rank == 1 and "docker compose" in hits[0].chunk.text


def test_k_limits(tmp_path, fake):
    kb = make(tmp_path, fake, [conv("a", "zebra apple"), conv("b", "zebra zebra zebra mango"), conv("c", "zebra pear")])
    assert len(kb.search("zebra", k=2)) == 2
    assert sorted(ids(kb.search("zebra", k=50))) == ["a", "b", "c"]
    assert [h.rank for h in kb.search("zebra", k=50)] == [1, 2, 3]


def test_default_k_is_five(tmp_path, fake):
    kb = make(tmp_path, fake, [conv(f"c{i}", f"shared word {i}") for i in range(7)])
    assert len(kb.search("shared")) == 5


@pytest.mark.parametrize("request_text", ['"unbalanced', "zebra*", "-zebra", "col:zebra", "zebra AND", "NEAR(zebra",
                                          "(zebra) [x] {y}", "zebra 🦓", "🦓", "AND OR NOT", "'; drop table chunks;--"])
def test_odd_requests_never_error(tmp_path, fake, request_text):
    kb = make(tmp_path, fake, [conv("a", "zebra stripes")])
    hits = kb.search(request_text)
    if "zebra" in request_text:
        assert ids(hits) == ["a"]


@pytest.mark.parametrize("request_text", ["", "   ", "\n\t"])
def test_empty_request_rejected(tmp_path, fake, request_text):
    kb = make(tmp_path, fake, [conv("a", "zebra")])
    with pytest.raises(ValueError, match="empty"):
        kb.search(request_text)


def test_missing_or_empty_index_returns_nothing(tmp_path, fake):
    kb = KnowledgeBase(tmp_path, fake)
    assert kb.search("zebra") == []
    kb.refresh_index()
    assert kb.search("zebra") == []


def test_notes_are_searchable_and_marked(tmp_path, fake):
    kb = KnowledgeBase(tmp_path, fake)
    kb.save(conv("a", "something else"))
    p = next(tmp_path.rglob("*.md"))
    p.write_bytes(p.read_bytes() + b"remember the giraffe password\n")
    kb.refresh_index()
    hits = kb.search("giraffe")
    assert hits[0].chunk.kind == "notes"


def test_refresh_keeps_keyword_index_in_step(tmp_path, fake):
    kb = make(tmp_path, fake, [conv("a", "alpha topic"), conv("b", "beta topic")])
    pa = next(tmp_path.rglob("*-a.md"))
    pb = next(tmp_path.rglob("*-b.md"))
    pa.write_bytes(render(conv("a", "gamma topic")).encode())  # changed
    pb.unlink()  # removed
    kb.save(conv("c", "delta topic"))  # added
    kb.refresh_index()
    texts = " ".join(h.chunk.text for h in kb.search("alpha beta", k=50))
    assert "alpha" not in texts and "beta" not in texts
    assert ids(kb.search("gamma"))[0] == "a" and ids(kb.search("delta"))[0] == "c"
    assert sorted(ids(kb.search("topic"))) == ["a", "c"]


def test_spec1_index_is_rebuilt_and_searchable(tmp_path, fake, monkeypatch):
    monkeypatch.setattr(kbmod, "RULES_VERSION", 2)
    kb = KnowledgeBase(tmp_path, fake)
    kb.save(conv("a", "zebra"))
    kb.refresh_index()
    db = sqlite3.connect(kb.index_path)  # make it look like a spec-1 index: no keyword table
    db.execute("drop table if exists chunks_fts")
    db.commit()
    db.close()
    monkeypatch.undo()
    assert ids(kb.search("zebra")) == ["a"]  # meaning side still works without the keyword table
    kb.refresh_index()
    assert ids(kb.search("zebra")) == ["a"]


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYFORALL_CONFIG_DIR", str(tmp_path / "cfg"))
    return tmp_path


def test_cli_search_prints_hits(cfg, fake, capsys):
    kbdir = cfg / "kb"
    KnowledgeBase(kbdir, fake).save(conv("a", "zebra stripes " + "x" * 400, title="Animal chat"))
    main(["reindex", "--kb", str(kbdir)], embedder=fake)
    capsys.readouterr()
    assert main(["search", "zebra", "-k", "3", "--kb", str(kbdir)], embedder=fake) == 0
    out = capsys.readouterr().out
    assert "1. Animal chat" in out and "claude" in out and "2025-01-01" in out and "claude:a:0" in out
    assert "zebra stripes" in out and "x" * 400 not in out
    assert "score 1.000" in out  # the conftest re-ranker scores the only hit 1


def test_cli_search_empty_index_says_reindex(cfg, fake, capsys):
    assert main(["search", "zebra", "--kb", str(cfg / "kb")], embedder=fake) == 0
    assert "reindex" in capsys.readouterr().out


def test_cli_search_empty_request(cfg, fake, capsys):
    assert main(["search", "  ", "--kb", str(cfg / "kb")], embedder=fake) == 2
    assert "empty" in capsys.readouterr().err.lower()


class ReverseReranker:
    """Scores later texts higher, so the re-ranked order is the reverse of the fused order."""
    name = "reverse"

    def rerank(self, request, texts):
        return [float(n) for n in range(len(texts))]


def test_reranker_order_decides_final_order(tmp_path):
    kb = KnowledgeBase(tmp_path, TableEmbedder(), ReverseReranker())
    for c in [conv("a", "mixed kitten"), conv("b", "purr"), conv("c", "boat")]:
        kb.save(c)
    kb.refresh_index()
    # fused order is a, b, c (see test_chunk_in_both_lists_outranks_one_list)
    hits = kb.search("kitten", k=2)
    assert ids(hits) == ["c", "b"]
    assert [h.rank for h in hits] == [1, 2] and [h.score for h in hits] == [2.0, 1.0]


@pytest.mark.slow
def test_real_reranker_prefers_relevant_text():
    from memoryforall.rerank import FastReranker
    s = FastReranker().rerank("how do I bake sourdough bread",
                              ["Feed the starter, then proof the dough overnight before baking.", "The docker compose file failed."])
    assert s[0] > s[1]


@pytest.mark.slow
def test_real_local_models_search_end_to_end(tmp_path):
    kb = KnowledgeBase(tmp_path)
    for c in [conv("bread", "how long should sourdough proof"), conv("car", "the car engine makes a noise"),
              conv("trip", "where to stay in Lisbon")]:
        kb.save(c)
    kb.refresh_index()
    hits = kb.search("baking bread at home", k=2)
    assert ids(hits)[0] == "bread" and len(hits) == 2 and hits[0].score > hits[1].score
