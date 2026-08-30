"""Central configuration, loaded from environment variables / .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- API keys -----------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# --- Models ---------------------------------------------------------------
REWRITE_MODEL = os.environ.get("REWRITE_MODEL", "claude-opus-5")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "whisper-1")

# --- Storage --------------------------------------------------------------
CACHE_DIR = Path(os.environ.get("CACHE_DIR", BASE_DIR / "cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TMP_DIR = Path(os.environ.get("TMP_DIR", BASE_DIR / "tmp"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

# --- Limits / behavior ------------------------------------------------
# Hard safety cap so a runaway/oversized video can't hang the server or blow
# past Whisper API costs unexpectedly. 2hr+ videos are explicitly supported;
# this is a generous ceiling above that (default 6 hours).
MAX_VIDEO_DURATION_SECONDS = int(os.environ.get("MAX_VIDEO_DURATION_SECONDS", 6 * 3600))

# OpenAI's Whisper transcription endpoint rejects files above this size.
# We chunk audio to stay comfortably under it.
WHISPER_MAX_UPLOAD_BYTES = 24 * 1024 * 1024  # 24MB, just under the 25MB API cap

# Length (seconds) of each audio chunk fed to Whisper when a file must be split.
WHISPER_CHUNK_SECONDS = int(os.environ.get("WHISPER_CHUNK_SECONDS", 600))  # 10 min

# Whether to attempt the Whisper fallback at all (requires OPENAI_API_KEY).
WHISPER_ENABLED = bool(OPENAI_API_KEY)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
