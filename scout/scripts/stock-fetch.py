"""Download the chosen candidate for one need and conform it into edit/assets/.

Uses the round-1 pick when it found one, otherwise the round-2 pick.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.config import load_resolved
from vidlib.conform import conform
from vidlib.footage import pexels
from vidlib.node import artifacts_dir, emit, json_input, text_input

need = json_input("need")
if json_input("found"):
    choice, cands_file, reason, round_ = json_input("choice"), text_input("candidates"), text_input("reason"), 1
else:
    choice, cands_file, reason, round_ = json_input("choice_2"), text_input("candidates_2"), text_input("reason_2"), 2

candidates = json.loads(Path(cands_file).read_text()) if cands_file else []
if not 1 <= choice <= len(candidates):
    raise SystemExit(f"{need['id']}: no usable pick (choice {choice} of {len(candidates)} candidates in round {round_})")
c = candidates[choice - 1]

out = artifacts_dir()
raw = out / "room" / "scout" / need["id"] / f"pexels-{c['id']}.mp4"
pexels.download(c["file_url"], raw)
assets = out / "edit" / "assets"
assets.mkdir(parents=True, exist_ok=True)
clip = assets / f"{need['id']}.mp4"
duration = conform(raw, clip, load_resolved(out)["format"])
raw.unlink()
(out / "room" / "scout" / need["id"] / "pick.md").write_text(
    f"Picked Pexels {c['id']} ({c['url']}, by {c['author']}) in round {round_}.\n\n{reason}\n"
)
emit(
    {
        "id": need["id"],
        "source": "stock",
        "clip": f"assets/{need['id']}.mp4",
        "duration": round(duration, 3),
        "provenance": {
            "provider": "pexels", "id": c["id"], "url": c["url"], "author": c["author"],
            "author_url": c["author_url"], "query": c["query"], "round": round_,
            "file": f"{c['file_width']}x{c['file_height']}",
        },
        "reason": reason,
    }
)
