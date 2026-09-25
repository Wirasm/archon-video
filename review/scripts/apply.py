"""Apply the approved playbook change and record the review."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import playbook
from vidlib.node import emit, json_input, run_id, state_dir, text_input

review = json_input("review")
p = review
video_run, kind, comment = text_input("run_id"), text_input("kind"), text_input("comment", "")
provenance = {"video_run": video_run, "review_run": run_id(), "approver_comment": comment}
path = state_dir() / "playbook.jsonl"

rule_id = ""
if p["action"] != "none":
    try:
        event = playbook.append(path, p["action"], p["rule_id"], p["scope"], kind, p["text"], p["evidence"], provenance)
    except playbook.PlaybookError as err:
        raise SystemExit(f"the approved change cannot be applied: {err}")
    rule_id = event["rule_id"]
version = playbook.version(playbook.load(path))

with (state_dir() / "reviews.jsonl").open("a") as fh:
    fh.write(json.dumps({
        "video_run": video_run, "review_run": run_id(), "kind": kind, "verdict": review["verdict"],
        "strengths": review["strengths"], "defects": review["defects"], "action": p["action"], "rule_id": rule_id,
        "playbook_version": version, "approver_comment": comment, "watch_next": review["watch_next"],
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }) + "\n")
emit({"action": p["action"], "rule_id": rule_id, "playbook_version": version})
