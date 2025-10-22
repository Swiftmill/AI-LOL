from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

from .nlu import get_nlu
from .store import DATA_DIR, atomic_write, read_json, write_json

ALIASES_PATH = DATA_DIR / "ontology" / "aliases.json"


class Ontology:
    def __init__(self) -> None:
        self.path = ALIASES_PATH
        self.aliases: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        self.aliases = read_json(self.path, {})

    def save(self) -> None:
        write_json(self.path, self.aliases)

    def normalize(self, text: str) -> str:
        lowered = text.lower()
        tokens = re.split(r"(\W+)", lowered)
        normalized_tokens = [self.aliases.get(tok, tok) for tok in tokens]
        return "".join(normalized_tokens)

    def add_alias(self, source: str, target: str) -> None:
        if not source or not target:
            return
        self.aliases[source.lower().strip()] = target.lower().strip()
        self.save()

    def extract(self, message: str) -> Optional[Tuple[str, str, float]]:
        nlu = get_nlu()
        candidate = nlu.parse_alias(message)
        if candidate:
            source, target, confidence = candidate
            if confidence >= 0.9:
                self.add_alias(source, target)
            return candidate
        return None


_ontology: Optional[Ontology] = None


def get_ontology() -> Ontology:
    global _ontology
    if _ontology is None:
        _ontology = Ontology()
    return _ontology

