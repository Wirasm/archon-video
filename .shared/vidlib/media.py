"""ffmpeg and ffprobe helpers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

LOUDNESS = {"I": -14.0, "TP": -1.0, "LRA": 11.0}
# Normalise with extra true-peak headroom: the AAC encode after loudnorm raises
# peaks by a few tenths of a dB, and QC checks the encoded file against TP.
TP_HEADROOM = 0.5


def run(args: list[str], cwd: Path | None = None) -> str:
    """Run ffmpeg/ffprobe; return stderr. Fail with ffmpeg's own error text."""
    proc = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 0:
        raise SystemExit(f"{args[0]} failed ({proc.returncode}):\n{proc.stderr[-3000:]}")
    return proc.stderr


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def _last_json_object(text: str) -> dict:
    """loudnorm prints its measurement as a JSON object at the end of stderr."""
    start = text.rfind("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise SystemExit("loudnorm printed no measurement")
    return json.loads(text[start:end + 1])


def measure_loudness(path: Path) -> dict:
    stderr = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", f"loudnorm=I={LOUDNESS['I']}:TP={LOUDNESS['TP']}:LRA={LOUDNESS['LRA']}:print_format=json",
        "-f", "null", "-",
    ])
    return _last_json_object(stderr)


def loudnorm_two_pass(src: Path, dest: Path) -> dict:
    """Normalise to -14 LUFS integrated, -1 dBTP, with measured values (linear mode)."""
    m = measure_loudness(src)
    target = f"I={LOUDNESS['I']}:TP={LOUDNESS['TP'] - TP_HEADROOM}:LRA={LOUDNESS['LRA']}"
    measured = (
        f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
        f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
    )
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
        "-af", f"loudnorm={target}:{measured}:linear=true,aresample=48000",
        "-ar", "48000", "-ac", "2", str(dest),
    ])
    return m
