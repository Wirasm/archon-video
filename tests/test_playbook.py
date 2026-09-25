import pytest

from vidlib import playbook as pb

PROV = {"video_run": "v1", "review_run": "r1", "approver_comment": ""}


def test_rules_are_numbered_revised_and_retired_by_id(tmp_path):
    path = tmp_path / "playbook.jsonl"
    pb.append(path, "add", "", "kind", "social", "Open on the object, not a person.", "b01", PROV)
    pb.append(path, "add", "", "common", "social", "No shot over 4 s.", "b05", PROV)
    pb.append(path, "revise", "R1", "kind", "social", "Open on the object in hand.", "b01", PROV)
    events = pb.load(path)
    assert pb.version(events) == 3
    assert {r["rule_id"]: r["text"] for r in pb.active(events).values()} == {
        "R1": "Open on the object in hand.", "R2": "No shot over 4 s."}
    pb.append(path, "retire", "R2", "kind", "social", "", "", PROV)
    assert list(pb.active(pb.load(path))) == ["R1"]


def test_numbering_never_reuses_a_retired_id(tmp_path):
    path = tmp_path / "playbook.jsonl"
    pb.append(path, "add", "", "kind", "social", "a", "", PROV)
    pb.append(path, "retire", "R1", "kind", "social", "", "", PROV)
    assert pb.append(path, "add", "", "kind", "social", "b", "", PROV)["rule_id"] == "R2"


def test_revising_an_unknown_rule_fails_and_writes_nothing(tmp_path):
    path = tmp_path / "playbook.jsonl"
    with pytest.raises(pb.PlaybookError):
        pb.append(path, "revise", "R9", "kind", "social", "x", "", PROV)
    assert pb.load(path) == []
