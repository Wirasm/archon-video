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

from vidlib import SHARED_DIR
from vidlib import playbook
from vidlib.config import ConfigError, digest, resolve
from vidlib.node import artifacts_dir, emit, state_dir, text_input


def check_binaries() -> list[str]:
    problems = []
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            problems.append(f"{binary} is not on PATH (brew install ffmpeg, or apt-get install ffmpeg)")
    if not problems:
        filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        if " ass " not in filters:
            problems.append("ffmpeg has no libass (the `ass` filter); captions need an ffmpeg built with libass")
    return problems


def recent_hooks(kind: str, limit: int = 10) -> list[str]:
    library = state_dir() / "library.jsonl"
    if not library.exists():
        return []
    rows = [json.loads(line) for line in library.read_text().splitlines() if line.strip()]
    return [r["hook"] for r in rows if r.get("kind") == kind and r.get("hook")][-limit:]


def context_block(cfg: dict, kind_brief: str, facts: str | None, hooks: list[str], rules: str) -> str:
    brand = cfg["brand"]
    fmt = cfg["format"]
    parts = [
        f"## Brand: {brand['name']}",
        "Brand tokens (the main creative lever; follow them):",
        "```json\n" + json.dumps(brand.get("tokens", {}), indent=2) + "\n```",
    ]
    if brand.get("voice_and_tone"):
        parts.append("Voice and tone:\n" + str(brand["voice_and_tone"]).strip())
    if brand.get("audience"):
        parts.append(f"Audience: {brand['audience']}")
    parts.append(kind_brief.strip())
    if cfg["kind_options"]:
        parts.append("Options for this kind: " + json.dumps(cfg["kind_options"]))
    parts.append(
        f"Format: {fmt['name']}, {fmt['aspect']} vertical video at {fmt['width']}x{fmt['height']}. "
        f"Target length: {cfg['length_s']['min']}-{cfg['length_s']['max']} seconds of narration."
    )
    if facts:
        parts.append("Facts you may state (claim nothing about the brand beyond these):\n" + facts.strip())
    if rules:
        parts.append(rules)
    if hooks:
        parts.append(
            "Recent openings for this kind (do not repeat their angle or structure):\n"
            + "\n".join(f"- {h}" for h in hooks)
        )
    return "\n\n".join(parts)


def main() -> None:
    kind = text_input("kind", "social")
    config_path = Path(text_input("config", "video.config.yaml")).expanduser()
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path

    problems = check_binaries()
    if not config_path.exists():
        problems.append(
            f"no config at {config_path}; copy video.config.example.yaml from the pack to your project as video.config.yaml"
        )
        raise SystemExit("preflight failed:\n- " + "\n- ".join(problems))

    raw_text = config_path.read_text()
    try:
        cfg = resolve(yaml.safe_load(raw_text) or {}, kind, config_path.parent, dict(os.environ))
    except ConfigError as err:
        problems += err.problems
    if problems:
        raise SystemExit("preflight failed:\n- " + "\n- ".join(problems))

    cfg["config_file"] = str(config_path)
    cfg["config_digest"] = digest(raw_text)
    kind_brief = (SHARED_DIR / "kinds" / f"{kind}.md").read_text()
    facts = Path(cfg["facts_file"]).read_text() if cfg["facts_file"] else None
    hooks = recent_hooks(kind)
    events = playbook.load(state_dir() / "playbook.jsonl")
    cfg["playbook_version"] = playbook.version(events)

    out = artifacts_dir()
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(cfg, indent=2))

    emit(
        {
            "kind": kind,
            "format": cfg["format"]["name"],
            "config_digest": cfg["config_digest"],
            "length_min": cfg["length_s"]["min"],
            "length_max": cfg["length_s"]["max"],
            "moods": cfg["music"]["moods"],
            "playbook_version": cfg["playbook_version"],
            "context": context_block(cfg, kind_brief, facts, hooks, playbook.render(events, kind)),
        }
    )


if __name__ == "__main__":
    main()
