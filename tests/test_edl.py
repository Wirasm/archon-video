import pytest

from vidlib.edl import TAIL_S, PlanError, build
from vidlib.words import Word

WORDS = [Word(t, i * 0.5 + 0.1, i * 0.5 + 0.4) for i, t in enumerate("one two three four five six".split())]


def beat(start, emphasis=None):
    return {"start_word": start, "source": "stock", "visual": f"v{start}", "queries": [], "emphasis_word": emphasis, "overlay": ""}


def test_beats_tile_the_video_without_gaps():
    beats = build([beat(3), beat(0), beat(1)], WORDS, 3.0, 30)
    assert [b["start"] for b in beats] == [0.0, 0.6, 1.6]
    assert all(a["end"] == b["start"] for a, b in zip(beats, beats[1:]))
    assert beats[-1]["end"] == pytest.approx(3.0 + TAIL_S)
    assert beats[1]["span"] == "two three"


def test_first_beat_is_forced_to_word_zero():
    assert build([beat(2), beat(4)], WORDS, 3.0, 30)[0]["start"] == 0.0


def test_out_of_range_start_word_fails():
    with pytest.raises(PlanError):
        build([beat(0), beat(9)], WORDS, 3.0, 30)


def test_emphasis_outside_its_beat_is_dropped():
    beats = build([beat(0, emphasis=4), beat(3, emphasis=4)], WORDS, 3.0, 30)
    assert beats[0]["emphasis_t"] is None
    assert beats[1]["emphasis_t"] == pytest.approx(0.5)
