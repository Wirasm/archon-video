"""The prose block every agent node receives: brief, brand, format, facts, lessons."""

from __future__ import annotations

import json


def context_block(cfg: dict, brief: str, facts: str | None, lessons: str) -> str:
    brand = cfg["brand"]
    fmt = cfg["format"]
    safe = fmt["safe"]
    parts = [
        "## The brief\n" + brief.strip(),
        f"## Brand: {brand['name']}\n"
        "Design tokens and brand guidance. Interpret them; they are not a template. "
        "`constraints` are hard rules.\n```json\n" + json.dumps(brand, indent=2) + "\n```",
        f"## Format\n{fmt['name']}: {fmt['width']}x{fmt['height']} ({fmt['aspect']}) at {fmt['fps']} fps, "
        f"at most {fmt['max_duration_s']} s. Platform UI covers the edges: keep text and anything the viewer must "
        f"read inside {safe['left']} px from the left, {safe['right']} px from the right, {safe['top']} px from the top "
        f"and {safe['bottom']} px from the bottom. Narration length: {cfg['length_s']['min']}-{cfg['length_s']['max']} seconds.",
    ]
    if facts:
        parts.append("## Facts\nClaim nothing about the brand beyond these:\n" + facts.strip())
    if lessons:
        parts.append(lessons)
    return "\n\n".join(parts)


def recent_openings(hooks: list[str]) -> str:
    """Only the hook writer reads this. In the shared block, other agents took
    the list for examples of the current video and doubted their own input."""
    if not hooks:
        return "(none yet)"
    return "Recent openings (do not repeat their angle or structure):\n" + "\n".join(f"- {h}" for h in hooks)
