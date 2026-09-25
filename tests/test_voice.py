"""Every provider ends in wav audio plus either timed words or None."""

import base64
import io
import subprocess
import wave
from pathlib import Path

import pytest

from vidlib.voice import deepgram, elevenlabs
from vidlib.voice.elevenlabs import group_words
from vidlib.words import map_to_script

VOICE = {"voice_id": "v", "model": None, "timings": "auto"}


def tone_wav(seconds: float = 0.5) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(24000)
        w.writeframes(b"\x00\x00" * int(24000 * seconds))
    return buf.getvalue()


class FakeResponse:
    def __init__(self, *, json_body=None, content=b""):
        self.ok, self.status_code = True, 200
        self._json, self.content = json_body, content

    def json(self):
        return self._json


def test_character_alignment_groups_into_words():
    chars = list("Hi there, you.")
    starts = [i * 0.1 for i in range(len(chars))]
    ends = [s + 0.1 for s in starts]
    assert group_words(chars, starts, ends) == [("Hi", 0.0, 0.2), ("there,", pytest.approx(0.3), pytest.approx(0.9)), ("you.", pytest.approx(1.0), pytest.approx(1.4))]


def test_elevenlabs_returns_audio_and_script_words(tmp_path, monkeypatch):
    mp3 = tmp_path / "a.mp3"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "1", str(mp3)], check=True)
    text = "Ninety percent."
    body = {
        "audio_base64": base64.b64encode(mp3.read_bytes()).decode(),
        "alignment": {
            "characters": list(text),
            "character_start_times_seconds": [i * 0.05 for i in range(len(text))],
            "character_end_times_seconds": [i * 0.05 + 0.05 for i in range(len(text))],
        },
    }
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    monkeypatch.setattr(elevenlabs.requests, "post", lambda *a, **k: FakeResponse(json_body=body))
    speech = elevenlabs.synthesize(text, VOICE, tmp_path / "n.wav")
    assert (tmp_path / "n.wav").exists() and speech.duration == pytest.approx(1.0, abs=0.05)
    assert [w.text for w in map_to_script(text, speech.timed)] == ["Ninety", "percent."]


def test_deepgram_returns_audio_only(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "k")
    monkeypatch.setattr(deepgram.requests, "post", lambda *a, **k: FakeResponse(content=tone_wav()))
    speech = deepgram.synthesize("Hello.", {"voice_id": None, "model": "aura-2-thalia-en"}, tmp_path / "n.wav")
    assert speech.timed is None and speech.duration == pytest.approx(0.5, abs=0.02)


def test_deepgram_refuses_text_over_its_limit(tmp_path):
    with pytest.raises(SystemExit):
        deepgram.synthesize("a" * 2001, VOICE, tmp_path / "n.wav")
