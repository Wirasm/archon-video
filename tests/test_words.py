import pytest

from vidlib.words import map_to_script


def test_exact_tokens_keep_provider_times():
    words = map_to_script("Most teams ship late.", [("Most", 0.0, 0.2), ("teams", 0.2, 0.5), ("ship", 0.5, 0.7), ("late.", 0.7, 1.0)])
    assert [w.text for w in words] == ["Most", "teams", "ship", "late."]
    assert words[3].start == 0.7


def test_punctuation_and_case_differences_still_match():
    words = map_to_script("Most teams, honestly.", [("most", 0.0, 0.2), ("teams", 0.2, 0.5), ("honestly", 0.6, 1.0)])
    assert [(w.text, w.start) for w in words] == [("Most", 0.0), ("teams,", 0.2), ("honestly.", 0.6)]


def test_unmatched_script_tokens_share_the_gap_between_neighbours():
    # The provider spoke "90%" as two tokens the script does not contain.
    words = map_to_script("about 90% of us", [("about", 0.0, 0.3), ("ninety", 0.3, 0.6), ("percent", 0.6, 0.9), ("of", 0.9, 1.0), ("us", 1.0, 1.2)])
    assert [w.text for w in words] == ["about", "90%", "of", "us"]
    assert words[1].start == pytest.approx(0.3) and words[1].end == pytest.approx(0.9)


def test_starts_never_go_backwards():
    words = map_to_script("a b c", [("a", 0.0, 0.1), ("c", 0.5, 0.6)])
    starts = [w.start for w in words]
    assert starts == sorted(starts)
