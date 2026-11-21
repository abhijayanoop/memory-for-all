"""Embedder interface: name, dimension, embed(texts) -> unit-length vectors."""
import json
import math
import os
import time
import urllib.error
from urllib.request import Request, urlopen

KEYS = {"openai": "OPENAI_API_KEY", "claude": "ANTHROPIC_API_KEY"}  # provider -> key's environment variable


class FastEmbedder:
    name, dimension = "BAAI/bge-small-en-v1.5", 384

    def __init__(self):
        self._model = None  # loaded on first embed so `status` stays instant

    def embed(self, texts):
        if self._model is None:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(self.name)
        # bge outputs are already L2-normalised
        return [v.tolist() for v in self._model.embed(texts)]


class OpenAIEmbedder:
    """Hosted search: sends Chunk and Request text to OpenAI. The key is read from OPENAI_API_KEY at embed time."""
    name, dimension = "text-embedding-3-small", 1536
    batch, retries = 100, 6  # 100 Chunks of <=1,800 chars stays far under the per-request token cap

    def embed(self, texts):
        key = os.environ.get(KEYS["openai"])
        if not key:
            raise RuntimeError(f"Hosted search needs {KEYS['openai']} in the environment.")
        out = []
        for i in range(0, len(texts), self.batch):
            data = sorted(self._post(key, texts[i:i + self.batch]), key=lambda d: d["index"])
            for d in data:
                n = math.sqrt(sum(x * x for x in d["embedding"]))
                out.append([x / n for x in d["embedding"]])
        return out

    def _post(self, key, texts):
        req = Request("https://api.openai.com/v1/embeddings",
                      json.dumps({"model": self.name, "input": texts}).encode(),
                      {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        for attempt in range(self.retries + 1):
            try:
                with urlopen(req, timeout=60) as r:
                    return json.loads(r.read())["data"]
            except urllib.error.HTTPError as e:
                if e.code == 429 and b"insufficient_quota" in e.read():  # retrying cannot help; body never shown
                    raise RuntimeError(f"OpenAI says the account is out of quota (HTTP 429); check billing for "
                                       f"the key in {KEYS['openai']}.") from None
                if e.code == 429 and attempt < self.retries:
                    time.sleep(float(e.headers.get("Retry-After") or 2 ** attempt))
                    continue
                if e.code == 401:
                    raise RuntimeError(f"OpenAI rejected the key in {KEYS['openai']} (HTTP 401); check it.") from None
                # the response body is not shown: OpenAI echoes part of the key in it
                raise RuntimeError(f"OpenAI embeddings request failed: HTTP {e.code} {e.reason}") from None
            except urllib.error.URLError as e:
                raise RuntimeError(f"Could not reach OpenAI: {e.reason}") from None


# Fixed lookup from embedder name (as stored in the index's meta) to constructor.
EMBEDDERS = {FastEmbedder.name: FastEmbedder, OpenAIEmbedder.name: OpenAIEmbedder}
# Which embedder each search Mode targets.
SEARCH_EMBEDDER = {"local": FastEmbedder.name, "hosted": OpenAIEmbedder.name}
