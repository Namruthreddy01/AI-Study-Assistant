import json
from pathlib import Path

import numpy as np

from app.services.chunking import TextChunk

try:
    import faiss
except ImportError:  # pragma: no cover - depends on installation platform
    faiss = None


class VectorStore:
    """Persistent per-document vector storage, backed by FAISS when available."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _vectors_file(self, document_id: str) -> Path:
        return self.directory / f"{document_id}.npz"

    def _index_file(self, document_id: str) -> Path:
        return self.directory / f"{document_id}.faiss"

    def _chunks_file(self, document_id: str) -> Path:
        return self.directory / f"{document_id}.json"

    def save(self, document_id: str, vectors: np.ndarray, chunks: list[TextChunk]) -> None:
        np.savez_compressed(self._vectors_file(document_id), vectors=vectors.astype(np.float32))
        payload = [
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "page": chunk.page,
                "text": chunk.text,
            }
            for chunk in chunks
        ]
        self._chunks_file(document_id).write_text(json.dumps(payload), encoding="utf-8")

        if faiss is not None:
            index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(vectors.astype(np.float32))
            faiss.write_index(index, str(self._index_file(document_id)))

    def load_chunks(self, document_id: str) -> list[TextChunk]:
        file = self._chunks_file(document_id)
        if not file.exists():
            return []
        return [TextChunk(**item) for item in json.loads(file.read_text(encoding="utf-8"))]

    def search(
        self, document_id: str, query: np.ndarray, limit: int = 4
    ) -> list[tuple[TextChunk, float]]:
        chunks = self.load_chunks(document_id)
        vector_file = self._vectors_file(document_id)
        if not chunks or not vector_file.exists():
            return []
        vectors = np.load(vector_file)["vectors"].astype(np.float32)
        count = min(limit, len(chunks))
        if faiss is not None and self._index_file(document_id).exists():
            index = faiss.read_index(str(self._index_file(document_id)))
            scores, indices = index.search(query.astype(np.float32).reshape(1, -1), count)
            pairs = zip(indices[0].tolist(), scores[0].tolist())
        else:
            scores = vectors @ query.astype(np.float32)
            order = np.argsort(scores)[::-1][:count]
            pairs = ((int(position), float(scores[position])) for position in order)
        return [(chunks[position], float(score)) for position, score in pairs if position >= 0]

    def search_multiple(
        self, document_ids: list[str], query: np.ndarray, limit: int = 6, per_doc_limit: int = 4
    ) -> list[tuple[TextChunk, float]]:
        unique_ids = list(dict.fromkeys(document_ids))
        candidates: list[tuple[TextChunk, float]] = []
        for doc_id in unique_ids:
            doc_results = self.search(doc_id, query, limit=per_doc_limit)
            candidates.extend(doc_results)
        candidates.sort(key=lambda item: item[1], reverse=True)
        return candidates[:limit]

    def delete(self, document_id: str) -> None:
        self._vectors_file(document_id).unlink(missing_ok=True)
        self._index_file(document_id).unlink(missing_ok=True)
        self._chunks_file(document_id).unlink(missing_ok=True)
