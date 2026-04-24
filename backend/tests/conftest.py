"""Pytest bootstrap — ensures `backend/` is importable when pytest is invoked from the repo root.

CI runs `pytest backend/tests/ -q` from the repo root; without this shim `from app...` imports fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
