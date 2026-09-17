# Deployment

Two services, deployed separately: the FastAPI backend (`backend/`) on
Render, and the Next.js frontend (repo root) on Vercel. Both read from the
same GitHub repo/branch — no shared build step between them.

## Backend → Render

1. On [render.com](https://render.com), **New +** → **Web Service** → connect
   this GitHub repo and pick the `claude/youtube-transcript-ai-rewrite-em21my`
   branch (or `main` once merged).
2. **Environment**: Docker.
3. **Root Directory**: leave blank (repo root) — the Dockerfile needs both
   `backend/` and `model/` as siblings in its build context, so the build
   context must stay at the repo root, not `backend/`.
4. **Dockerfile Path**: `backend/Dockerfile`
5. **Docker Build Context Directory**: `.` (repo root)
6. **Health Check Path**: `/health`
7. Plan: the free tier works for testing. See the **cold-start caveat**
   below before relying on it for anything real.
8. Deploy. Once live, note the URL — something like
   `https://gambitparlay-api.onrender.com`. Confirm it works:
   ```bash
   curl https://gambitparlay-api.onrender.com/status
   curl https://gambitparlay-api.onrender.com/ratings
   ```

### Optional: live scores (API-Football)

`GET /live-scores` shows real, live EPL scores for today (separate from the
prediction model). It's optional — if unconfigured, the endpoint just
returns an empty list and the frontend hides that section entirely.

To enable it:
1. In the Render service → **Environment** tab → add an environment
   variable: `API_FOOTBALL_KEY` = your key from
   [api-football.com](https://www.api-football.com/) (free tier is 100
   requests/day, plenty for this — the backend caches responses for 30
   seconds so many visitors only cost one upstream request).
2. Save — Render redeploys automatically with the new env var.
3. Confirm: `curl https://<your-render-url>/live-scores` should return real
   match data on a day EPL matches are being played, `[]` otherwise.

No other environment variables are required — everything else about the
backend has no secrets (no other API keys, no database).

### Cold-start / scheduler caveat (read before relying on daily refit)

Render's free tier spins the service down after ~15 minutes idle and cold
starts on the next request. Two consequences:

- The **daily 06:00 UTC refit job** (APScheduler, in `backend/app/main.py`)
  only fires if the process happens to be running at that moment. On a free
  instance that's asleep most of the day, it may simply never fire.
- The **startup fit** (~5-6 seconds) reruns on every cold start, so the
  first request after idle time is slow.

The model still refits and serves correctly whenever the process is
running — this only affects whether "daily" is reliable unattended. Two
ways to fix it, pick one:

1. **Simplest**: upgrade to Render's paid Starter tier, which doesn't spin
   down. The scheduled job then behaves as designed.
2. **Free-tier workaround**: use Render's Cron Jobs (or an external pinger
   like a `GET /health` from a service like cron-job.org) to hit the API
   every 10-15 minutes, keeping the instance warm so the 06:00 UTC job
   actually runs. This costs nothing extra but is a workaround, not a fix.

## Frontend → Vercel

1. On [vercel.com](https://vercel.com), **Add New** → **Project** → import
   the same GitHub repo (or use the existing connected project, if you have
   one — it already auto-deploys this branch on every push).
2. **Root Directory**: leave as default (repo root) — the Next.js app lives
   at the repo root, not in a subdirectory.
3. Framework preset: Next.js (auto-detected — no changes needed).
4. **Environment Variables**: add
   ```
   NEXT_PUBLIC_API_BASE_URL = https://gambitparlay-api.onrender.com
   ```
   (your actual Render URL from above, no trailing slash).
5. Deploy. Vercel gives you a `https://<project>.vercel.app` URL.

CORS is already wide open on the backend (`allow_origins=["*"]` in
`backend/app/main.py`), so no backend changes are needed for the Vercel
domain to call it. If you later want to lock this down, restrict it to your
actual Vercel domain(s) once you know them.

## After both are deployed

- Confirm the full path end-to-end: load the Vercel URL in a browser, check
  the ratings table, fixture cards, and bet evaluator all populate from the
  live Render API (open browser devtools → Network tab if anything looks
  empty).
- Update `mobile/capacitor.config.ts`'s `PRODUCTION_URL` to the Vercel URL
  before doing anything with the iOS shell — see `mobile/README.md`.
