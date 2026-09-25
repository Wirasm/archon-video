"""Turn whatever a provider returns into the one narration format: 48 kHz mono wav."""

from __future__ import annotations

import subprocess
from pathlib import Path

SAMPLE_RATE = 48000


def to_wav(src: Path, dest: Path, raw_format: tuple[str, int] | None = None) -> float:
    """Convert `src` (any container, or raw PCM given (sample format, rate)) and return seconds."""
    inputs = ["-f", raw_format[0], "-ar", str(raw_format[1]), "-ac", "1"] if raw_format else []
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", str(src),
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dest)],
        check=True,
    )
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dest)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out)
