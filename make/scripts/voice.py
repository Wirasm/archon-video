"""Narrate the picked script with the configured voice provider.

Reads  : config.json, the bound `narration`
Writes : narration.wav, script.txt, and words.json when the provider has timings
Prints : whether the align node must time the words
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".shared"))

from vidlib import words as wordsmod
from vidlib.config import load_resolved
from vidlib.node import artifacts_dir, emit, log, text_input
from vidlib.voice import provider

out = artifacts_dir()
cfg = load_resolved(out)
voice = cfg["voice"]
narration = " ".join(text_input("narration").split())
if not narration:
    raise SystemExit("the picked script has no narration")
(out / "script.txt").write_text(narration + "\n")

p = provider(voice["provider"])
log(f"synthesising {len(narration.split())} words with {p.name} {voice['model'] or ''}")
speech = p.synthesize(narration, voice, out / "narration.wav")

native = speech.timed is not None and voice["timings"] != "align"
if native:
    words = wordsmod.map_to_script(narration, speech.timed)
    wordsmod.write(out / "words.json", words, speech.duration, "native", p.name, voice["model"])
emit({"provider": p.name, "duration": round(speech.duration, 3), "needs_alignment": not native})
