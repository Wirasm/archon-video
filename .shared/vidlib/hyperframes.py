"""The pinned HyperFrames CLI. Prompts and the render script read the pin from here."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

PACKAGE = "hyperframes@0.8.75"


def run(args: list[str], cwd: Path, timeout: int | None = None) -> subprocess.CompletedProcess:
    # The CLI's anonymous telemetry is on by default.
    env = os.environ | {"HYPERFRAMES_NO_TELEMETRY": "1"}
    return subprocess.run(["npx", "-y", PACKAGE, *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
