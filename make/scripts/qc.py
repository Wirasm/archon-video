"""Measure the rendered video and check it for repeated shots.

Global failures fail the run after qc.json is written. Per-beat flags go to
retry-list (first pass) or are recorded (second pass).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import qc, variety
from vidlib import words as wordsmod
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, state_dir

RECENT_VIDEOS = 20

out = artifacts_dir()
cfg = load_resolved(out)
edl = json.loads((out / "edl.json").read_text())
words = wordsmod.read(out / "words.json")
rendered = json.loads((out / "render.json").read_text())
footage = json.loads((out / "footage.json").read_text())

# On the retry pass, keep the first pass's report next to the new one.
if rendered["retried"] and (out / "qc.json").exists():
    (out / "qc.json").rename(out / "qc-first.json")

report = qc.check(Path(rendered["video"]), cfg["format"], edl["beats"], words["words"], words["duration"], rendered["duration"])

# The same stock clip in two beats, or a shot that looks like another beat's,
# reads as filler: new footage once. A shot seen in a recent video is reported.
seen: dict[str, str] = {}
for r in footage:
    key = f"{r['provenance'].get('provider')}:{r['provenance'].get('id')}"
    if key in seen:
        report["beats"][r["id"]].append({"issue": f"same clip as {seen[key]}", "retry": True})
    seen.setdefault(key, r["id"])

hashes = {b["id"]: variety.dhash(out / "strips" / f"{b['id']}-2.jpg") for b in edl["beats"]}
for later, earlier in variety.repeats_within(hashes).items():
    if not any("same clip" in f["issue"] for f in report["beats"][later]):
        report["beats"][later].append({"issue": f"looks like the shot in {earlier}", "retry": True})
library_file = state_dir() / "library.jsonl"
library = [json.loads(line) for line in library_file.read_text().splitlines() if line.strip()] if library_file.exists() else []
for bid, run in variety.repeats_across(hashes, library[-RECENT_VIDEOS:]).items():
    report["beats"][bid].append({"issue": f"looks like a shot in recent video {run}", "retry": False})
report["frame_hashes"] = hashes

(out / "qc.json").write_text(json.dumps(report, indent=1))
if not report["global_ok"]:
    raise SystemExit("QC failed:\n- " + "\n- ".join(report["global_failures"]))
flagged = {k: [f["issue"] for f in v] for k, v in report["beats"].items() if v}
emit({"passed": True, "flagged_beats": flagged, "measurements": report["measurements"]})
