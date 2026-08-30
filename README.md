# YouTube Transcript + AI Rewrite

Paste a YouTube URL, get a clean transcript, edit it, and rewrite it with
Claude while preserving the original speaker's tone and voice.

## How it works

1. **Transcript extraction** (`backend/transcript_service.py`), prioritizing accuracy:
   1. Official **manually-created** YouTube captions (via `youtube-transcript-api`) - fast, free, human-accurate.
   2. If only **auto-generated** captions exist (or none at all) and `OPENAI_API_KEY` is set, the audio is downloaded with `yt-dlp` and transcribed with **OpenAI's Whisper API** for higher accuracy. Long audio is chunked with `ffmpeg` to stay under Whisper's upload limit, so 2hr+ videos work (just slower).
   3. If Whisper isn't configured, YouTube's auto-generated captions are used as a last resort, with a warning surfaced in the UI.
   4. Transcripts are cached per video ID under `cache/<video_id>.json` so a video is never reprocessed.
2. **AI rewrite** (`backend/rewrite_service.py`): sends the transcript + your instructions to Claude (`claude-opus-5` by default) with a system prompt that explicitly analyzes and preserves tone/voice/pacing/structure unless you ask it to change them. Presets: clean up filler words, shorten, adapt for YouTube Shorts / TikTok caption / blog post, rewrite for a new topic (same voice), or custom instructions.

## Requirements

- Python 3.10+
- [`ffmpeg`](https://ffmpeg.org/) on your `PATH` (only needed for the Whisper fallback path - audio download/transcode/chunking)
- An Anthropic API key (for the rewrite feature)
- An OpenAI API key (optional, for the Whisper fallback)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in ANTHROPIC_API_KEY (required for rewrite)
# and OPENAI_API_KEY (optional, for the Whisper fallback)
```

## Run

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** - the backend serves the frontend directly,
so there's nothing else to start.

## API

- `POST /api/transcript` - `{ "url": "...", "force_refresh": false }` -> transcript, source (`manual_captions` / `auto_captions` / `whisper`), segments with timestamps, cache status.
- `POST /api/rewrite` - `{ "transcript_text": "...", "preset": "shorten", "target_topic": null, "instructions": "" }` -> `{ "rewritten_text": "..." }`.
- `GET /api/health` - reports whether the Whisper fallback and rewrite feature are configured.

## Error handling

Invalid URLs, private/deleted/unavailable videos, videos with no audio
track, and videos over the configured length cap (`MAX_VIDEO_DURATION_SECONDS`,
default 6h) all return a clear error message in the UI instead of a stack
trace.

## Notes / next steps for deployment

- Cache is a flat JSON-per-video directory (`cache/`) - fine for local use; swap for Redis/S3/a DB before deploying multi-instance.
- No auth/rate-limiting yet (v1, local-only per the brief).
- `CORS` is wide open (`*`) for local dev - lock this down before deploying publicly.
- Self-hosting Whisper instead of OpenAI's API is a drop-in swap in `backend/whisper_service.py` if you'd rather not pay per-minute.
