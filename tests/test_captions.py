from vidlib.captions import ass_colour, build_ass, build_srt, chunk
from vidlib.formats import FORMATS
from vidlib.words import Word

STYLE = {"font_family": "Arial Black", "uppercase": True, "text": "#FFFFFF", "accent": "#FFD60A", "outline": "#000000"}
WORDS = [Word(t, i * 0.4, i * 0.4 + 0.35) for i, t in enumerate("Most teams ship late, and nobody asks why. Here is the reason.".split())]


def test_colour_is_ass_bgr():
    assert ass_colour("#FFD60A") == "&H000AD6FF"


def test_chunks_break_on_punctuation_and_width():
    groups = [" ".join(w.text for w in g) for g in chunk(WORDS, 3, 18)]
    assert groups == ["Most teams ship", "late,", "and nobody asks", "why.", "Here is the", "reason."]


def test_caption_events_never_overlap():
    ass = build_ass(WORDS, FORMATS["shorts"].to_dict(), STYLE, [])
    events = [line.split(",")[1:3] for line in ass.splitlines() if line.startswith("Dialogue: 0,")]

    def secs(t):
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    spans = [(secs(a), secs(b)) for a, b in events]
    assert all(end <= nxt_start + 1e-6 for (_, end), (nxt_start, _) in zip(spans, spans[1:]))


def test_captions_sit_inside_the_format_safe_zone():
    fmt = FORMATS["shorts"].to_dict()
    ass = build_ass(WORDS, fmt, STYLE, [])
    cap_style = next(line for line in ass.splitlines() if line.startswith("Style: Cap,"))
    margin_l, margin_r, margin_v = (int(x) for x in cap_style.split(",")[-4:-1])
    assert margin_l >= fmt["safe"]["left"] and margin_r >= fmt["safe"]["right"]
    assert margin_v >= fmt["safe"]["bottom"]


def test_srt_shows_script_text():
    cues = [block.splitlines()[2] for block in build_srt(WORDS).strip().split("\n\n")]
    assert cues == ["Most teams ship late,", "and nobody asks why.", "Here is the reason."]
