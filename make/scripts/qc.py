"""Measure the mastered video and compare it with recent videos.

Spec failures fail the run after qc.json is written. Flags and look-alike
shots from recent videos are recorded for the operator and the reviewer.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import qc, sheets, variety
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, state_dir

RECENT_VIDEOS = 20
SAMPLE_EVERY_S = 2.5

out = artifacts_dir()
cfg = load_resolved(out)
rendered = json.loads((out / "render.json").read_text())
video = Path(rendered["video"])

report = qc.check(video, cfg["format"], rendered["duration"])

# Frames every few seconds: the review sheets for `review`, and the hashes the
# variety check compares with recent videos.
frames_dir = out / "frames"
frames_dir.mkdir(exist_ok=True)
times = [t * SAMPLE_EVERY_S + 0.5 for t in range(int(rendered["duration"] // SAMPLE_EVERY_S))]
paths = [sheets.frame(video, t, frames_dir / f"t{t:06.2f}.jpg") for t in times]
sheets.build([(f"{t:.1f}s", [p]) for t, p in zip(times, paths)], frames_dir, "review", per_sheet=12, columns=6)
hashes = {f"{t:.1f}s": variety.dhash(p) for t, p in zip(times, paths)}
library_file = state_dir() / "library.jsonl"
library = [json.loads(line) for line in library_file.read_text().splitlines() if line.strip()] if library_file.exists() else []
for at, run in variety.repeats_across(hashes, library[-RECENT_VIDEOS:]).items():
    report["flags"].append({"t": float(at[:-1]), "issue": f"looks like a shot in recent video {run}"})
report["frame_hashes"] = list(hashes.values())

(out / "qc.json").write_text(json.dumps(report, indent=1))
if not report["global_ok"]:
    raise SystemExit("QC failed:\n- " + "\n- ".join(report["global_failures"]))
emit({"passed": True, "flags": [f"{f['t']:.1f}s {f['issue']}" for f in report["flags"]], "measurements": report["measurements"]})
