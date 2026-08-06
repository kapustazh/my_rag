"""RAG against the machine"""

import os
from pathlib import Path

_cache = Path(__file__).resolve().parents[1] / ".cache"
_cache.mkdir(exist_ok=True)
os.environ.setdefault("HF_HOME", str(_cache / "hf_cache"))
os.environ.setdefault("UV_CACHE_DIR", str(_cache / "uv_cache"))