"""Re-ranker interface: name, rerank(request, texts) -> raw scores, higher is better."""


class FastReranker:
    name = "Xenova/ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        self._model = None  # loaded on first rerank so `status` stays instant

    def rerank(self, request, texts):
        if self._model is None:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            self._model = TextCrossEncoder(self.name)
        return [float(s) for s in self._model.rerank(request, texts)]
