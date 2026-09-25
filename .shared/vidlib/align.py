"""Forced alignment of a known script against its narration.

wav2vec2 CTC (torchaudio's WAV2VEC2_ASR_BASE_960H bundle) aligns the script's
own letters to the audio, so there is no transcript to reconcile. Chosen over
faster-whisper on a 38 s Cartesia narration: mean start error 55 ms vs 113 ms
against Cartesia's native timings, 106/109 words within 150 ms vs 80/109, and
2.5 s vs 6.6 s warm. English only; scripts write numbers as words.
"""

from __future__ import annotations

import re
from pathlib import Path

from .voice import Timed


def letters(token: str) -> str:
    """The characters the English wav2vec2 vocabulary can align."""
    return re.sub(r"[^A-Z']", "", token.upper())


def align(wav: Path, script: str) -> Timed:
    """Timed script tokens. Tokens with nothing alignable (e.g. "2012") are left
    out; map_to_script gives them the span between their neighbours."""
    import soundfile as sf
    import torch
    import torchaudio

    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model()
    data, rate = sf.read(str(wav), dtype="float32", always_2d=True)
    audio = torch.from_numpy(data.T.copy()).mean(0, keepdim=True)
    audio = torchaudio.functional.resample(audio, rate, bundle.sample_rate)

    tokens = [(t, letters(t)) for t in script.split()]
    tokens = [(t, l) for t, l in tokens if l]
    if not tokens:
        raise SystemExit("nothing in the script can be aligned (no letters)")
    vocab = {c: i for i, c in enumerate(bundle.get_labels())}
    targets = torch.tensor([[vocab[c] for _, l in tokens for c in l]])

    with torch.inference_mode():
        emission, _ = model(audio)
    emission = torch.log_softmax(emission, dim=-1)
    path, scores = torchaudio.functional.forced_align(emission, targets, blank=0)
    spans = torchaudio.functional.merge_tokens(path[0], scores[0].exp())
    seconds_per_frame = audio.shape[1] / emission.shape[1] / bundle.sample_rate

    timed: Timed = []
    k = 0
    for token, chars in tokens:
        word_spans = spans[k:k + len(chars)]
        k += len(chars)
        timed.append((token, word_spans[0].start * seconds_per_frame, word_spans[-1].end * seconds_per_frame))
    return timed
