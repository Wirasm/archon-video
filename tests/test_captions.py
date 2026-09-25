from vidlib.captions import build_srt
from vidlib.words import Word

WORDS = [Word(t, i * 0.4, i * 0.4 + 0.35) for i, t in enumerate("Most teams ship late, and nobody asks why. Here is the reason.".split())]


def cues(srt):
    return [block.splitlines() for block in srt.strip().split("\n\n")]


def test_srt_shows_script_text_in_phrases():
    assert [c[2] for c in cues(build_srt(WORDS))] == ["Most teams ship late,", "and nobody asks why.", "Here is the reason."]


def test_srt_follows_where_the_narration_starts_in_the_video():
    assert cues(build_srt(WORDS, offset=1.5))[0][1] == "00:00:01,500 --> 00:00:03,050"
