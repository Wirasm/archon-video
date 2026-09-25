"""Pairwise hook tournament: every pair judged in both orders.

A hook scores a win only when it wins in both orders, which cancels the judge's
position bias. Raw wins break ties.
"""

from __future__ import annotations

from itertools import combinations


def pairs(hooks: list[dict]) -> list[dict]:
    out = []
    for x, y in combinations(hooks, 2):
        for a, b in ((x, y), (y, x)):
            out.append({"pair_id": f"{a['id']}-vs-{b['id']}", "a": a, "b": b})
    return out


def rank(hooks: list[dict], judged_pairs: list[dict], verdicts: list[dict]) -> list[dict]:
    """Return hooks sorted best first, each with consistent and raw win counts.

    `verdicts` is the fan-out aggregate in the same order as `judged_pairs`. A
    failed judgment (an engine failure marker) counts for neither side.
    """
    if len(verdicts) != len(judged_pairs):
        raise ValueError(f"{len(verdicts)} verdicts for {len(judged_pairs)} pairs")
    raw = {h["id"]: 0 for h in hooks}
    won: dict[tuple[str, str], str] = {}
    for pair, verdict in zip(judged_pairs, verdicts):
        if not isinstance(verdict, dict) or verdict.get("winner") not in ("A", "B"):
            continue
        winner = pair["a"]["id"] if verdict["winner"] == "A" else pair["b"]["id"]
        raw[winner] += 1
        won[(pair["a"]["id"], pair["b"]["id"])] = winner
    consistent = {h["id"]: 0 for h in hooks}
    for x, y in combinations([h["id"] for h in hooks], 2):
        first, second = won.get((x, y)), won.get((y, x))
        if first and first == second:
            consistent[first] += 1
    ranked = sorted(hooks, key=lambda h: (-consistent[h["id"]], -raw[h["id"]]))
    return [h | {"wins": consistent[h["id"]], "raw_wins": raw[h["id"]]} for h in ranked]


def table(ranked: list[dict]) -> str:
    lines = ["| hook | consistent wins | raw wins | spoken |", "|---|---|---|---|"]
    lines += [f"| {h['id']} | {h['wins']} | {h['raw_wins']} | {h['spoken']} |" for h in ranked]
    return "\n".join(lines)
