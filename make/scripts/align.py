"""Time the script's words against narration.wav by forced alignment."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import words as wordsmod
from vidlib.align import align
from vidlib.config import load_resolved
from vidlib.media import duration
from vidlib.node import artifacts_dir, emit

out = artifacts_dir()
cfg = load_resolved(out)
script = (out / "script.txt").read_text().strip()
wav = out / "narration.wav"
words = wordsmod.map_to_script(script, align(wav, script))
wordsmod.write(out / "words.json", words, duration(wav), "aligned", cfg["voice"]["provider"], cfg["voice"]["model"])
emit({"words": len(words)})
