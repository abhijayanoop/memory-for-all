import hashlib
import math

import pytest


class FakeEmbedder:
    name, dimension = "fake", 8

    def embed(self, texts):
        out = []
        for t in texts:
            v = [b - 127.5 for b in hashlib.sha256(t.encode()).digest()[: self.dimension]]
            n = math.sqrt(sum(x * x for x in v))
            out.append([x / n for x in v])
        return out


@pytest.fixture
def fake():
    return FakeEmbedder()


class KeepOrderReranker:
    """Scores texts by position, so the fused order is kept."""
    name = "keep-order"

    def rerank(self, request, texts):
        return [float(len(texts) - n) for n in range(len(texts))]


@pytest.fixture(autouse=True)
def fake_reranker(request, monkeypatch):
    # the default KnowledgeBase re-ranker would load the real model; slow tests keep it
    if not request.node.get_closest_marker("slow"):
        from memoryforall import rerank
        monkeypatch.setattr(rerank, "FastReranker", KeepOrderReranker)
