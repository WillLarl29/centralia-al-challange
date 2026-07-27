import json
from pathlib import Path
from typing import Any

import numpy as np

from .base import SearchResult, VectorStoreProvider


class LocalNumpyVectorStore(VectorStoreProvider):
    """Vector store persistido en disco con numpy (sin infraestructura externa).

    Guarda `embeddings.npy` (matriz N x D) y `records.json` (id, texto y metadata
    por fila, en el mismo orden). Sirve para desarrollar y probar el RAG completo
    antes de conectar Oracle Autonomous Database 23ai (AI Vector Search) en
    producción, implementado en `oracle23ai.py` bajo la misma interfaz.
    """

    def __init__(self, storage_dir: Path):
        self._dir = storage_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._embeddings_path = self._dir / "embeddings.npy"
        self._records_path = self._dir / "records.json"

        self._ids: list[str] = []
        self._texts: list[str] = []
        self._metadatas: list[dict[str, Any]] = []
        self._embeddings: np.ndarray | None = None

        self._load()

    def _load(self) -> None:
        if self._records_path.exists() and self._embeddings_path.exists():
            records = json.loads(self._records_path.read_text(encoding="utf-8"))
            self._ids = records["ids"]
            self._texts = records["texts"]
            self._metadatas = records["metadatas"]
            self._embeddings = np.load(self._embeddings_path)

    def _persist(self) -> None:
        self._records_path.write_text(
            json.dumps({"ids": self._ids, "texts": self._texts, "metadatas": self._metadatas}, ensure_ascii=False),
            encoding="utf-8",
        )
        if self._embeddings is not None:
            np.save(self._embeddings_path, self._embeddings)

    def upsert(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        new_matrix = np.array(embeddings, dtype=np.float32)

        # Reemplaza registros existentes con el mismo id (idempotencia de la ingesta).
        existing_index = {chunk_id: i for i, chunk_id in enumerate(self._ids)}
        keep_mask = np.ones(len(self._ids), dtype=bool)
        for chunk_id in ids:
            if chunk_id in existing_index:
                keep_mask[existing_index[chunk_id]] = False

        if self._embeddings is not None and len(self._ids) > 0:
            self._ids = [cid for cid, keep in zip(self._ids, keep_mask) if keep]
            self._texts = [t for t, keep in zip(self._texts, keep_mask) if keep]
            self._metadatas = [m for m, keep in zip(self._metadatas, keep_mask) if keep]
            filtered = self._embeddings[keep_mask]
            self._embeddings = np.vstack([filtered, new_matrix]) if filtered.shape[0] else new_matrix
        else:
            self._embeddings = new_matrix

        self._ids.extend(ids)
        self._texts.extend(texts)
        self._metadatas.extend(metadatas)
        self._persist()

    def similarity_search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        if self._embeddings is None or len(self._ids) == 0:
            return []

        query = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query) or 1e-8
        matrix_norm = np.linalg.norm(self._embeddings, axis=1)
        matrix_norm[matrix_norm == 0] = 1e-8

        similarities = (self._embeddings @ query) / (matrix_norm * query_norm)
        top_indices = np.argsort(-similarities)[:top_k]

        return [
            SearchResult(
                id=self._ids[i],
                text=self._texts[i],
                metadata=self._metadatas[i],
                score=float(similarities[i]),
            )
            for i in top_indices
        ]

    def count(self) -> int:
        return len(self._ids)
