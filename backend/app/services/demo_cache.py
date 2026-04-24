"""Local JSON read-through cache for GLM pipeline stages.

Protects the live demo if wifi drops (PRD §8.2). Each of the four GLM calls
writes its response to disk keyed by a SHA-256 of the stage inputs. On re-run
the cached payload is served, which also makes verdict output deterministic
across repeated identical inputs (F7 acceptance).
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "demo_cache"


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)


def make_key(stage: str, *parts: Any) -> str:
    hasher = hashlib.sha256()
    hasher.update(stage.encode("utf-8"))
    hasher.update(b"\x00")
    for part in parts:
        if isinstance(part, (bytes, bytearray)):
            hasher.update(bytes(part))
        else:
            hasher.update(_canonical_json(part).encode("utf-8"))
        hasher.update(b"\x00")
    return hasher.hexdigest()


def _path_for(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get(key: str) -> dict | None:
    path = _path_for(key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def put(key: str, payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _path_for(key)
    # Unique tmp suffix per writer so concurrent identical-key writes don't
    # clobber each other's in-flight tmp file before rename.
    tmp_path = path.with_suffix(f".json.tmp-{os.getpid()}-{uuid.uuid4().hex}")
    try:
        tmp_path.write_text(_canonical_json(payload), encoding="utf-8")
        tmp_path.replace(path)
    except Exception:
        # Best effort: remove the orphaned tmp file on failure.
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
