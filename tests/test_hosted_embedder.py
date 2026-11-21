import io
import json
import math
import urllib.error

import pytest

from conftest import FakeEmbedder
from memoryforall import embed
from memoryforall.cli import main
from memoryforall.embed import EMBEDDERS, FastEmbedder, OpenAIEmbedder
from memoryforall.kb import KnowledgeBase
from test_import import conv


class FakeOpenAI:
    """Stands in for urlopen: records each request and replies from a queue of status codes."""

    def __init__(self, statuses=()):
        self.statuses, self.requests = list(statuses), []

    def __call__(self, req, timeout=None):
        body = json.loads(req.data)
        self.requests.append((req, body))
        status = self.statuses.pop(0) if self.statuses else 200
        if status != 200:
            raise urllib.error.HTTPError(req.full_url, status, "err", {"Retry-After": "0"},
                                         io.BytesIO(b'{"error": {"message": "Incorrect API key provided: sk-sec***"}}'))
        # unnormalised, out of order, to check the embedder fixes both
        data = [{"index": i, "embedding": [3.0 * (len(t) + 1), 4.0 * (len(t) + 1)] + [0.0] * 1534}
                for i, t in enumerate(body["input"])][::-1]
        return io.BytesIO(json.dumps({"data": data}).encode())


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    monkeypatch.setattr(embed.time, "sleep", lambda s: None)
    fake = FakeOpenAI()
    monkeypatch.setattr(embed, "urlopen", fake)
    return fake


def test_embeds_in_batches_returning_unit_vectors_in_order(http):
    e = OpenAIEmbedder()
    texts = [f"text {i}" * (i + 1) for i in range(250)]
    out = e.embed(texts)
    assert (e.name, e.dimension) == ("text-embedding-3-small", 1536)
    assert [len(b["input"]) for _, b in http.requests] == [100, 100, 50]
    assert all(b["model"] == "text-embedding-3-small" for _, b in http.requests)
    assert http.requests[0][0].get_header("Authorization") == "Bearer sk-secret-value"
    assert len(out) == 250 and all(len(v) == 1536 for v in out)
    assert all(math.isclose(math.hypot(*v), 1.0) for v in out)
    assert out[0][:2] == pytest.approx([0.6, 0.8])


def test_rate_limit_is_retried(http):
    http.statuses = [429, 429]
    assert len(OpenAIEmbedder().embed(["a", "b"])) == 2
    assert len(http.requests) == 3


def test_bad_key_raises_clear_error_without_key(http):
    http.statuses = [401]
    with pytest.raises(RuntimeError) as e:
        OpenAIEmbedder().embed(["a"])
    assert "OPENAI_API_KEY" in str(e.value) and "sk-sec" not in str(e.value)


def test_missing_key_raises_clear_error(http, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAIEmbedder().embed(["a"])
    assert http.requests == []


def test_other_http_errors_raise_clear_error(http):
    http.statuses = [500]
    with pytest.raises(RuntimeError, match="500"):
        OpenAIEmbedder().embed(["a"])


def test_lookup_table_maps_names_to_the_two_real_embedders():
    assert EMBEDDERS == {"BAAI/bge-small-en-v1.5": FastEmbedder, "text-embedding-3-small": OpenAIEmbedder}


# --- command line: the target embedder follows the saved search Mode ---

class FakeLocal(FakeEmbedder):
    name, used = FastEmbedder.name, []

    def embed(self, texts):
        self.used.append(len(texts))
        return super().embed(texts)


class FakeHosted(FakeLocal):
    name, used = OpenAIEmbedder.name, []


@pytest.fixture
def kb(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYFORALL_CONFIG_DIR", str(tmp_path / "cfg"))
    FakeLocal.used, FakeHosted.used = [], []
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.json").write_text(json.dumps(conv()))
    main(["set-kb", str(tmp_path / "kb")])
    main(["import", str(src)], embedder=FakeLocal())
    return tmp_path / "kb"


def test_reindex_embeds_with_the_saved_search_mode(kb, http, capsys):
    fakes = {FakeLocal.name: FakeLocal, FakeHosted.name: FakeHosted}
    assert main(["reindex"], embedders=fakes) == 0
    assert FakeLocal.used and not FakeHosted.used
    main(["mode", "search", "hosted"])
    assert main(["reindex"], embedders=fakes) == 0
    assert FakeHosted.used
    assert capsys.readouterr().out.splitlines()[-1].startswith("added: 1")  # full re-embed


def test_failed_hosted_rebuild_leaves_old_index_live(kb, http, capsys):
    main(["reindex"], embedders={FakeLocal.name: FakeLocal})
    before = KnowledgeBase(kb, FakeLocal()).chunks()
    assert before
    main(["mode", "search", "hosted"])
    http.statuses = [401]
    capsys.readouterr()
    assert main(["reindex"]) == 1
    err = capsys.readouterr().err
    assert "OPENAI_API_KEY" in err and "sk-secret-value" not in err and "Traceback" not in err
    assert KnowledgeBase(kb, FakeLocal()).chunks() == before
    main(["mode", "search", "local"])
    assert main(["reindex"], embedders={FakeLocal.name: FakeLocal}) == 0
    assert capsys.readouterr().out.splitlines()[-1].startswith("added: 0")  # old index still current
