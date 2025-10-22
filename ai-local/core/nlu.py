import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import spacy
except Exception:  # pragma: no cover
    spacy = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


INTENT_TEMPLATES = {
    "GREET": ["bonjour", "salut", "hello"],
    "DEFINE": ["c'est quoi X", "que signifie X", "définis X"],
    "SEARCH_ORDER": ["cherche sur le web", "regarde sur internet", "va sur google"],
    "ALIAS_LEARN": ["X veut dire Y", "X = Y", "Y (X)", "X signifie Y"],
    "RULE_CREATE": ["quand je dis X réponds Y", "si je dis X répond Y"],
    "EXPLORE": ["explore", "exploration", "découvre"]
}


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


@lru_cache(maxsize=1)
def get_spacy(lang: str = "fr"):
    if spacy is None:
        raise RuntimeError("spaCy is not installed")
    try:
        if lang == "fr":
            return spacy.load("fr_core_news_sm")
        return spacy.load("en_core_web_sm")
    except OSError:
        return spacy.blank("fr" if lang == "fr" else "en")


@lru_cache(maxsize=1)
def get_transformer() -> Optional[SentenceTransformer]:
    if SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception:
        return None


class NLUEngine:
    def __init__(self) -> None:
        self.fr_nlp = get_spacy("fr")
        self.en_nlp = get_spacy("en")
        self.embedder = get_transformer()
        self.intent_embeddings = self._prepare_intents()

    def _prepare_intents(self) -> Dict[str, List[np.ndarray]]:
        vectors: Dict[str, List[np.ndarray]] = {}
        if self.embedder is None:
            return vectors
        for intent, phrases in INTENT_TEMPLATES.items():
            vectors[intent] = []
            for phrase in phrases:
                vectors[intent].append(self.embedder.encode(phrase))
        return vectors

    def _embed(self, text: str) -> Optional[np.ndarray]:
        if self.embedder is None:
            return None
        return self.embedder.encode(text)

    def detect_intent(self, message: str) -> Tuple[str, float]:
        text = message.lower().strip()
        scores: Dict[str, float] = {}
        if self.embedder is None:
            for intent, phrases in INTENT_TEMPLATES.items():
                scores[intent] = max(1.0 if phrase.replace("x", "").strip() in text else 0.0 for phrase in phrases)
        else:
            query_vec = self._embed(text)
            if query_vec is not None:
                for intent, vecs in self.intent_embeddings.items():
                    if not vecs:
                        continue
                    scores[intent] = max(cosine_similarity(query_vec, vec) for vec in vecs)
        if not scores:
            return "UNKNOWN", 0.0
        intent, score = max(scores.items(), key=lambda kv: kv[1])
        threshold = 0.35 if self.embedder else 0.5
        if score < threshold:
            return "UNKNOWN", score
        return intent, score

    def extract_topic(self, message: str) -> Optional[str]:
        doc = self.fr_nlp(message)
        candidates = [chunk.text for chunk in doc.noun_chunks]
        if not candidates:
            doc = self.en_nlp(message)
            candidates = [chunk.text for chunk in doc.noun_chunks]
        if not candidates:
            # fallback simple
            tokens = [token.text for token in doc if token.is_alpha and not token.is_stop]
            if tokens:
                return tokens[-1].lower()
            return None
        return candidates[-1].strip()

    def parse_alias(self, message: str) -> Optional[Tuple[str, str, float]]:
        text = message.lower().strip()
        token_pattern = r"[\w\s'’\-\.]+"
        patterns = [
            rf"(?P<from>{token_pattern})\s*=\s*(?P<to>{token_pattern})",
            rf"(?P<from>{token_pattern})\s+veut\s+dire\s+(?P<to>{token_pattern})",
            rf"(?P<to>{token_pattern})\s*\((?P<from>{token_pattern})\)",
            rf"(?P<from>{token_pattern})\s+signifie\s+(?P<to>{token_pattern})"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                source = match.group("from").strip()
                target = match.group("to").strip()
                if not source or not target:
                    continue
                confidence = 0.95 if len(source.split()) <= 3 else 0.8
                return source, target, confidence
        return None

    def infer_slots(self, message: str) -> Dict[str, Optional[str]]:
        topic = self.extract_topic(message)
        return {"topic": topic, "query": topic}


_nlu_instance: Optional[NLUEngine] = None


def get_nlu() -> NLUEngine:
    global _nlu_instance
    if _nlu_instance is None:
        _nlu_instance = NLUEngine()
    return _nlu_instance

