"""Search Pexels for one footage need and build a numbered contact sheet.

Round 1 uses the director's queries; round 2 uses the picker's `queries`.
Writes room/scout/<id>/sheet-<round>.jpg and candidates-<round>.json.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.config import load_resolved
from vidlib.footage import contact_sheet, pexels
from vidlib.node import artifacts_dir, emit, json_input, log, state_dir, text_input

RECENT_VIDEOS = 20

need = json_input("need")
round_ = int(text_input("round"))
queries = json_input("queries") if round_ > 1 else need["queries"]
queries = [q for q in queries if q.strip()] or [need["shows"]]

cfg = load_resolved(artifacts_dir())
fmt = cfg["format"]
out = artifacts_dir() / "room" / "scout" / need["id"]
out.mkdir(parents=True, exist_ok=True)

# Clips used by recent videos stay out of the candidates: repeated footage is
# what reads as filler, and what YouTube's inauthentic-content policy targets.
library_file = state_dir() / "library.jsonl"
rows = [json.loads(line) for line in library_file.read_text().splitlines() if line.strip()] if library_file.exists() else []
refs = {ref for row in rows[-RECENT_VIDEOS:] for ref in row.get("footage", [])}
avoid = {ref.split(":", 1)[1] for ref in refs if ref.startswith("pexels:")}
candidates = [c.to_dict() for c in pexels.search(queries, float(need["min_seconds"]), fmt["width"], fmt["height"], avoid=avoid)]
log(f"{need['id']} round {round_}: {len(candidates)} candidates for {queries}")
cands_file = out / f"candidates-{round_}.json"
cands_file.write_text(json.dumps(candidates, indent=1))
sheet = out / f"sheet-{round_}.jpg"
if candidates:
    contact_sheet.build(candidates, sheet, fmt["width"], fmt["height"])
emit({"sheet": str(sheet) if candidates else "", "candidates_file": str(cands_file), "count": len(candidates)})
