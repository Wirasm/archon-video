"""Count consistent pairwise wins and keep the top three hooks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.node import artifacts_dir, emit, json_input, log
from vidlib.tournament import rank, table

hooks = json_input("hooks")
judged = json_input("pairs")
verdicts = json_input("verdicts")
failed = sum(1 for v in verdicts if not isinstance(v, dict) or "winner" not in v)
if failed == len(verdicts):
    raise SystemExit("every pairwise judgment failed; nothing to rank")
if failed:
    log(f"{failed} of {len(verdicts)} judgments failed and count for neither hook")
ranked = rank(hooks, judged, verdicts)
(artifacts_dir() / "hooks.md").write_text(table(ranked) + "\n")
emit({"top": ranked[:3], "table": table(ranked)})
