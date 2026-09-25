"""words.json: the one timing artifact everything downstream reads.

Every voice provider ends here. `text` is always the script's own token as
written, never the provider's normalised spelling, so captions show the script.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


def tokens(script: str) -> list[str]:
    return script.split()


def _norm(token: str) -> str:
    return re.sub(r"[^\w]", "", token.lower())


def map_to_script(script: str, timed: list[tuple[str, float, float]]) -> list[Word]:
    """Give every script token a start and end from a provider's timed tokens.

    Providers normalise text ("90%" -> "ninety percent", punctuation), so tokens
    are aligned with a sequence match on normalised text. Matched tokens take the
    provider's times; a run of unmatched script tokens shares the span between
    its matched neighbours evenly.
    """
    script_tokens = tokens(script)
    if not script_tokens:
        raise ValueError("empty script")
    if not timed:
        raise ValueError("no timed tokens to map")

    a = [_norm(t) for t in script_tokens]
    b = [_norm(t) for t, _, _ in timed]
    times: list[tuple[float, float] | None] = [None] * len(script_tokens)
    for block in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(block.size):
            _, start, end = timed[block.b + k]
            times[block.a + k] = (start, end)

    end_of_audio = max(end for _, _, end in timed)
    i = 0
    while i < len(times):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(times) and times[j] is None:
            j += 1
        gap_start = times[i - 1][1] if i > 0 else 0.0
        gap_end = times[j][0] if j < len(times) else end_of_audio
        gap_end = max(gap_end, gap_start)
        step = (gap_end - gap_start) / (j - i)
        for k in range(i, j):
            times[k] = (gap_start + step * (k - i), gap_start + step * (k - i + 1))
        i = j

    words = [Word(t, s, e) for t, (s, e) in zip(script_tokens, times)]  # type: ignore[misc]
    # Starts must never go backwards, or cuts and captions would reorder.
    for k in range(1, len(words)):
        if words[k].start < words[k - 1].start:
            words[k] = Word(words[k].text, words[k - 1].start, max(words[k].end, words[k - 1].start))
    return words


def write(path: Path, words: list[Word], duration: float, source: str, provider: str, model: str | None) -> None:
    path.write_text(
        json.dumps(
            {
                "words": [asdict(w) for w in words],
                "duration": duration,
                "source": source,
                "provider": provider,
                "model": model,
            },
            indent=1,
        )
    )


def read(path: Path) -> dict:
    data = json.loads(path.read_text())
    data["words"] = [Word(**w) for w in data["words"]]
    return data
