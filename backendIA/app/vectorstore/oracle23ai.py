import json
from typing import Any

from app.core.config import Settings

from .base import SearchResult, VectorStoreProvider

_TABLE_NAME = "CENTRALIA_CHUNKS"

_CREATE_TABLE_SQL = f"""
CREATE TABLE {_TABLE_NAME} (
    id           VARCHAR2(64) PRIMARY KEY,
    text         CLOB NOT NULL,
    metadata     JSON,
    embedding    VECTOR
)
"""

_UPSERT_SQL = f"""
MERGE INTO {_TABLE_NAME} t
USING (SELECT :id AS id FROM dual) s
ON (t.id = s.id)
WHEN MATCHED THEN UPDATE SET
    t.text = :text, t.metadata = :metadata, t.embedding = :embedding
WHEN NOT MATCHED THEN INSERT (id, text, metadata, embedding)
    VALUES (:id, :text, :metadata, :embedding)
"""

_SEARCH_SQL = f"""
SELECT id, text, metadata,
       VECTOR_DISTANCE(embedding, :query_vector, COSINE) AS distance
FROM {_TABLE_NAME}
ORDER BY distance
FETCH FIRST :top_k ROWS ONLY
"""


class Oracle23aiVectorStore(VectorStoreProvider):
    """Vector store de producción sobre Oracle Autonomous Database 23ai (AI Vector Search).

    Requiere: wallet de conexión descargado desde OCI, y las variables
    ORACLE_DB_* configuradas en `.env`. Antes del primer uso, ejecutar
    `_CREATE_TABLE_SQL` una vez (ver `scripts/setup_oracle_schema.py`).
    """

    def __init__(self, settings: Settings):
        import oracledb  # import perezoso: evita requerir el driver si no se usa este provider

        self._oracledb = oracledb
        self._pool = oracledb.create_pool(
            user=settings.oracle_db_user,
            password=settings.oracle_db_password,
            dsn=settings.oracle_db_dsn,
            config_dir=settings.oracle_db_wallet_location,
            wallet_location=settings.oracle_db_wallet_location,
            wallet_password=settings.oracle_db_wallet_password,
            min=1,
            max=4,
            increment=1,
        )

    def upsert(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        rows = [
            {
                "id": chunk_id,
                "text": text,
                "metadata": json.dumps(metadata, ensure_ascii=False),
                "embedding": embedding,
            }
            for chunk_id, text, metadata, embedding in zip(ids, texts, metadatas, embeddings)
        ]
        with self._pool.acquire() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(_UPSERT_SQL, rows)
            connection.commit()

    def similarity_search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        with self._pool.acquire() as connection:
            with connection.cursor() as cursor:
                cursor.execute(_SEARCH_SQL, query_vector=query_embedding, top_k=top_k)
                rows = cursor.fetchall()

        results: list[SearchResult] = []
        for chunk_id, text, metadata_raw, distance in rows:
            metadata = json.loads(metadata_raw) if metadata_raw else {}
            clob_text = text.read() if hasattr(text, "read") else text
            # COSINE distance: 0 = idéntico, 2 = opuesto -> similitud = 1 - distancia
            results.append(SearchResult(id=chunk_id, text=clob_text, metadata=metadata, score=1 - float(distance)))
        return results

    def count(self) -> int:
        with self._pool.acquire() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {_TABLE_NAME}")
                (total,) = cursor.fetchone()
        return int(total)
