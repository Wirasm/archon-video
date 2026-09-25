"""Download the chosen candidate for one beat.

Uses the round-1 pick when it found one, otherwise the round-2 pick.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.footage import pexels
from vidlib.node import artifacts_dir, emit, json_input, text_input

beat = json_input("beat")
if json_input("found"):
    choice, cands_file, reason, round_ = json_input("choice"), text_input("candidates"), text_input("reason"), 1
else:
    choice, cands_file, reason, round_ = json_input("choice_2"), text_input("candidates_2"), text_input("reason_2"), 2

candidates = json.loads(Path(cands_file).read_text()) if cands_file else []
if not 1 <= choice <= len(candidates):
    raise SystemExit(f"{beat['id']}: no usable pick (choice {choice} of {len(candidates)} candidates in round {round_})")
c = candidates[choice - 1]

clip = artifacts_dir() / "beats" / beat["id"] / f"pexels-{c['id']}.mp4"
pexels.download(c["file_url"], clip)
emit(
    {
        "id": beat["id"],
        "source": "stock",
        "clip": str(clip),
        "provenance": {
            "provider": "pexels", "id": c["id"], "url": c["url"], "author": c["author"],
            "author_url": c["author_url"], "query": c["query"], "round": round_,
            "file": f"{c['file_width']}x{c['file_height']}",
        },
        "reason": reason,
    }
)
