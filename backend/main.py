from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, lot_store, rewrite_service, transcript_service
from .exceptions import TranscriptAppError
from .schemas import (
    LotState,
    RewriteRequest,
    RewriteResponse,
    TranscriptRequest,
    TranscriptResponse,
)

app = FastAPI(title="YouTube Transcript + AI Rewrite")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TranscriptAppError)
async def handle_app_error(request: Request, exc: TranscriptAppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "whisper_enabled": config.WHISPER_ENABLED,
        "rewrite_enabled": bool(config.ANTHROPIC_API_KEY),
    }


@app.post("/api/transcript", response_model=TranscriptResponse)
def post_transcript(req: TranscriptRequest):
    return transcript_service.get_transcript(req.url, force_refresh=req.force_refresh)


@app.post("/api/rewrite", response_model=RewriteResponse)
def post_rewrite(req: RewriteRequest):
    rewritten = rewrite_service.rewrite_transcript(req)
    return RewriteResponse(rewritten_text=rewritten)


# --- The Lot ---------------------------------------------------------------
# One shared JSON blob (there's only one lot) so every device that opens
# /the-lot sees the same list. No auth for v1, same as the rest of this app.


@app.get("/api/lot", response_model=LotState)
def get_lot():
    return lot_store.get() or LotState()


@app.put("/api/lot", response_model=LotState)
def put_lot(state: LotState):
    lot_store.set(state.model_dump())
    return state


# --- Serve the static frontend (local dev only) ---------------------------
# On Vercel, everything under public/ is served directly by the platform
# (and takes precedence over the vercel.json rewrite into this app), so
# mounting it here too would be redundant - and the filesystem there is
# read-only outside of /tmp anyway.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "public"
if FRONTEND_DIR.exists() and not config.IS_VERCEL:
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
