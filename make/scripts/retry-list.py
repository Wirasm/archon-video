"""Collect the beats that get new footage once: vision-flagged and QC-flagged.

Each carries a fix note for the picker and, as `avoid`, the clips this video
already uses so the retry cannot pick one of them again.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.node import artifacts_dir, emit, json_input

out = artifacts_dir()
edl = json.loads((out / "edl.json").read_text())
qc = json.loads((out / "qc.json").read_text())
footage = json.loads((out / "footage.json").read_text())
review = json_input("review")
(out / "qc-review.json").write_text(json.dumps(review, indent=1))

notes: dict[str, list[str]] = {}
for v in review["beats"]:
    if not v["ok"]:
        notes.setdefault(v["id"], []).append(f"{v['problem']} Instead: {v['fix']}".strip())
for bid, flags in qc["beats"].items():
    for f in flags:
        if f["retry"]:
            notes.setdefault(bid, []).append(f["issue"])

used = sorted({f"{r['provenance'].get('provider')}:{r['provenance'].get('id')}" for r in footage})
beats = [b | {"fix_note": " ".join(notes[b["id"]]), "avoid": used} for b in edl["beats"] if b["id"] in notes]
unknown = sorted(set(notes) - {b["id"] for b in edl["beats"]})
if unknown:
    raise SystemExit(f"review names beats that are not in the cut: {unknown}")
emit({"needs_retry": bool(beats), "beats": beats, "summary": review["summary"]})
