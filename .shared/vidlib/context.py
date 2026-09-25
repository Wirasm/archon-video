"""The prose block every agent node receives: brand, kind, format, facts, rules."""

from __future__ import annotations

import json


def context_block(cfg: dict, kind_brief: str, facts: str | None, rules: str) -> str:
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
    return "\n\n".join(parts)


def recent_openings(hooks: list[str]) -> str:
    """Only the hook writer reads this. In the shared block, other agents took
    the list for examples of the current video and doubted their own input."""
    if not hooks:
        return "(none yet)"
    return "Recent openings for this kind (do not repeat their angle or structure):\n" + "\n".join(f"- {h}" for h in hooks)
