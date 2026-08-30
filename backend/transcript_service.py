"""Orchestrates the transcript pipeline: cache -> official captions ->
Whisper fallback, prioritizing accuracy over speed as specified.
"""
from __future__ import annotations

import re

from . import cache, captions, config, whisper_service, youtube
from .exceptions import TranscriptionFailedError, VideoTooLongError
from .schemas import TranscriptResponse


def _segments_to_text(segments: list[dict]) -> str:
    """Join segment text into clean, readable paragraphs (timestamps
    stripped for display; the raw segments are kept separately).
    """
    raw = " ".join(s["text"].strip() for s in segments if s["text"].strip())
    # Caption tracks often encode literal newlines inside snippet text and
    # double space between cues; normalize whitespace.
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def get_transcript(url: str, force_refresh: bool = False) -> TranscriptResponse:
    video_id = youtube.extract_video_id(url)

    if not force_refresh:
        cached = cache.get(video_id)
        if cached:
            return TranscriptResponse(**cached, cached=True)

    metadata = youtube.get_video_metadata(video_id)
    if metadata["duration"] and metadata["duration"] > config.MAX_VIDEO_DURATION_SECONDS:
        hours = config.MAX_VIDEO_DURATION_SECONDS / 3600
        raise VideoTooLongError(
            f"This video is longer than the {hours:.0f}-hour limit configured for this tool."
        )

    caption_result = captions.fetch_captions(video_id)
    warning = None
    source = None
    segments: list[dict] = []

    manual_available = caption_result is not None and not caption_result.is_generated

    if manual_available:
        source = "manual_captions"
        segments = caption_result.segments
    elif config.WHISPER_ENABLED:
        try:
            segments = whisper_service.transcribe_via_whisper(video_id)
            source = "whisper"
        except TranscriptionFailedError:
            if caption_result is not None:
                source = "auto_captions"
                segments = caption_result.segments
                warning = (
                    "Whisper transcription failed; falling back to YouTube's "
                    "auto-generated captions, which may contain errors."
                )
            else:
                raise
    elif caption_result is not None:
        source = "auto_captions"
        segments = caption_result.segments
        warning = (
            "Only auto-generated captions are available for this video and "
            "the Whisper fallback isn't configured (set OPENAI_API_KEY for "
            "higher accuracy on videos without human-made captions)."
        )
    else:
        raise TranscriptionFailedError(
            "No captions are available for this video and the Whisper "
            "fallback isn't configured. Set OPENAI_API_KEY to enable "
            "audio transcription."
        )

    transcript_text = _segments_to_text(segments)
    if not transcript_text:
        raise TranscriptionFailedError("Transcription produced no text for this video.")

    response = TranscriptResponse(
        video_id=video_id,
        title=metadata["title"],
        duration=metadata["duration"],
        source=source,
        transcript_text=transcript_text,
        segments=segments,
        cached=False,
        warning=warning,
    )

    to_store = response.model_dump(exclude={"cached"})
    cache.set(video_id, to_store)

    return response
