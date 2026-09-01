"""Pydantic request/response models."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    start: float
    duration: float
    text: str


class TranscriptRequest(BaseModel):
    url: str = Field(..., description="A YouTube video URL")
    force_refresh: bool = Field(False, description="Bypass the cache and reprocess")


class TranscriptResponse(BaseModel):
    video_id: str
    title: Optional[str] = None
    duration: Optional[float] = None
    source: Literal["manual_captions", "auto_captions", "whisper"]
    transcript_text: str
    segments: list[TranscriptSegment]
    cached: bool
    warning: Optional[str] = None


REWRITE_PRESETS = Literal[
    "custom",
    "clean_filler",
    "shorten",
    "youtube_shorts",
    "tiktok_caption",
    "blog_post",
    "new_topic",
]


class RewriteRequest(BaseModel):
    transcript_text: str
    instructions: str = Field(
        "", description="Free-form instructions describing the desired change"
    )
    preset: REWRITE_PRESETS = "custom"
    target_topic: Optional[str] = Field(
        None, description="New subject/product to rewrite the content about, if any"
    )


class RewriteResponse(BaseModel):
    rewritten_text: str
    style_notes: Optional[str] = None


class LotCar(BaseModel):
    id: str
    lot: str
    status: Literal["for-sale", "sold"]
    # A key into the frontend's CAR_SPRITES map (public/index.html) - just
    # "camaro-ss" for now. Left as a plain string rather than a Literal so
    # adding a new make there doesn't also require a backend deploy, and so
    # cars saved before this field existed still validate.
    make: str = "camaro-ss"


class LotState(BaseModel):
    cars: list[LotCar] = Field(default_factory=list)
