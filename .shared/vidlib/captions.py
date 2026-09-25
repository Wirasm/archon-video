"""The SRT sidecar: phrase-level subtitles from words.json, for accessibility.

On-screen text is the editor's decision and lives in the composition. The SRT
is a separate file platforms can show or index; it follows the narration.
"""

from __future__ import annotations

import re

from .words import Word

SENTENCE_END = re.compile(r"[.!?]$")
PHRASE_END = re.compile(r"[.!?,;:]$")


def srt_time(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(words: list[Word], offset: float = 0.0) -> str:
    """Cues of up to about seven words; `offset` is where the narration starts in the video."""
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
        out.append(f"{n}\n{srt_time(cue[0].start + offset)} --> {srt_time(end + offset)}\n{' '.join(w.text for w in cue)}\n")
    return "\n".join(out)
