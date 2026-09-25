"""Measure the rendered video. Global failures fail the run after qc.json is written."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import qc
from vidlib import words as wordsmod
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, json_input

out = artifacts_dir()
cfg = load_resolved(out)
edl = json.loads((out / "edl.json").read_text())
words = wordsmod.read(out / "words.json")
rendered = json.loads((out / "render.json").read_text())

report = qc.check(Path(rendered["video"]), cfg["format"], edl["beats"], words["words"], words["duration"], rendered["duration"])

# The same stock clip in two beats reads as filler.
seen: dict[str, str] = {}
for r in json_input("footage"):
    key = f"{r['provenance'].get('provider')}:{r['provenance'].get('id')}"
    if key in seen:
        report["beats"][r["id"]].append(f"same footage as {seen[key]}")
    seen.setdefault(key, r["id"])

(out / "qc.json").write_text(json.dumps(report, indent=1))
if not report["global_ok"]:
    raise SystemExit("QC failed:\n- " + "\n- ".join(report["global_failures"]))
flagged = {k: v for k, v in report["beats"].items() if v}
emit({"passed": True, "flagged_beats": flagged, "measurements": report["measurements"]})
