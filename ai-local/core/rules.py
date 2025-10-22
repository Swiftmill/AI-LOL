from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .store import DATA_DIR, append_jsonl, read_jsonl

RULES_PATH = DATA_DIR / "rules.jsonl"


def load_rules() -> List[Dict[str, str]]:
    return read_jsonl(RULES_PATH)


def match_rule(message: str) -> Optional[Dict[str, str]]:
    text = message.lower().strip()
    for entry in load_rules():
        if entry.get("if", "").lower() in text:
            return entry
    return None


def add_rule(if_text: str, reply_text: str) -> Dict[str, str]:
    record = {"if": if_text.strip(), "reply": reply_text.strip()}
    append_jsonl(RULES_PATH, record)
    return record

