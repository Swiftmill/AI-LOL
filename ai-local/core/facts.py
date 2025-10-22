from __future__ import annotations

import json
from typing import Dict, List, Optional

from .store import DATA_DIR, append_jsonl, read_jsonl

FACTS_PATH = DATA_DIR / "facts.jsonl"


def load_facts() -> List[Dict[str, object]]:
    return read_jsonl(FACTS_PATH)


def find_fact(topic: str) -> Optional[Dict[str, object]]:
    topic_lower = topic.lower()
    for fact in load_facts():
        if fact.get("topic", "").lower() == topic_lower:
            return fact
    return None


def fuzzy_lookup(message: str) -> Optional[Dict[str, object]]:
    text = message.lower()
    for fact in load_facts():
        topic = str(fact.get("topic", "")).lower()
        if topic and (topic in text or text in topic):
            return fact
    return None


def save_fact(topic: str, summary: str, sources: List[str]) -> Dict[str, object]:
    topic = topic.lower().strip()
    existing = find_fact(topic)
    record = {"topic": topic, "summary": summary.strip(), "sources": sources[:3]}
    if existing:
        # overwrite existing by rewriting file
        facts = load_facts()
        updated: List[Dict[str, object]] = []
        for fact in facts:
            if fact.get("topic", "").lower() == topic:
                updated.append(record)
            else:
                updated.append(fact)
        with FACTS_PATH.open("w", encoding="utf-8") as f:
            for fact in updated:
                f.write(json.dumps(fact, ensure_ascii=False) + "\n")
    else:
        append_jsonl(FACTS_PATH, record)
    return record

