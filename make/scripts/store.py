"""Store the finished video with everything that made it, and record it.

Default destination: $STATE_DIR/video/videos/<run-id>/ with a `latest` link.
`output.dir` in the config replaces the videos/ folder. The bundle keeps the
composition, the room notes and the review sheets, so a review, or a person,
can see how the edit was made.
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, json_input, run_id, state_dir, text_input

out = artifacts_dir()
cfg = load_resolved(out)
pick = json_input("pick")
copy = json_input("copy")
editor = json_input("editor")
qc = json.loads((out / "qc.json").read_text())
rendered = json.loads((out / "render.json").read_text())
words = json.loads((out / "words.json").read_text())
footage = json.loads((out / "room" / "scout" / "footage.json").read_text())

root = Path(cfg["output_dir"]) if cfg["output_dir"] else state_dir() / "videos"
root.mkdir(parents=True, exist_ok=True)
rid = run_id()
staging = root / f".{rid}.partial"
dest = root / rid
if staging.exists():
    shutil.rmtree(staging)
staging.mkdir()

for name in ("video.mp4", "captions.srt", "qc.json", "render.json", "words.json", "narration.wav", "config.json"):
    if (out / name).exists():
        shutil.copy2(out / name, staging / name)
(staging / "copy.json").write_text(json.dumps(copy, indent=1))
(staging / "script.json").write_text(json.dumps(pick, indent=1))
# The edit itself, without the media it points at (that is in the run's artifacts).
shutil.copytree(out / "edit", staging / "edit", ignore=shutil.ignore_patterns("assets", "*.mp4", "snapshots", "node_modules"))
shutil.copytree(out / "room", staging / "room", ignore=shutil.ignore_patterns("*.mp4", "frames"))
(staging / "frames").mkdir()
for sheet in (out / "frames").glob("review-*.jpg"):
    shutil.copy2(sheet, staging / "frames" / sheet.name)

manifest = {
    "run_id": rid,
    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "brief": cfg["brief"],
    "format": cfg["format"]["name"],
    "config_file": cfg["config_file"],
    "config_digest": cfg["config_digest"],
    "playbook_version": cfg["playbook_version"],
    "pick_comment": text_input("pick_comment", ""),
    "voice": {"provider": words["provider"], "model": words["model"], "voice_id": cfg["voice"]["voice_id"], "timings": words["source"]},
    "duration": rendered["duration"],
    "render": {"seconds": rendered["render_seconds"], "summary": rendered["render_summary"]},
    "edit_summary": editor["summary"],
    "footage": [{"need": r["id"], "source": r["source"], **r["provenance"]} for r in footage],
    "qc": {"passed": qc["global_ok"], "flags": qc["flags"]},
}
(staging / "manifest.json").write_text(json.dumps(manifest, indent=1))
if dest.exists():
    shutil.rmtree(dest)
staging.rename(dest)

latest = root / "latest"
tmp_link = root / ".latest.tmp"
if tmp_link.is_symlink() or tmp_link.exists():
    tmp_link.unlink()
tmp_link.symlink_to(rid)
os.replace(tmp_link, latest)

with (state_dir() / "library.jsonl").open("a") as fh:
    fh.write(json.dumps({
        "run_id": rid, "created_at": manifest["created_at"], "brief": cfg["brief"][:300],
        "title": pick["title"], "hook": pick["narration"].split(".")[0], "path": str(dest),
        "config_digest": cfg["config_digest"], "playbook_version": cfg["playbook_version"],
        "frame_hashes": qc["frame_hashes"],
        "footage": [f"{r['provenance'].get('provider')}:{r['provenance'].get('id')}" for r in footage],
        "qc_passed": qc["global_ok"],
    }) + "\n")

emit({"path": str(dest), "video": str(dest / "video.mp4"), "latest": str(latest), "qc_passed": qc["global_ok"],
      "playbook_version": cfg["playbook_version"], "flags": [f"{f['t']:.1f}s {f['issue']}" for f in qc["flags"]]})
