"""Vercel's Python runtime entrypoint. Requests are rewritten here per
vercel.json; this just exposes the same FastAPI ASGI app used locally.
"""
import sys
from pathlib import Path

# Make sure the repo root (and therefore the `backend` package) is
# importable regardless of how Vercel's builder sets up sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.main import app  # noqa: E402

__all__ = ["app"]
