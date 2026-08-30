"""High-accuracy fallback: download audio with yt-dlp, transcribe with
OpenAI's Whisper API. Used when official captions are missing or are
auto-generated (lower quality) and Whisper is configured.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import yt_dlp
from openai import OpenAI

from . import config
from .exceptions import NoAudioError, TranscriptionFailedError, VideoUnavailableError


def _download_audio(video_id: str, workdir: Path) -> Path:
    """Download best-audio and transcode to a modest-bitrate mono MP3 via
    ffmpeg (through yt-dlp's postprocessor) to keep file size manageable
    for long videos.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_template = str(workdir / "audio.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",  # kbps - plenty for speech, keeps size down
            }
        ],
        "postprocessor_args": {
            "ffmpeg": ["-ac", "1"],  # mono
        },
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        message = str(exc).lower()
        if "private" in message or "unavailable" in message or "removed" in message:
            raise VideoUnavailableError(
                "This video is private, deleted, or otherwise unavailable."
            ) from exc
        raise TranscriptionFailedError(f"Could not download audio: {exc}") from exc

    audio_path = workdir / "audio.mp3"
    if not audio_path.exists():
        raise NoAudioError("This video doesn't appear to have an audio track.")
    return audio_path


def _split_audio(audio_path: Path, workdir: Path, chunk_seconds: int) -> list[Path]:
    """Split into fixed-length chunks with ffmpeg's segment muxer (stream
    copy - fast, no re-encode) so each upload stays under Whisper's size
    limit.
    """
    chunk_dir = workdir / "chunks"
    chunk_dir.mkdir(exist_ok=True)
    pattern = str(chunk_dir / "chunk_%04d.mp3")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-c",
        "copy",
        "-loglevel",
        "error",
        pattern,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise TranscriptionFailedError(
            "ffmpeg is not installed. Install ffmpeg to use the Whisper fallback."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise TranscriptionFailedError(f"Failed to split audio: {exc.stderr}") from exc

    return sorted(chunk_dir.glob("chunk_*.mp3"))


def _chunks_for_upload(audio_path: Path, workdir: Path) -> list[Path]:
    size = audio_path.stat().st_size
    if size <= config.WHISPER_MAX_UPLOAD_BYTES:
        return [audio_path]

    # Estimate a chunk length that keeps each piece under the size cap,
    # then let ffmpeg cut on that interval.
    duration_probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        total_duration = float(duration_probe.stdout.strip())
    except ValueError:
        total_duration = 0.0

    if total_duration > 0:
        bytes_per_second = size / total_duration
        safe_chunk_seconds = max(
            60, math.floor(config.WHISPER_MAX_UPLOAD_BYTES / bytes_per_second * 0.9)
        )
        chunk_seconds = min(config.WHISPER_CHUNK_SECONDS, safe_chunk_seconds)
    else:
        chunk_seconds = config.WHISPER_CHUNK_SECONDS

    return _split_audio(audio_path, workdir, chunk_seconds)


def transcribe_via_whisper(video_id: str) -> list[dict]:
    """Returns segments: [{"start": float, "duration": float, "text": str}, ...]"""
    if not config.OPENAI_API_KEY:
        raise TranscriptionFailedError(
            "Whisper fallback requested but OPENAI_API_KEY is not configured."
        )

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    workdir = config.TMP_DIR / f"whisper_{video_id}_{uuid.uuid4().hex[:8]}"
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        audio_path = _download_audio(video_id, workdir)
        chunks = _chunks_for_upload(audio_path, workdir)

        segments: list[dict] = []
        offset = 0.0
        for chunk_path in chunks:
            with open(chunk_path, "rb") as f:
                try:
                    result = client.audio.transcriptions.create(
                        model=config.WHISPER_MODEL,
                        file=f,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                    )
                except Exception as exc:  # noqa: BLE001 - surface as a clean app error
                    raise TranscriptionFailedError(
                        f"Whisper transcription failed: {exc}"
                    ) from exc

            chunk_segments = getattr(result, "segments", None) or []
            chunk_duration = 0.0
            for seg in chunk_segments:
                start = float(seg.start) + offset
                duration = max(0.0, float(seg.end) - float(seg.start))
                segments.append({"start": start, "duration": duration, "text": seg.text.strip()})
                chunk_duration = max(chunk_duration, float(seg.end))

            if not chunk_segments:
                # Fall back to whole-chunk text with no fine-grained timing.
                text = (getattr(result, "text", "") or "").strip()
                if text:
                    segments.append({"start": offset, "duration": 0.0, "text": text})

            offset += chunk_duration if chunk_duration else config.WHISPER_CHUNK_SECONDS

        if not segments:
            raise TranscriptionFailedError("Whisper returned an empty transcript.")

        return segments
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
