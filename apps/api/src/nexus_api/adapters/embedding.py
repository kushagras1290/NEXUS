from __future__ import annotations

import asyncio
from functools import cached_property

from fastembed import TextEmbedding


class FastEmbedder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @cached_property
    def _model(self) -> TextEmbedding:
        return TextEmbedding(model_name=self.model_name)

    def _embed_sync(self, text: str) -> list[float]:
        vectors = list(self._model.embed([text]))
        if not vectors:
            raise RuntimeError("Embedding model returned no vector")
        return vectors[0].astype(float).tolist()

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_sync, text)

    def embed_batch_sync(self, texts: list[str]) -> list[list[float]]:
        return [vector.astype(float).tolist() for vector in self._model.embed(texts)]
