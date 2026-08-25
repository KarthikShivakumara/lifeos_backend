from __future__ import annotations

import math
import re
from collections import Counter


class VectorEmbeddingEngine:
    def _tokenize(self, text: str) -> list[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) > 2]

    def get_embedding(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        counts = Counter(tokens)
        norm = math.sqrt(sum(c * c for c in counts.values()))
        return {word: count / norm for word, count in counts.items()}

    def cosine_similarity(self, vec1: dict[str, float], vec2: dict[str, float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        # Compute dot product
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[w] * vec2[w] for w in intersection)
        return float(dot_product)


embedding_engine = VectorEmbeddingEngine()
