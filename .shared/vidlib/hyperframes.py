"""The pinned HyperFrames CLI and the skills the editor loads.

Prompts and the render script read the pin from here. Keep it on the release
the installed skills track (`npx hyperframes skills check`), so the editor's
skills and the CLI it runs describe the same framework.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

PACKAGE = "hyperframes@0.8.78"


def run(args: list[str], cwd: Path, timeout: int | None = None) -> subprocess.CompletedProcess:
    # The CLI's anonymous telemetry is on by default.
    env = os.environ | {"HYPERFRAMES_NO_TELEMETRY": "1"}
    return subprocess.run(["npx", "-y", PACKAGE, *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def skill_roots(project: Path, home: Path) -> list[Path]:
    """Where Claude (.claude/skills) and Codex (.agents/skills, ~/.codex/skills) find skills."""
    return [
        project / ".claude/skills",
        home / ".claude/skills",
        project / ".agents/skills",
        home / ".agents/skills",
        home / ".codex/skills",
    ]


def missing_skills(names: list[str], roots: list[Path]) -> list[str]:
    """The named skills with no SKILL.md under any root.

    A workflow pack cannot ship skills, and Archon only warns when a declared
    one is absent, so without this check the editor would run without them.
    """
    return [name for name in names if not any((root / name / "SKILL.md").is_file() for root in roots)]
