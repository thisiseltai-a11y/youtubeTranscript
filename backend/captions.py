"""Fetch YouTube's own caption tracks via youtube-transcript-api."""
from __future__ import annotations

from dataclasses import dataclass

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from .exceptions import VideoUnavailableError

# Languages tried in order. English first since that's the common case;
# extend this list (or make it user-configurable) for other-language content.
PREFERRED_LANGUAGES = ["en", "en-US", "en-GB"]


@dataclass
class CaptionResult:
    is_generated: bool
    language_code: str
    segments: list[dict]  # [{"start": float, "duration": float, "text": str}, ...]


def fetch_captions(video_id: str) -> CaptionResult | None:
    """Return manually-created captions if available, else auto-generated
    ones, else None if the video has no captions at all (or they're
    disabled/unreachable).
    """
    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(video_id)
    except VideoUnavailable as exc:
        raise VideoUnavailableError(
            "This video is private, deleted, or otherwise unavailable."
        ) from exc
    except TranscriptsDisabled:
        return None
    except CouldNotRetrieveTranscript:
        return None

    transcript = None
    is_generated = True
    try:
        transcript = transcript_list.find_manually_created_transcript(PREFERRED_LANGUAGES)
        is_generated = False
    except NoTranscriptFound:
        try:
            transcript = transcript_list.find_generated_transcript(PREFERRED_LANGUAGES)
            is_generated = True
        except NoTranscriptFound:
            # No English track in either flavor. As a last resort, grab
            # whatever manually-created track exists (any language) rather
            # than falling back to a lower-accuracy path unnecessarily.
            for t in transcript_list:
                transcript = t
                is_generated = t.is_generated
                break

    if transcript is None:
        return None

    try:
        fetched = transcript.fetch()
    except CouldNotRetrieveTranscript:
        return None

    segments = [
        {"start": snippet.start, "duration": snippet.duration, "text": snippet.text}
        for snippet in fetched
    ]
    if not segments:
        return None

    return CaptionResult(
        is_generated=is_generated,
        language_code=transcript.language_code,
        segments=segments,
    )
