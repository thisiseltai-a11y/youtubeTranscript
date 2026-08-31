# YouTube Transcript + AI Rewrite

Paste a YouTube URL, get a clean transcript, edit it, and rewrite it with
Claude while preserving the original speaker's tone and voice.

Runs locally with `uvicorn`, and deploys to **Vercel** as a Python
serverless function (`api/index.py`) + static frontend (`public/`).

## How it works

1. **Transcript extraction** (`backend/transcript_service.py`), prioritizing accuracy:
   1. Official **manually-created** YouTube captions (via `youtube-transcript-api`) - fast, free, human-accurate.
   2. If only **auto-generated** captions exist (or none at all), `OPENAI_API_KEY` is set, and the video is short enough (see **Whisper duration cap** below), the audio is downloaded with `yt-dlp` and transcribed with **OpenAI's Whisper API** for higher accuracy. Long audio is chunked to stay under Whisper's upload limit.
   3. Otherwise, YouTube's auto-generated captions are used as a last resort, with a warning surfaced in the UI.
   4. Transcripts are cached per video ID (see **Caching** below) so a video is never reprocessed.
2. **AI rewrite** (`backend/rewrite_service.py`): sends the transcript + your instructions to Claude (`claude-opus-5` by default) with a system prompt that explicitly analyzes and preserves tone/voice/pacing/structure unless you ask it to change them. Presets: clean up filler words, shorten, adapt for YouTube Shorts / TikTok caption / blog post, rewrite for a new topic (same voice), or custom instructions.

## Requirements

