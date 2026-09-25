"""Turn the beat plan into cut times and write edl.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import words as wordsmod
from vidlib.config import load_resolved
from vidlib.edl import PlanError, build, table
from vidlib.node import artifacts_dir, emit, json_input

out = artifacts_dir()
cfg = load_resolved(out)
plan = json_input("plan")
words = wordsmod.read(out / "words.json")
try:
    beats = build(plan["beats"], words["words"], words["duration"], cfg["format"]["fps"])
except PlanError as err:
    raise SystemExit(f"unusable beat plan: {err}")
mood = plan.get("mood") if plan.get("mood") in cfg["music"]["moods"] else None
edl = {"beats": beats, "mood": mood, "total": beats[-1]["end"]}
(out / "edl.json").write_text(json.dumps(edl, indent=1))
emit(edl | {"table": table(beats)})
