"""Embedder interface: name, dimension, embed(texts) -> unit-length vectors."""


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
