"""Narrate the picked script and write words.json.

Reads  : config.json, the bound `narration`
Writes : narration.wav, words.json
Prints : paths, duration, and the indexed word list the beat planner anchors on
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import words as wordsmod
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, log, text_input
from vidlib.voice import cartesia


def main() -> None:
    out = artifacts_dir()
    cfg = load_resolved(out)
    narration = " ".join(text_input("narration").split())
    if not narration:
        raise SystemExit("the picked script has no narration")

    voice = cfg["voice"]
    wav = out / "narration.wav"
    if voice["provider"] != "cartesia":
        raise SystemExit(f"voice provider {voice['provider']!r} is not supported yet")
    log(f"synthesising {len(narration.split())} words with cartesia {voice['model']}")
    duration, timed = cartesia.synthesize(narration, voice["voice_id"], voice["model"], wav)

    words = wordsmod.map_to_script(narration, timed)
    wordsmod.write(out / "words.json", words, duration, "native", voice["provider"], voice["model"])
    (out / "script.txt").write_text(narration + "\n")

    indexed = " ".join(f"[{i}]{w.text}@{w.start:.2f}" for i, w in enumerate(words))
    emit(
        {
            "audio": str(wav),
            "words_file": str(out / "words.json"),
            "duration": round(duration, 3),
            "provider": voice["provider"],
            "timings": "native",
            "word_count": len(words),
            "indexed": indexed,
        }
    )


if __name__ == "__main__":
    main()
