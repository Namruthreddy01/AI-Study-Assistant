import hashlib
import re
from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """Provider boundary for swapping local embeddings with an API later."""

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Return one L2-normalized vector per input text."""


class HashEmbeddingProvider(EmbeddingProvider):
    """A deterministic local embedding useful for private demos and tests."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = re.findall(r"[a-zA-Z0-9]{2,}", text.lower())
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self.dimension
                sign = 1.0 if digest[4] % 2 else -1.0
                vectors[row, index] += sign
            norm = np.linalg.norm(vectors[row])
            if norm:
                vectors[row] /= norm
        return vectors
