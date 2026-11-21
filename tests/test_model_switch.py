import pytest

from conftest import FakeEmbedder
from memoryforall.cli import main
from memoryforall.embed import FastEmbedder, OpenAIEmbedder
from memoryforall.kb import KnowledgeBase
from test_search import conv, ids


class A(FakeEmbedder):
    name, used = "fake-a", []

    def embed(self, texts):
        A.used.append(texts)
        return super().embed(texts)


class B(FakeEmbedder):
    name, used = "fake-b", []

    def embed(self, texts):
        B.used.append(texts)
        return super().embed(texts)


class BrokenB(B):
    def embed(self, texts):
        raise RuntimeError("network down")


class KeylessA(A):
    def embed(self, texts):
        raise RuntimeError("needs a key")


TABLE = {A.name: A, B.name: B}


@pytest.fixture
def built(tmp_path):
    """A Knowledge Base whose live index was built with A."""
    kb = KnowledgeBase(tmp_path, A())
    kb.save(conv("a", "zebra stripes"))
    kb.save(conv("b", "fix the boat engine"))
    kb.refresh_index()
    A.used, B.used = [], []
    return tmp_path


def test_search_uses_live_model_until_refresh(built):
    kb = KnowledgeBase(built, B(), TABLE)
    assert kb.index_embedder() == A.name
    assert ids(kb.search("zebra"))[0] == "a"
    assert A.used == [["zebra"]] and not B.used
    kb.refresh_index()
    A.used, B.used = [], []
    assert kb.index_embedder() == B.name
    assert ids(kb.search("zebra"))[0] == "a"
    assert B.used == [["zebra"]] and not A.used


def test_failed_refresh_leaves_search_on_old_model(built):
    kb = KnowledgeBase(built, BrokenB(), TABLE)
    with pytest.raises(RuntimeError):
        kb.refresh_index()
    assert kb.index_embedder() == A.name
    assert ids(kb.search("zebra"))[0] == "a"
    assert A.used == [["zebra"]]


@pytest.mark.parametrize("table", [{B.name: B}, {A.name: KeylessA, B.name: B}], ids=["unknown", "no-key"])
def test_unusable_old_model_falls_back_to_keyword_only(built, table, capsys):
    kb = KnowledgeBase(built, B(), table)
    assert ids(kb.search("zebra")) == ["a"]  # keyword only: the boat Chunk has no shared word
    assert "keyword" in capsys.readouterr().err.lower()
    assert not B.used  # never embeds the Request with a model that does not match the index


def test_switching_back_before_refresh_means_nothing_pending(built):
    kb = KnowledgeBase(built, A(), TABLE)
    assert kb.index_embedder() == kb.embedder.name


# --- command line ---

class Local(FakeEmbedder):
    name = FastEmbedder.name


class Hosted(FakeEmbedder):
    name = OpenAIEmbedder.name


def test_cli_reports_pending_reembed_until_reindex(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MEMORYFORALL_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    fakes = {Local.name: Local, Hosted.name: Hosted}
    main(["set-kb", str(tmp_path / "kb")])
    KnowledgeBase(tmp_path / "kb", Local()).save(conv("a", "zebra stripes"))
    main(["reindex"], embedders=fakes)
    main(["mode", "search", "hosted"])
    capsys.readouterr()

    assert main(["search", "zebra"], embedders=fakes) == 0
    out = capsys.readouterr().out
    assert "re-embed pending" in out and Local.name in out and "1. a" in out
    assert main(["status"], embedders=fakes) == 0
    out = capsys.readouterr().out
    assert f"index model: {Local.name}" in out and "re-embed pending" in out

    main(["mode", "search", "local"])  # switching back cancels it
    capsys.readouterr()
    main(["status"], embedders=fakes)
    out = capsys.readouterr().out
    assert f"index model: {Local.name}" in out and "pending" not in out

    main(["mode", "search", "hosted"])
    main(["reindex"], embedders=fakes)
    capsys.readouterr()
    main(["search", "zebra"], embedders=fakes)
    main(["status"], embedders=fakes)
    out = capsys.readouterr().out
    assert "pending" not in out and f"index model: {Hosted.name}" in out
