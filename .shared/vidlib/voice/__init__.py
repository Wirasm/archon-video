"""Voice providers. Each writes a mono wav and returns timed tokens when it has them.

Synthesis and timings are separate: a provider without timings returns None,
and the `align` node times the script against the audio instead. Every path
ends in the same words.json (see vidlib.words).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

Timed = list[tuple[str, float, float]]


@dataclass(frozen=True)
class Speech:
    duration: float
    timed: Timed | None  # None: the provider returns audio only


@dataclass(frozen=True)
class Provider:
    name: str
    key_env: str | None  # None: runs locally, no key
    native_timings: bool
    synthesize: Callable[[str, dict, Path], Speech]


def _load() -> dict[str, Provider]:
    from . import cartesia, deepgram, elevenlabs, kokoro

    return {
        "cartesia": Provider("cartesia", "CARTESIA_API_KEY", True, cartesia.synthesize),
        "elevenlabs": Provider("elevenlabs", "ELEVENLABS_API_KEY", True, elevenlabs.synthesize),
        "deepgram": Provider("deepgram", "DEEPGRAM_API_KEY", False, deepgram.synthesize),
        "kokoro": Provider("kokoro", None, False, kokoro.synthesize),
    }


# Name -> key env var; config validation needs this without importing HTTP clients.
KEYS: dict[str, str | None] = {
    "cartesia": "CARTESIA_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "deepgram": "DEEPGRAM_API_KEY",
    "kokoro": None,
}


def provider(name: str) -> Provider:
    return _load()[name]