- Python 3.10+
- An Anthropic API key (for the rewrite feature)
- An OpenAI API key (optional, for the Whisper fallback)
- `ffmpeg` is **not** a system dependency - the Whisper path bundles its own static binary via `imageio-ffmpeg`, so this works the same locally and on Vercel with nothing to install.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in ANTHROPIC_API_KEY (required for rewrite)
# and OPENAI_API_KEY (optional, for the Whisper fallback)
```

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** - the backend serves `public/` directly, so
there's nothing else to start. Locally, the Whisper fallback has no
practical duration cap (2hr+ videos are fine, just slower).

## Deploying to Vercel

```bash
npm i -g vercel   # if you don't have the CLI
vercel login
vercel            # first deploy - links/creates the project
vercel --prod     # subsequent production deploys
```

Or connect the GitHub repo at vercel.com/new and it'll pick up
`vercel.json` automatically on every push.

**Set environment variables** (Project Settings -> Environment Variables, or `vercel env add`):

| Variable | Required | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Powers the rewrite feature. |
| `OPENAI_API_KEY` | No | Enables the Whisper fallback. Without it, videos lacking human-made captions fall back to auto-captions. |
| `KV_REST_API_URL` / `KV_REST_API_TOKEN` | Recommended | Set automatically when you add the **Upstash for Redis** integration from the Vercel Marketplace. Without it, caching still works but only as a best-effort, non-durable fallback in `/tmp`. |
| `WEBSHARE_PROXY_USERNAME` / `WEBSHARE_PROXY_PASSWORD` | Recommended for real traffic | See **YouTube blocking cloud IPs** below - the scalable fix. |
| `YTDLP_COOKIES_B64` | No | See **YouTube blocking cloud IPs** below - a single-identity fallback. |
| `WHISPER_MAX_DURATION_SECONDS` | No | Default `300` (5 min) on Vercel. Raise this only alongside `maxDuration` in `vercel.json` - see below. |

### Whisper duration cap (why it exists)

Vercel functions have a hard execution time limit - **60s max on Hobby**,
up to **300s+ on Pro** (see [Vercel's function duration docs](https://vercel.com/docs/functions/configuring-functions/duration)
for current numbers). Downloading audio, transcoding, and calling the
Whisper API for a long video can easily exceed that. Rather than let a
request time out, videos longer than `WHISPER_MAX_DURATION_SECONDS`
(default 5 min on Vercel) skip Whisper entirely and fall back to
YouTube's auto-generated captions instead, with a warning shown in the UI.

If you're on a Pro plan and want Whisper on longer videos, raise **both**:
- `vercel.json` -> `functions."api/index.py".maxDuration` (e.g. `300`)
- the `WHISPER_MAX_DURATION_SECONDS` env var (leave headroom under `maxDuration` - downloading + transcoding + the Whisper call all need to fit inside it)

There's no cap on Whisper when running locally (`uvicorn`) since there's no serverless timeout to worry about.

### YouTube blocking cloud IPs

YouTube sometimes rate-limits or blocks requests (both metadata lookups and
audio downloads) that come from datacenter/cloud IP ranges, including
Vercel's - you may see errors mentioning "Sign in to confirm you're not a
bot" (or a generic "Video unavailable") that don't happen locally, even on
videos that are obviously public.

Three mitigations, roughly in order of how well they scale:

1. **Baked in by default, free**: requests go through YouTube's mobile client
   API surface (`player_client: [android, ios, web]` in
   `backend/ytdlp_common.py`) instead of only the main web client, since the
   web client is what usually triggers the bot-check wall on cloud IPs. No
   setup needed, but doesn't hold up under real traffic.
2. **Rotating residential proxies (recommended for anything beyond solo
   testing)**: requests route through a large pool of real residential IPs
   via [Webshare](https://www.webshare.io) instead of this server's own IP,
   so no single IP takes on enough volume to get flagged - this is what
   `youtube-transcript-api` itself (the library behind the captions path)
   recommends for exactly this problem.
   1. Create a Webshare account and buy a **"Residential"** proxy package (their free tier - 10 proxies, 1GB/month - is enough to test with; do **not** buy "Proxy Server" or "Static Residential", those don't rotate).
   2. Grab your **Proxy Username** and **Proxy Password** from https://dashboard.webshare.io/proxy/settings (two separate values, not one combined key).
   3. Set `WEBSHARE_PROXY_USERNAME` and `WEBSHARE_PROXY_PASSWORD` in Vercel (both required together).
3. **Cookies (single-identity fallback)**: makes requests look like one
   specific logged-in browser session rather than an anonymous cloud IP.
   Works, but it's one identity behind however many users hit your site, so
   it degrades under real traffic the same way a single un-proxied server
   IP would - use this only if you don't want to set up a proxy yet.
   1. Export your youtube.com cookies as a Netscape-format `cookies.txt` (e.g. the "Get cookies.txt" browser extension) while logged into a real YouTube account.
   2. Base64-encode the file: `base64 -w0 cookies.txt` (macOS: `base64 -i cookies.txt`).
   3. Set that string as the `YTDLP_COOKIES_B64` env var in Vercel.

None of these are guaranteed to eliminate blocking entirely - treat them as
mitigations, not a permanent fix. If errors persist, the app shows the
actual underlying yt-dlp error message rather than a guessed category,
which is the fastest way to tell what's actually happening.

### Caching

Locally, the cache is a flat JSON-per-video directory (`cache/`). On
Vercel there's no persistent disk between invocations, so the cache
prefers **Upstash Redis** via the "Upstash for Redis" Vercel Marketplace
integration (free tier available) - add it from your project's
Integrations tab and the `KV_REST_API_URL`/`KV_REST_API_TOKEN` env vars
are wired up automatically. Without that integration, the app still runs,
just without durable caching (each cold start starts fresh).

## The Lot

A small standalone page at `/the-lot` (`public/the-lot.html`) for tracking
inventory as a pixel-art town - one house per car, grouped by lot number and
for-sale/sold status. Unrelated to the transcript tool; it just rides along
on the same Vercel deployment. No auth (same as the rest of this app, v1) -
anyone with the URL can view and edit it.

State is a single shared JSON blob (`backend/lot_store.py`), using the same
Upstash-Redis-or-local-file storage as the transcript cache, so every device
that opens the page sees the same list. The page also caches the last-seen
state in `localStorage` for an instant first paint and offline viewing.

## API

- `POST /api/transcript` - `{ "url": "...", "force_refresh": false }` -> transcript, source (`manual_captions` / `auto_captions` / `whisper`), segments with timestamps, cache status.
- `POST /api/rewrite` - `{ "transcript_text": "...", "preset": "shorten", "target_topic": null, "instructions": "" }` -> `{ "rewritten_text": "..." }`.
- `GET /api/health` - reports whether the Whisper fallback and rewrite feature are configured.
- `GET /api/lot` / `PUT /api/lot` - reads/replaces The Lot's shared `{ "cars": [{ "id", "lot", "status" }] }` state.

## Error handling

Invalid URLs, private/deleted/unavailable videos, videos with no audio
track, and videos over the configured length cap (`MAX_VIDEO_DURATION_SECONDS`,
default 6h) all return a clear error message in the UI instead of a stack
trace.

## Notes / possible next steps

- No auth/rate-limiting yet (v1, per the brief) - anyone with the URL can call the API and spend your Anthropic/OpenAI credits. Worth adding before sharing the link widely.
- `CORS` is wide open (`*`) - fine while it's just you testing, worth locking down before wider use.
- Self-hosting Whisper instead of OpenAI's API is a swap in `backend/whisper_service.py` if you'd rather not pay per-minute - though that reintroduces a "where does the model actually run" problem that Vercel's serverless functions aren't a good fit for (no GPU, no long-lived process); it'd want its own always-on host.
- For Whisper on videos longer than what a Pro-plan function timeout can fit, the real fix is a background job (queue + worker) rather than raising timeouts further - flagged in case this becomes the bottleneck later.
