"""The small surface every script node uses: dirs, bound inputs, output, logs."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def artifacts_dir() -> Path:
    return Path(os.environ["ARTIFACTS_DIR"])


def state_dir() -> Path:
    """Per-project state shared across runs; the pack keeps its files under video/."""
    d = Path(os.environ["STATE_DIR"]) / "video"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_id() -> str:
    return os.environ["WORKFLOW_ID"]


def text_input(name: str, default: str | None = None) -> str:
    """A value bound with `with:` or a workflow input, delivered as INPUTS_<NAME>."""
    value = os.environ.get("INPUTS_" + name.upper().replace("-", "_"))
    if value is None:
        if default is not None:
            return default
        raise SystemExit(f"missing input {name!r} (INPUTS_{name.upper()})")
    return value


def json_input(name: str) -> Any:
    """Objects and arrays arrive as canonical JSON text; parse them once."""
    return json.loads(text_input(name))


def emit(value: Any) -> None:
    """The node's stdout is its output; keep it one JSON document."""
    sys.stdout.write(json.dumps(value))
    sys.stdout.flush()


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)
