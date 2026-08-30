"""Central configuration, loaded from environment variables / .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Vercel sets VERCEL=1 for both build and runtime. Used to switch to
# /tmp-only storage (the only writable path in a serverless function) and
# to skip mounting a local static-file server (Vercel serves public/ itself).
IS_VERCEL = bool(os.environ.get("VERCEL"))

# --- API keys -----------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# --- Models ---------------------------------------------------------------
REWRITE_MODEL = os.environ.get("REWRITE_MODEL", "claude-opus-5")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "whisper-1")

# --- Storage --------------------------------------------------------------
# Local prototype: a JSON file per video under ./cache. On Vercel, the
# filesystem is read-only except /tmp, and /tmp isn't guaranteed to persist
# between invocations - so the transcript cache prefers Upstash Redis (via
# the "Upstash for Redis" Vercel Marketplace integration) when configured,
# and falls back to /tmp as a best-effort, non-durable cache otherwise.
KV_REST_API_URL = os.environ.get("KV_REST_API_URL", "")
KV_REST_API_TOKEN = os.environ.get("KV_REST_API_TOKEN", "")
KV_ENABLED = bool(KV_REST_API_URL and KV_REST_API_TOKEN)

_default_cache_dir = Path("/tmp/cache") if IS_VERCEL else BASE_DIR / "cache"
CACHE_DIR = Path(os.environ.get("CACHE_DIR", _default_cache_dir))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_default_tmp_dir = Path("/tmp") if IS_VERCEL else BASE_DIR / "tmp"
TMP_DIR = Path(os.environ.get("TMP_DIR", _default_tmp_dir))
TMP_DIR.mkdir(parents=True, exist_ok=True)

# --- Limits / behavior ------------------------------------------------
# Hard safety cap so a runaway/oversized video can't hang the server or blow
# past Whisper API costs unexpectedly. 2hr+ videos are explicitly supported;
# this is a generous ceiling above that (default 6 hours). This only bounds
# outright rejection - the *much* tighter WHISPER_MAX_DURATION_SECONDS below
# is what actually protects a serverless deploy from timing out.
MAX_VIDEO_DURATION_SECONDS = int(os.environ.get("MAX_VIDEO_DURATION_SECONDS", 6 * 3600))

# OpenAI's Whisper transcription endpoint rejects files above this size.
# We chunk audio to stay comfortably under it.
WHISPER_MAX_UPLOAD_BYTES = 24 * 1024 * 1024  # 24MB, just under the 25MB API cap

# Length (seconds) of each audio chunk fed to Whisper when a file must be split.
WHISPER_CHUNK_SECONDS = int(os.environ.get("WHISPER_CHUNK_SECONDS", 600))  # 10 min

# Whether to attempt the Whisper fallback at all (requires OPENAI_API_KEY).
WHISPER_ENABLED = bool(OPENAI_API_KEY)

# Videos longer than this skip the Whisper fallback entirely (falling back
# to auto-captions if available) rather than risk a serverless function
# timeout. Default (5 min) is sized to comfortably fit inside a 60s Vercel
# Hobby function; raise this (and vercel.json's maxDuration, up to a Pro
# plan's higher ceiling) if you're on Pro. Running locally (not on Vercel)
# this doesn't need to be nearly so conservative.
WHISPER_MAX_DURATION_SECONDS = int(
    os.environ.get("WHISPER_MAX_DURATION_SECONDS", 300 if IS_VERCEL else 3 * 3600)
)

# Optional: base64-encoded Netscape-format cookies.txt, used to make yt-dlp
# requests look like a logged-in browser session. YouTube sometimes blocks
# or rate-limits requests from cloud/datacenter IPs (including Vercel's);
# exporting cookies from a real browser session is the standard workaround.
# See README for how to generate this.
YTDLP_COOKIES_B64 = os.environ.get("YTDLP_COOKIES_B64", "")

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
