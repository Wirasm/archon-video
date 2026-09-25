"""The playbook: numbered house rules learned from human-approved reviews.

playbook.jsonl in the project's state folder is an append-only event log. Each
event adds a rule (R1, R2, ...), revises one or retires one, and carries its
provenance. The active rules are the fold of the log; the version is the
number of events, so every change bumps it and a stored video can name the
exact playbook it was made with.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ACTIONS = {"add", "revise", "retire"}
SCOPES = {"kind", "common"}


class PlaybookError(ValueError):
    pass


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def version(events: list[dict]) -> int:
    return len(events)


def active(events: list[dict]) -> dict[str, dict]:
    """rule_id -> {rule_id, scope, kind, text} for rules not retired."""
    rules: dict[str, dict] = {}
    for e in events:
        rid = e["rule_id"]
        if e["action"] == "add":
            rules[rid] = {k: e[k] for k in ("rule_id", "scope", "kind", "text")}
        elif e["action"] == "revise":
            rules[rid] = rules[rid] | {"text": e["text"]}
        elif e["action"] == "retire":
            rules.pop(rid, None)
    return rules


def for_kind(events: list[dict], kind: str) -> list[dict]:
    return [r for r in active(events).values() if r["scope"] == "common" or r["kind"] == kind]


def render(events: list[dict], kind: str) -> str:
    rules = for_kind(events, kind)
    if not rules:
        return ""
    lines = [f"House rules (playbook v{version(events)}), learned from reviewed videos. Follow them:"]
    lines += [f"- {r['rule_id']} ({'all kinds' if r['scope'] == 'common' else kind}): {r['text']}" for r in rules]
    return "\n".join(lines)


def append(path: Path, action: str, rule_id: str, scope: str, kind: str, text: str, evidence: str, provenance: dict) -> dict:
    """Validate one change against the current log and append it. Returns the event."""
    events = load(path)
    current = active(events)
    if action not in ACTIONS:
        raise PlaybookError(f"unknown action {action!r}")
    if scope not in SCOPES:
        raise PlaybookError(f"unknown scope {scope!r}")
    if action == "add":
        if not text.strip():
            raise PlaybookError("a new rule needs text")
        rule_id = f"R{sum(1 for e in events if e['action'] == 'add') + 1}"
    elif rule_id not in current:
        raise PlaybookError(f"{action} names {rule_id!r}, which is not an active rule ({', '.join(current) or 'none'})")
    elif action == "revise" and not text.strip():
        raise PlaybookError("a revision needs text")
    else:
        scope, kind = current[rule_id]["scope"], current[rule_id]["kind"]

    event = {
        "action": action, "rule_id": rule_id, "scope": scope, "kind": kind, "text": text.strip(),
        "evidence": evidence, "provenance": provenance,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(event) + "\n")
    return event
