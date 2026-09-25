"""Kokoro-82M through kokoro-onnx: free, local, Apache-2.0. Audio only.

The model and voice files download once into ~/.cache/archon-video/kokoro/.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

from . import Speech
from ._audio import to_wav

RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
FILES = ("kokoro-v1.0.onnx", "voices-v1.0.bin")


def _cache_dir() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    d = base / "archon-video" / "kokoro"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ensure_files() -> tuple[Path, Path]:
    d = _cache_dir()
    for name in FILES:
        dest = d / name
        if dest.exists():
            continue
        partial = dest.with_suffix(dest.suffix + ".partial")
        with requests.get(f"{RELEASE}/{name}", stream=True, timeout=600) as r:
            r.raise_for_status()
            with partial.open("wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        partial.rename(dest)
    return d / FILES[0], d / FILES[1]


def synthesize(text: str, voice: dict, out_wav: Path) -> Speech:
    import soundfile as sf
    from kokoro_onnx import Kokoro

    model, voices = _ensure_files()
    samples, rate = Kokoro(str(model), str(voices)).create(text, voice=voice["voice_id"] or "af_heart", lang="en-us")
    raw = out_wav.with_suffix(".kokoro.wav")
    sf.write(raw, samples, rate)
    duration = to_wav(raw, out_wav)
    raw.unlink()
    return Speech(duration, None)
