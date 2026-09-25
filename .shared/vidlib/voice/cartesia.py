"""Cartesia TTS over SSE with native word timestamps.

`/tts/sse` with `add_timestamps: true` streams audio chunks and word timings in
one response; `/tts/bytes` has no timings.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
from pathlib import Path

import requests

API = "https://api.cartesia.ai/tts/sse"
API_VERSION = "2026-03-01"
SAMPLE_RATE = 48000


def synthesize(text: str, voice_id: str, model: str, out_wav: Path) -> tuple[float, list[tuple[str, float, float]]]:
    """Write a mono 48 kHz wav; return (duration, [(token, start, end)])."""
    resp = requests.post(
        API,
        headers={
            "X-API-Key": os.environ["CARTESIA_API_KEY"],
            "Cartesia-Version": API_VERSION,
            "Content-Type": "application/json",
        },
        json={
            "model_id": model,
            "transcript": text,
            "voice": {"mode": "id", "id": voice_id},
            # SSE serves raw PCM only; ffmpeg wraps it below.
            "output_format": {"container": "raw", "encoding": "pcm_f32le", "sample_rate": SAMPLE_RATE},
            "language": "en",
            "add_timestamps": True,
        },
        timeout=300,
        stream=True,
    )
    if not resp.ok:
        raise SystemExit(f"Cartesia returned {resp.status_code}: {resp.text[:400]}")

    pcm = bytearray()
    timed: list[tuple[str, float, float]] = []
    for line in resp.iter_lines():
        if not line or not line.startswith(b"data:"):
            continue
        event = json.loads(line[5:].strip())
        kind = event.get("type")
        if kind == "chunk":
            pcm += base64.b64decode(event["data"])
        elif kind == "timestamps":
            wt = event.get("word_timestamps") or {}
            timed += list(zip(wt.get("words", []), wt.get("start", []), wt.get("end", [])))
        elif kind == "error":
            raise SystemExit(f"Cartesia stream error: {event.get('error')}")

    if not pcm:
        raise SystemExit("Cartesia returned no audio")
    if not timed:
        raise SystemExit("Cartesia returned no word timestamps; captions and cuts would be guesswork")

    raw = out_wav.with_suffix(".pcm")
    raw.write_bytes(bytes(pcm))
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "1",
         "-i", str(raw), "-c:a", "pcm_s16le", str(out_wav)],
        check=True,
    )
    raw.unlink()
    return len(pcm) / 4 / SAMPLE_RATE, timed
