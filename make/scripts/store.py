"""Store the finished video and record it in the project's library.

Default destination: $STATE_DIR/video/videos/<run-id>/ with a `latest` link.
`output.dir` in the config replaces the videos/ folder.
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
footage = json_input("footage")
qc = json.loads((out / "qc.json").read_text())
rendered = json.loads((out / "render.json").read_text())
words = json.loads((out / "words.json").read_text())

root = Path(cfg["output_dir"]) if cfg["output_dir"] else state_dir() / "videos"
root.mkdir(parents=True, exist_ok=True)
rid = run_id()
staging = root / f".{rid}.partial"
dest = root / rid
if staging.exists():
    shutil.rmtree(staging)
staging.mkdir()

for name in ("video.mp4", "captions.srt", "edl.json", "qc.json", "words.json", "narration.wav", "config.json"):
    shutil.copy2(out / name, staging / name)
(staging / "copy.json").write_text(json.dumps(copy, indent=1))
(staging / "script.json").write_text(json.dumps(pick, indent=1))
manifest = {
    "run_id": rid,
    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "topic": text_input("topic"),
    "kind": cfg["kind"],
    "format": cfg["format"]["name"],
    "config_file": cfg["config_file"],
    "config_digest": cfg["config_digest"],
    "voice": {"provider": words["provider"], "model": words["model"], "voice_id": cfg["voice"]["voice_id"], "timings": words["source"]},
    "music": {"track": rendered["music_track"], "mood": rendered["mood"]},
    "duration": rendered["duration"],
    "footage": [{"beat": r["id"], "source": r["source"], **r["provenance"]} for r in footage],
    "qc": {"passed": qc["global_ok"], "flagged_beats": {k: v for k, v in qc["beats"].items() if v}},
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
        "run_id": rid, "created_at": manifest["created_at"], "kind": cfg["kind"], "topic": manifest["topic"],
        "title": pick["title"], "hook": pick["narration"].split(".")[0], "path": str(dest),
        "config_digest": cfg["config_digest"], "music_track": rendered["music_track"],
        "footage": [f"{r['provenance'].get('provider')}:{r['provenance'].get('id')}" for r in footage],
        "qc_passed": qc["global_ok"],
    }) + "\n")

emit({"path": str(dest), "video": str(dest / "video.mp4"), "latest": str(latest), "qc_passed": qc["global_ok"],
      "flagged_beats": manifest["qc"]["flagged_beats"]})
