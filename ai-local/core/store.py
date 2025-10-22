import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class TTLCache:
    def __init__(self, ttl: float = 300.0):
        self.ttl = ttl
        self._store: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        exp = self._expiry.get(key)
        if exp is not None and exp < now:
            self.delete(key)
            return None
        return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._expiry[key] = time.time() + self.ttl

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self._expiry.pop(key, None)


_cache = TTLCache()


def atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(data)
        temp_name = tmp.name
    os.replace(temp_name, path)


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_json(path: Path, payload: Any) -> None:
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2))


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(line + "\n")
        temp_name = tmp.name
    with path.open("a", encoding="utf-8") as target:
        with open(temp_name, "r", encoding="utf-8") as src:
            for chunk in src:
                target.write(chunk)
    os.remove(temp_name)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def cache_get(key: str) -> Optional[Any]:
    return _cache.get(key)


def cache_set(key: str, value: Any, ttl: float = 300.0) -> None:
    _cache.ttl = ttl
    _cache.set(key, value)


def log_event(name: str, payload: Dict[str, Any]) -> None:
    logs_dir = DATA_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload["event"] = name
    payload["ts"] = time.time()
    append_jsonl(logs_dir / "events.jsonl", payload)


def ensure_files(paths: Iterable[Path]) -> None:
    for path in paths:
        if not path.exists():
            if path.suffix == ".jsonl":
                atomic_write(path, "")
            elif path.suffix == ".json":
                atomic_write(path, json.dumps({}, indent=2))
            else:
                path.touch()

