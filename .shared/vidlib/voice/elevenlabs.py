"""ElevenLabs TTS with character timings, grouped into words.

`/with-timestamps` returns base64 audio plus per-character start and end times
for the text as sent (`alignment`). Words are the runs of non-space characters.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import requests

from . import Speech, Timed
from ._audio import to_wav

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"


def group_words(chars: list[str], starts: list[float], ends: list[float]) -> Timed:
    words: Timed = []
    current, start, end = "", 0.0, 0.0
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if current:
                words.append((current, start, end))
            current = ""
            continue
        if not current:
            start = s
        current += ch
        end = e
    if current:
        words.append((current, start, end))
    return words


def synthesize(text: str, voice: dict, out_wav: Path) -> Speech:
    resp = requests.post(
        API.format(voice_id=voice["voice_id"]),
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
        json={"text": text, "model_id": voice["model"] or "eleven_multilingual_v2"},
        timeout=300,
    )
    if not resp.ok:
        raise SystemExit(f"ElevenLabs returned {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    alignment = data.get("alignment") or {}
    timed = group_words(
        alignment.get("characters", []),
        alignment.get("character_start_times_seconds", []),
        alignment.get("character_end_times_seconds", []),
    )
    if not timed:
        raise SystemExit("ElevenLabs returned no character alignment")
    mp3 = out_wav.with_suffix(".mp3")
    mp3.write_bytes(base64.b64decode(data["audio_base64"]))
    duration = to_wav(mp3, out_wav)
    mp3.unlink()
    return Speech(duration, timed)
