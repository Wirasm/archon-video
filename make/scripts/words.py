"""Read words.json, whichever node wrote it, and list the words for the director and editor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import words as wordsmod
from vidlib.node import artifacts_dir, emit

data = wordsmod.read(artifacts_dir() / "words.json")
words = data["words"]
emit(
    {
        "duration": round(data["duration"], 3),
        "provider": data["provider"],
        "timings": data["source"],
        "word_count": len(words),
        "indexed": " ".join(f"[{i}]{w.text}@{w.start:.2f}" for i, w in enumerate(words)),
    }
)
