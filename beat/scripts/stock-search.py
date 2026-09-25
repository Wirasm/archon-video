"""Search Pexels for one beat and build a numbered contact sheet.

Round 1 uses the planner's queries; round 2 uses the picker's `queries`.
Writes beats/<id>/sheet-<round>.jpg and candidates-<round>.json.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.config import load_resolved
from vidlib.footage import contact_sheet, pexels
from vidlib.node import artifacts_dir, emit, json_input, log, state_dir, text_input

RECENT_VIDEOS = 20

beat = json_input("beat")
round_ = int(text_input("round"))
queries = json_input("queries") if round_ > 1 else beat["queries"]
queries = [q for q in queries if q.strip()] or [beat["visual"]]

cfg = load_resolved(artifacts_dir())
fmt = cfg["format"]
out = artifacts_dir() / "beats" / beat["id"]
out.mkdir(parents=True, exist_ok=True)

# Clips used by recent videos, and on a retry the clips this video already uses,
# stay out of the candidates: repeated footage is what reads as filler.
library_file = state_dir() / "library.jsonl"
rows = [json.loads(line) for line in library_file.read_text().splitlines() if line.strip()] if library_file.exists() else []
refs = {ref for row in rows[-RECENT_VIDEOS:] for ref in row.get("footage", [])} | set(beat.get("avoid", []))
avoid = {ref.split(":", 1)[1] for ref in refs if ref.startswith("pexels:")}
candidates = [c.to_dict() for c in pexels.search(queries, beat["duration"], fmt["width"], fmt["height"], avoid=avoid)]
log(f"{beat['id']} round {round_}: {len(candidates)} candidates for {queries}")
# A retry pass keeps the first pass's files for review.
prefix = "retry-" if beat.get("fix_note") else ""
cands_file = out / f"{prefix}candidates-{round_}.json"
cands_file.write_text(json.dumps(candidates, indent=1))
sheet = out / f"{prefix}sheet-{round_}.jpg"
if candidates:
    contact_sheet.build(candidates, sheet, fmt["width"], fmt["height"])
emit({"sheet": str(sheet) if candidates else "", "candidates_file": str(cands_file), "count": len(candidates)})
