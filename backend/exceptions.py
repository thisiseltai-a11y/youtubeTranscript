"""Typed errors mapped to HTTP status codes in main.py."""
from __future__ import annotations


class TranscriptAppError(Exception):
    """Base class for all handled application errors."""

    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidURLError(TranscriptAppError):
    status_code = 400


class VideoUnavailableError(TranscriptAppError):
    """Private, deleted, region-locked, or otherwise unreachable video."""

    status_code = 404


class YouTubeBlockedError(TranscriptAppError):
    """YouTube is rate-limiting/blocking requests from this server's IP
    (common on cloud/datacenter IPs). Not the same thing as the video
    actually being unavailable - keep this distinct so the error message
    doesn't lie about the cause.
    """

    status_code = 503


class VideoTooLongError(TranscriptAppError):
    status_code = 422


class NoAudioError(TranscriptAppError):
    """Video has no audio track to transcribe (and no captions either)."""

    status_code = 422


class TranscriptionFailedError(TranscriptAppError):
    """Both the captions path and the Whisper fallback failed."""

    status_code = 502


class RewriteError(TranscriptAppError):
    status_code = 502


class LotSaveError(TranscriptAppError):
    """The Lot's shared state couldn't be written to storage."""

    status_code = 502
