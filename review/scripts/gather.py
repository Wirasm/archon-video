"""Find the video to review and bundle what the reviewer reads.

`latest` means the newest stored video that has not been reviewed. A video
that was already reviewed is reviewed again only when named by run id.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import playbook
from vidlib.node import artifacts_dir, emit, state_dir, text_input


def rows(name: str) -> list[dict]:
    p = state_dir() / name
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.exists() else []


library = rows("library.jsonl")
reviewed = {r["video_run"] for r in rows("reviews.jsonl")}
wanted = text_input("video", "latest").strip()
if not library:
    raise SystemExit("no stored videos yet; run make first")
if wanted == "latest":
    pending = [r for r in library if r["run_id"] not in reviewed]
    if not pending:
        raise SystemExit("every stored video has been reviewed; name one by run id to review it again")
    row = pending[-1]
else:
    matches = [r for r in library if r["run_id"].startswith(wanted)]
    if len(matches) != 1:
        raise SystemExit(f"{wanted!r} matches {len(matches)} stored videos; give a longer run id")
    row = matches[0]

d = Path(row["path"])
manifest = json.loads((d / "manifest.json").read_text())
script = json.loads((d / "script.json").read_text())
qc = json.loads((d / "qc.json").read_text())
cfg = json.loads((d / "config.json").read_text())
treatment = (d / "room" / "director" / "treatment.md").read_text() if (d / "room" / "director" / "treatment.md").exists() else "(none)"
events = playbook.load(state_dir() / "playbook.jsonl")
rules = playbook.active(events)

parts = [
    f"# Video {row['run_id']}",
    f"Length: {manifest['duration']:.1f} s. Made with playbook v{manifest.get('playbook_version', 0)}; "
    f"the playbook is now v{playbook.version(events)}. Videos stored for this project: {len(library)}.",
    "## The brief\n" + manifest.get("brief", "(none)"),
    "## Brand\n```json\n" + json.dumps(cfg["brand"], indent=1) + "\n```",
    f"## Script: {script['title']}\n\n{script['narration']}",
    "## What the person said when picking the script\n" + (manifest.get("pick_comment") or "(no comment)"),
    "## The director's treatment\n" + treatment,
    "## What the editor says it did\n" + manifest.get("edit_summary", "(none)"),
    f"The composition is `{d / 'edit' / 'index.html'}`; room notes are under `{d / 'room'}`.",
    "## Measured QC\n" + json.dumps({"measurements": qc["measurements"], "flags": qc.get("flags", [])}, indent=1),
    "## Active playbook lessons\n" + ("\n".join(f"- {r['rule_id']}: {r['text']}" for r in rules.values()) or "(none yet)"),
]

bundle = artifacts_dir() / "review-bundle.md"
bundle.parent.mkdir(parents=True, exist_ok=True)
bundle.write_text("\n\n".join(parts) + "\n")
# Lessons are not split by kind any more; the scope field stays for R5.
emit({"run_id": row["run_id"], "kind": "all", "bundle": bundle.read_text(),
      "sheets": sorted(str(p) for p in (d / "frames").glob("review-*.jpg"))})
