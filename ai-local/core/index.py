from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from .store import DATA_DIR, read_json, write_json

INDEX_PATH = DATA_DIR / "index.json"


class FactIndex:
    def __init__(self) -> None:
        self.path = INDEX_PATH
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.nn: Optional[NearestNeighbors] = None
        self.documents: List[str] = []
        self.topics: List[str] = []
        self.load()

    def load(self) -> None:
        payload = read_json(self.path, {"documents": [], "topics": []})
        self.documents = payload.get("documents", [])
        self.topics = payload.get("topics", [])
        if self.documents:
            self._fit()

    def _fit(self) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="french")
        matrix = self.vectorizer.fit_transform(self.documents)
        self.nn = NearestNeighbors(metric="cosine")
        self.nn.fit(matrix)

    def add(self, topic: str, summary: str) -> None:
        topic = topic.lower()
        text = f"{topic} {summary}"
        if topic in self.topics:
            idx = self.topics.index(topic)
            self.topics[idx] = topic
            self.documents[idx] = text
        else:
            self.topics.append(topic)
            self.documents.append(text)
        self._fit()
        self.save()

    def save(self) -> None:
        payload = {"documents": self.documents, "topics": self.topics}
        write_json(self.path, payload)

    def query(self, text: str, k: int = 3) -> List[Tuple[str, float]]:
        if not self.documents or self.vectorizer is None or self.nn is None:
            return []
        vec = self.vectorizer.transform([text])
        distances, indices = self.nn.kneighbors(vec, n_neighbors=min(k, len(self.documents)))
        results: List[Tuple[str, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            score = 1 - float(dist)
            results.append((self.topics[idx], score))
        return results


_index: Optional[FactIndex] = None


def get_index() -> FactIndex:
    global _index
    if _index is None:
        _index = FactIndex()
    return _index

