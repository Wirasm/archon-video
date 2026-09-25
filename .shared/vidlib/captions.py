"""Burned-in captions (ASS) and an SRT sidecar, both from words.json.

Placement comes from the output format's safe zone, style from the brand's
caption tokens. Caption events never overlap: an overlapping ASS event renders
stacked on top of the previous one.
"""

from __future__ import annotations

import re

from .words import Word

SENTENCE_END = re.compile(r"[.!?]$")
PHRASE_END = re.compile(r"[.!?,;:]$")


def ass_colour(hex_colour: str) -> str:
    """#RRGGBB -> ASS &H00BBGGRR."""
    h = hex_colour.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"colour must be #RRGGBB, got {hex_colour!r}")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ass_time(seconds: float) -> str:
    cs = int(round(max(0.0, seconds) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def srt_time(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "").replace("}", "")


def chunk(words: list[Word], max_words: int, max_chars: int) -> list[list[Word]]:
    """Short phrases that break on punctuation and never exceed the line width."""
    chunks: list[list[Word]] = []
    current: list[Word] = []
    length = 0
    for w in words:
        if current and (len(current) >= max_words or length + len(w.text) + 1 > max_chars):
            chunks.append(current)
            current, length = [], 0
        current.append(w)
        length += len(w.text) + 1
        if PHRASE_END.search(w.text):
            chunks.append(current)
            current, length = [], 0
    if current:
        chunks.append(current)
    return chunks


def build_ass(
    words: list[Word],
    fmt: dict,
    style: dict,
    overlays: list[tuple[float, float, str]],
) -> str:
    """ASS with a karaoke caption track and an upper-third overlay track.

    `style` is the resolved `captions` block of config.json. `overlays` are
    (start, end, text) spans shown in the upper third.
    """
    width, height, safe = fmt["width"], fmt["height"], fmt["safe"]
    font_size = round(width * 0.076)
    overlay_size = round(font_size * 0.9)
    # Caption baseline sits in the lower part of the safe box, clear of platform UI.
    margin_v = safe["bottom"] + round(height * 0.18)
    max_chars = int((width - safe["left"] - safe["right"]) / (font_size * 0.62))
    text_c, accent_c, outline_c = (ass_colour(style[k]) for k in ("text", "accent", "outline"))
    family = style["font_family"]
    upper = style["uppercase"]

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{family},{font_size},{text_c},{accent_c},{outline_c},&H96000000,-1,0,0,0,100,100,0,0,1,7,3,2,{safe['left']},{safe['right']},{margin_v},1
Style: Overlay,{family},{overlay_size},{text_c},{accent_c},{outline_c},&H96000000,-1,0,0,0,100,100,0,0,1,6,3,8,{safe['left']},{safe['right']},{safe['top'] + 40},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def show(text: str) -> str:
        return _escape(text.upper() if upper else text)

    lines: list[str] = []
    chunks = chunk(words, 3, max_chars)
    for c, group in enumerate(chunks):
        next_start = chunks[c + 1][0].start if c + 1 < len(chunks) else None
        for i, active in enumerate(group):
            rendered = " ".join(
                f"{{\\c{accent_c}}}{show(w.text)}{{\\c{text_c}}}" if j == i else show(w.text)
                for j, w in enumerate(group)
            )
            start = active.start
            if i + 1 < len(group):
                end = group[i + 1].start
            else:
                # Hold the last word a moment, but never past the next chunk.
                end = active.end + 0.12
                if next_start is not None:
                    end = min(end, next_start)
            if end <= start:
                end = start + 0.08
            lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,{rendered}")

    for start, end, text in overlays:
        if text.strip():
            lines.append(f"Dialogue: 1,{ass_time(start)},{ass_time(end)},Overlay,,0,0,0,,{show(text.strip())}")

    return header + "\n".join(lines) + "\n"


def build_srt(words: list[Word]) -> str:
    """Phrase-level subtitles for accessibility: up to about seven words a cue."""
    cues: list[list[Word]] = []
    current: list[Word] = []
    for w in words:
        current.append(w)
        if SENTENCE_END.search(w.text) or len(current) >= 7 or (len(current) >= 4 and PHRASE_END.search(w.text)):
            cues.append(current)
            current = []
    if current:
        cues.append(current)
    out = []
    for n, cue in enumerate(cues, 1):
        end = cue[-1].end
        if n < len(cues):
            end = min(end, cues[n][0].start)
        out.append(f"{n}\n{srt_time(cue[0].start)} --> {srt_time(end)}\n{' '.join(w.text for w in cue)}\n")
    return "\n".join(out)
