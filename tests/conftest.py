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
