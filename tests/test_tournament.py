from vidlib.tournament import pairs, rank

HOOKS = [{"id": f"h{i}", "spoken": f"line {i}"} for i in range(1, 4)]


def verdict_for(pair, winner_id):
    return {"winner": "A" if pair["a"]["id"] == winner_id else "B", "reason": ""}


def test_every_pair_is_judged_in_both_orders():
    ps = pairs(HOOKS)
    assert len(ps) == 6
    assert {(p["a"]["id"], p["b"]["id"]) for p in ps} == {
        ("h1", "h2"), ("h2", "h1"), ("h1", "h3"), ("h3", "h1"), ("h2", "h3"), ("h3", "h2")}


def test_only_order_consistent_wins_count():
    ps = pairs(HOOKS)
    # h3 beats everyone in both orders; h1 vs h2 is pure position bias (A always wins).
    verdicts = []
    for p in ps:
        ids = {p["a"]["id"], p["b"]["id"]}
        verdicts.append(verdict_for(p, "h3") if "h3" in ids else {"winner": "A", "reason": ""})
    ranked = rank(HOOKS, ps, verdicts)
    assert ranked[0]["id"] == "h3" and ranked[0]["wins"] == 2
    assert ranked[1]["wins"] == 0 and ranked[2]["wins"] == 0


def test_failed_judgments_count_for_nobody():
    ps = pairs(HOOKS)
    verdicts = [{"archon_failed": True, "error": "x", "status": "failed"}] * len(ps)
    assert all(h["raw_wins"] == 0 for h in rank(HOOKS, ps, verdicts))
