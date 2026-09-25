"""Measured QC on the finished video.

Only what can be measured. Global failures mean the render is broken and the
run fails. Per-beat flags are {"issue", "retry"}: `retry` flags send the beat
back for new footage once; the rest are reported only.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import media

# ffmpeg detection filters log machine lines such as "black_start:1.2 black_end:1.6".
BLACK = re.compile(r"black_start:([\d.]+) black_end:([\d.]+)")
FREEZE = re.compile(r"freezedetect\.freeze_start: ([\d.]+)")
SILENCE_START = re.compile(r"silence_start: ([\d.]+)")

CUT_SYNC_S = 0.15
DRIFT_S = 0.5
LONG_SHOT_S = 5.0


def _moov_before_mdat(path: Path) -> bool:
    """+faststart puts the moov atom before mdat, so playback starts before download ends."""
    with path.open("rb") as fh:
        while True:
            header = fh.read(8)
            if len(header) < 8:
                return False
            size = int.from_bytes(header[:4], "big")
            kind = header[4:8]
            if kind == b"moov":
                return True
            if kind == b"mdat":
                return False
            if size == 1:
                size = int.from_bytes(fh.read(8), "big")
                fh.seek(size - 16, 1)
            elif size < 8:
                return False
            else:
                fh.seek(size - 8, 1)


def _beat_at(beats: list[dict], t: float) -> str:
    for b in beats:
        if b["start"] <= t < b["end"]:
            return b["id"]
    return beats[-1]["id"]


def check(video: Path, fmt: dict, beats: list[dict], words: list, narration_s: float, expected_s: float) -> dict:
    failures: list[str] = []
    flags: dict[str, list[dict]] = {b["id"]: [] for b in beats}
    meta = media.probe(video)
    v = next((s for s in meta["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)
    if not v or not a:
        failures.append("missing a video or audio stream")
        return {"global_ok": False, "global_failures": failures, "beats": flags, "measurements": {}}

    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den or 1)
    duration = float(meta["format"]["duration"])
    if (v["width"], v["height"]) != (fmt["width"], fmt["height"]):
        failures.append(f"resolution {v['width']}x{v['height']}, expected {fmt['width']}x{fmt['height']}")
    if not fmt["fps"] - 1 <= fps <= fmt["fps"] + 1:
        failures.append(f"frame rate {fps:.2f}")
    if v.get("codec_name") != "h264" or v.get("pix_fmt") != "yuv420p":
        failures.append(f"video is {v.get('codec_name')}/{v.get('pix_fmt')}, expected h264/yuv420p")
    if not _moov_before_mdat(video):
        failures.append("moov atom is not at the front (+faststart missing)")
    if abs(duration - expected_s) > DRIFT_S:
        failures.append(f"duration {duration:.2f}s vs expected {expected_s:.2f}s")
    if duration > fmt["max_duration_s"]:
        failures.append(f"duration {duration:.1f}s exceeds the {fmt['name']} ceiling of {fmt['max_duration_s']}s")

    loud = media.measure_loudness(video)
    integrated, true_peak = float(loud["input_i"]), float(loud["input_tp"])
    if abs(integrated - media.LOUDNESS["I"]) > 1.0:
        failures.append(f"integrated loudness {integrated:.1f} LUFS, expected -14 +/- 1")
    if true_peak > media.LOUDNESS["TP"]:
        failures.append(f"true peak {true_peak:.1f} dBTP, expected <= -1")

    silence_log = media.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-map", "0:a",
                             "-af", "silencedetect=n=-45dB:d=0.7", "-f", "null", "-"])
    dead_air = [float(s) for s in SILENCE_START.findall(silence_log) if float(s) < narration_s]
    if dead_air:
        failures.append(f"dead air inside the narration at {', '.join(f'{s:.1f}s' for s in dead_air)}")

    picture_log = media.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-map", "0:v",
                             "-vf", "blackdetect=d=0.3:pix_th=0.10,freezedetect=n=0.003:d=0.6",
                             "-f", "null", "-"])
    for start, end in BLACK.findall(picture_log):
        flags[_beat_at(beats, float(start))].append({"issue": f"black frames {float(start):.1f}-{float(end):.1f}s", "retry": True})
    for start in FREEZE.findall(picture_log):
        flags[_beat_at(beats, float(start))].append({"issue": f"frozen picture from {float(start):.1f}s", "retry": True})

    word_starts = [w.start for w in words]
    fps_out = fmt["fps"]
    for b in beats[1:]:
        cut = round(b["start"] * fps_out) / fps_out
        nearest = min(abs(cut - s) for s in word_starts)
        if nearest > CUT_SYNC_S:
            failures.append(f"cut at {cut:.2f}s ({b['id']}) is {nearest * 1000:.0f} ms from any word start")
    for b in beats:
        if b["duration"] > LONG_SHOT_S:
            flags[b["id"]].append({"issue": f"long shot ({b['duration']:.1f}s)", "retry": False})

    return {
        "global_ok": not failures,
        "global_failures": failures,
        "beats": flags,
        "measurements": {
            "width": v["width"], "height": v["height"], "fps": round(fps, 2), "duration": round(duration, 3),
            "integrated_lufs": integrated, "true_peak_dbtp": true_peak, "beats": len(beats),
        },
    }
