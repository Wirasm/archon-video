"""Render the editor's composition exactly as written, then master it.

HyperFrames renders edit/index.html. Mastering changes nothing the editor
decided: the audio is normalised to the loudness target (-14 LUFS, -1 dBTP)
and the picture re-encoded to the delivery spec. The SRT sidecar follows the
narration's place on the composition's timeline.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import captions, hyperframes, media
from vidlib import words as wordsmod
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, log

out = artifacts_dir()
cfg = load_resolved(out)
edit = out / "edit"

proc = hyperframes.run(["timeline", "--json"], edit, timeout=300)
if proc.returncode != 0:
    raise SystemExit(f"hyperframes timeline failed:\n{proc.stderr[-2000:]}")
timeline = json.loads(proc.stdout)["timeline"]
narration = next((r for t in timeline["tracks"] for r in t["rows"] if (r.get("src") or "").endswith("narration.wav")), None)

started = time.monotonic()
raw = edit / "render.mp4"
proc = hyperframes.run(
    ["render", "--quality", "delivery", "--fps", str(cfg["format"]["fps"]), "--output", str(raw)], edit, timeout=7200
)
render_s = time.monotonic() - started
if proc.returncode != 0 or not raw.exists():
    raise SystemExit(f"hyperframes render failed:\n{(proc.stdout + proc.stderr)[-3000:]}")
summary = [line.strip() for line in proc.stdout.splitlines() if "rendered in" in line or "capture" in line][-2:]
log("\n".join(summary))

audio = out / "mix-raw.wav"
media.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-vn", "-ac", "2", str(audio)])
mastered = out / "mix.wav"
loudness = media.loudnorm_two_pass(audio, mastered)
audio.unlink()
video = out / "video.mp4"
media.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-i", str(mastered),
           "-map", "0:v", "-map", "1:a", "-r", str(cfg["format"]["fps"]), *media.ENCODE, "-shortest", str(video)])

srt = None
if narration:
    words = wordsmod.read(out / "words.json")
    srt = out / "captions.srt"
    srt.write_text(captions.build_srt(words["words"], offset=float(narration["absStart"])))

info = {
    "video": str(video),
    "srt": str(srt) if srt else None,
    "duration": round(float(timeline["duration"]), 3),
    "render_seconds": round(render_s, 1),
    "render_summary": " | ".join(summary),
    "loudness_before": {k: loudness[k] for k in ("input_i", "input_tp", "input_lra")},
}
(out / "render.json").write_text(json.dumps(info, indent=1))
emit(info)
