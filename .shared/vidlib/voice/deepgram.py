"""Deepgram Aura TTS. Audio only: the align node times the words."""

from __future__ import annotations

import os
from pathlib import Path

import requests

from . import Speech
from ._audio import to_wav

API = "https://api.deepgram.com/v1/speak"
MAX_CHARS = 2000  # Deepgram's per-request text limit


def synthesize(text: str, voice: dict, out_wav: Path) -> Speech:
    if len(text) > MAX_CHARS:
        raise SystemExit(f"Deepgram speaks at most {MAX_CHARS} characters per request; the script has {len(text)}")
    resp = requests.post(
        API,
        # The Aura model id names the voice, e.g. aura-2-thalia-en.
        params={"model": voice["model"] or "aura-2-thalia-en", "encoding": "linear16", "sample_rate": 48000, "container": "wav"},
        headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}", "Content-Type": "application/json"},
        json={"text": text},
        timeout=300,
    )
    if not resp.ok:
        raise SystemExit(f"Deepgram returned {resp.status_code}: {resp.text[:400]}")
    raw = out_wav.with_suffix(".dg.wav")
    raw.write_bytes(resp.content)
    duration = to_wav(raw, out_wav)
    raw.unlink()
    return Speech(duration, None)
