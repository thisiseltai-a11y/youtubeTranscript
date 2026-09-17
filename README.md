# gambitParlay

Statistical EPL match predictions from a backtested Dixon-Coles Poisson
model, wrapped as a deployable web app (and prepped for an iOS shell).

## Layout

- **`/`** (this directory) — the Next.js frontend. Lives at the repo root
  so it deploys with Vercel's default settings (no Root Directory override
  needed).
- **`model/`** — the original Dixon-Coles model code (`data_loader.py`,
  `poisson_model.py`, `backtest.py`, `staking.py`, `main.py`) plus fetched
  EPL match data. Unmodified — everything else wraps this.
- **`backend/`** — FastAPI service wrapping `model/` (`GET /ratings`,
  `GET /fixtures`, `POST /evaluate-bet`, `GET /backtest-summary`). Fits
  once at startup, refits daily.
- **`mobile/`** — Capacitor iOS app shell prep (loads the deployed
  frontend in a native WebView). See `mobile/README.md`.

See `DEPLOYMENT.md` for how to deploy the frontend (Vercel) and backend
(Render/Fly.io).

## Local development

```bash
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_BASE_URL to your local/deployed backend
npm run dev
```

Backend, separately:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
