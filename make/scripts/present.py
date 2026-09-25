"""Lay the three scripts out for the pick gate, best-ranked hook first."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.node import artifacts_dir, emit, json_input, text_input

top = json_input("top")
by_hook = {s["hook_id"]: s for s in json_input("scripts")}
order = [by_hook[h["id"]] for h in top if h["id"] in by_hook]
order += [s for s in by_hook.values() if s not in order]

blocks = []
for n, s in enumerate(order, 1):
    words = len(s["narration"].split())
    blocks.append(
        f"### Script {n}: {s['title']}\n"
        f"Overlay: {s['overlay']}\n"
        f"About {words / 2.5:.0f} s ({words} words)\n\n"
        f"{s['narration']}\n\n"
        f"_{s['notes']}_"
    )
text = "\n\n".join(blocks) + "\n\n#### Hook tournament\n" + text_input("table")
(artifacts_dir() / "scripts.md").write_text(text + "\n")
(artifacts_dir() / "scripts.json").write_text(json.dumps(order, indent=1))
emit({"text": text, "ordered": order})
