"""Shared code for the archon-video pack.

Scripts import it with:

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))
    from vidlib import ...
"""

from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parents[1]
