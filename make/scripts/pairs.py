"""Every pair of hooks, in both orders, for the judge fan-out."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib.node import emit, json_input
from vidlib.tournament import pairs

emit({"pairs": pairs(json_input("hooks"))})
