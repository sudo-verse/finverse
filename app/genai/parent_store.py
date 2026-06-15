"""Parent-chunk store for small-to-big (parent–child) retrieval.

Child chunks are what we embed and match on (precise); their parent section is
what we hand to the generator (full context). Parents aren't searched, so they
don't need to live in the vector store — a JSON sidecar next to the Chroma
directory is enough at this corpus scale (swap for SQLite/Redis if it grows).
"""

import json
import os
import threading

from app.config import CHROMA_DIR
from app.utils.logger import logger

_PATH = os.path.join(CHROMA_DIR, "parents.json")
_lock = threading.Lock()
_store: dict | None = None


def _load() -> dict:
    global _store
    if _store is None:
        try:
            with open(_PATH) as f:
                _store = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _store = {}
    return _store


def _save(store: dict) -> None:
    os.makedirs(CHROMA_DIR, exist_ok=True)
    tmp = _PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(store, f)
    os.replace(tmp, _PATH)  # atomic


def get(parent_id: str) -> dict | None:
    with _lock:
        return _load().get(parent_id)


def put_many(items: dict[str, dict]) -> None:
    if not items:
        return
    with _lock:
        store = _load()
        store.update(items)
        _save(store)


def clear() -> None:
    global _store
    with _lock:
        _store = {}
        _save(_store)
    logger.info("parent_store: cleared")


def count() -> int:
    with _lock:
        return len(_load())
