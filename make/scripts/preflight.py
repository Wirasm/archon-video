"""Resolve the config and fail before any spend if the run cannot finish.

Checks only what the configured providers need: keys, binaries, referenced
files. Writes $ARTIFACTS_DIR/config.json (every later node reads that copy) and
prints the context block the agent nodes receive.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

import yaml

from vidlib import hyperframes, playbook
from vidlib.config import ConfigError, digest, resolve
from vidlib.context import context_block, recent_openings
from vidlib.node import artifacts_dir, emit, state_dir, text_input


def check_binaries() -> list[str]:
    problems = []
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            problems.append(f"{binary} is not on PATH (brew install ffmpeg, or apt-get install ffmpeg)")
    # The composition renders with HyperFrames, which needs Node 22 or newer.
    node = shutil.which("node")
    if not node or not shutil.which("npx"):
        problems.append("node and npx are not on PATH; HyperFrames needs Node 22 or newer")
    else:
        version = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip().lstrip("v")
        if int(version.split(".")[0] or 0) < 22:
            problems.append(f"node {version} is too old; HyperFrames needs Node 22 or newer")
    return problems


def check_skills() -> list[str]:
    """The editor node's `skills:` list in make.yaml is the one list; check it is installed."""
    workflow = yaml.safe_load((Path(__file__).resolve().parents[1] / "make.yaml").read_text())
    editor = next(node for node in workflow["nodes"] if node["id"] == "editor")
    missing = hyperframes.missing_skills(editor["skills"], hyperframes.skill_roots(Path.cwd(), Path.home()))
    if not missing:
        return []
    return [
        f"the editor's HyperFrames skills are not installed ({', '.join(missing)}); "
        "install them with: npx hyperframes skills update " + " ".join(missing)
    ]


def recent_hooks(limit: int = 10) -> list[str]:
    library = state_dir() / "library.jsonl"
    if not library.exists():
        return []
    rows = [json.loads(line) for line in library.read_text().splitlines() if line.strip()]
    return [r["hook"] for r in rows if r.get("hook")][-limit:]


def main() -> None:
    brief = text_input("brief").strip()
    if not brief:
        raise SystemExit("the brief is empty")
    config_path = Path(text_input("config", "video.config.yaml")).expanduser()
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path

    problems = check_binaries() + check_skills()
    if not config_path.exists():
        problems.append(
            f"no config at {config_path}; copy video.config.example.yaml from the pack to your project as video.config.yaml"
        )
        raise SystemExit("preflight failed:\n- " + "\n- ".join(problems))

    raw_text = config_path.read_text()
    try:
        cfg = resolve(yaml.safe_load(raw_text) or {}, config_path.parent, dict(os.environ))
    except ConfigError as err:
        problems += err.problems
    if problems:
        raise SystemExit("preflight failed:\n- " + "\n- ".join(problems))

    cfg["config_file"] = str(config_path)
    cfg["config_digest"] = digest(raw_text)
    cfg["brief"] = brief
    facts = Path(cfg["facts_file"]).read_text() if cfg["facts_file"] else None
    hooks = recent_hooks()
    events = playbook.load(state_dir() / "playbook.jsonl")
    cfg["playbook_version"] = playbook.version(events)

    out = artifacts_dir()
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(cfg, indent=2))

    emit(
        {
            "format": cfg["format"]["name"],
            "config_digest": cfg["config_digest"],
            "length_min": cfg["length_s"]["min"],
            "length_max": cfg["length_s"]["max"],
            "playbook_version": cfg["playbook_version"],
            "context": context_block(cfg, brief, facts, playbook.render(events)),
            "recent_openings": recent_openings(hooks),
            "hyperframes": hyperframes.PACKAGE,
            "music": "\n".join(f"- {Path(t).relative_to(cfg['music']['dir'])}" for t in cfg["music"]["tracks"]) or "(no music library)",
        }
    )


if __name__ == "__main__":
    main()
