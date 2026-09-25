"""Load and resolve video.config.yaml: design tokens, voice, format, sources.

Preflight is the only reader of the YAML file. It writes the resolved result to
$ARTIFACTS_DIR/config.json and every later node reads that copy, so editing the
config mid-run cannot change a run.

Validation rejects only what a later script needs and cannot guess: an unknown
provider, a missing key, a missing file, a format this version cannot render.
The brand block passes through to the agents unvalidated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .formats import FORMATS, get_format
from .voice import KEYS as VOICE_KEYS

TIMINGS = {"auto", "align"}
# Providers whose voice is chosen by voice_id; Deepgram names the voice in `model`.
NEEDS_VOICE_ID = {"cartesia", "elevenlabs"}
STOCK_PROVIDERS = {"pexels": "PEXELS_API_KEY"}
MUSIC_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}


class ConfigError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def _get(d: Any, *path: str, default: Any = None) -> Any:
    for key in path:
        if not isinstance(d, dict) or key not in d:
            return default
        d = d[key]
    return d


def resolve(raw: dict, base_dir: Path, env: dict[str, str]) -> dict:
    """Return the resolved config, or raise ConfigError listing every problem."""
    problems: list[str] = []

    if raw.get("version") != 1:
        problems.append(f"version must be 1 (got {raw.get('version')!r})")
    for retired in ("kinds", "source"):
        if retired in raw:
            problems.append(f"`{retired}` is no longer a config key: the brief decides what a video is and how it is made")

    brand = raw.get("brand")
    if not isinstance(brand, dict) or not brand.get("name"):
        problems.append("brand.name is required")
        brand = brand if isinstance(brand, dict) else {}

    def existing_file(value: Any, field: str) -> Path | None:
        if value in (None, ""):
            return None
        p = (base_dir / str(value)).expanduser().resolve()
        if not p.is_file():
            problems.append(f"{field}: {p} does not exist")
        return p

    facts = existing_file(brand.get("facts"), "brand.facts")
    logo = existing_file(brand.get("logo"), "brand.logo")
    font_files: dict[str, str] = {}
    for role, font in (brand.get("fonts") or {}).items():
        if isinstance(font, dict) and font.get("file"):
            p = existing_file(font["file"], f"brand.fonts.{role}.file")
            if p and p.suffix.lower() not in FONT_EXTENSIONS:
                problems.append(f"brand.fonts.{role}.file must be one of {sorted(FONT_EXTENSIONS)}")
            if p:
                font_files[role] = str(p)

    if _get(raw, "avatar", "enabled", default=False):
        problems.append("avatar.enabled: the synthetic avatar is not supported yet")

    provider = _get(raw, "voice", "provider", default="cartesia")
    voice_id = _get(raw, "voice", "voice_id")
    timings = _get(raw, "voice", "timings", default="auto")
    if provider not in VOICE_KEYS:
        problems.append(f"unknown voice.provider {provider!r}; known: {', '.join(VOICE_KEYS)}")
    else:
        key = VOICE_KEYS[provider]
        if key and not env.get(key):
            problems.append(f"voice.provider {provider} needs {key} in Archon's env (~/.archon/.env)")
        if provider in NEEDS_VOICE_ID and not voice_id:
            problems.append(f"voice.voice_id is required for {provider}")
    if timings not in TIMINGS:
        problems.append(f"voice.timings must be auto or align (got {timings!r})")

    fmt_name = raw.get("format", "shorts")
    fmt = None
    if not isinstance(fmt_name, str):
        problems.append(f"format must be a name ({', '.join(FORMATS)}), got {fmt_name!r}")
    else:
        try:
            fmt = get_format(fmt_name)
            if not fmt.supported:
                problems.append(f"format {fmt_name!r} ({fmt.aspect}) is not supported yet; use shorts, reels or tiktok")
        except ValueError as err:
            problems.append(str(err))

    length_min = _get(raw, "length_s", "min", default=25)
    length_max = _get(raw, "length_s", "max", default=45)
    if not (isinstance(length_min, (int, float)) and isinstance(length_max, (int, float)) and 0 < length_min <= length_max):
        problems.append(f"length_s needs 0 < min <= max (got {length_min!r}, {length_max!r})")
    elif fmt and length_max > fmt.max_duration_s:
        problems.append(f"length_s.max {length_max} exceeds the {fmt.name} ceiling of {fmt.max_duration_s}s")

    stock = _get(raw, "stock", "provider", default="pexels")
    if stock not in STOCK_PROVIDERS:
        problems.append(f"unknown stock.provider {stock!r}")
    elif not env.get(STOCK_PROVIDERS[stock]):
        problems.append(f"stock.provider {stock} needs {STOCK_PROVIDERS[stock]} in Archon's env (~/.archon/.env)")

    music: list[str] = []
    music_dir = None
    if _get(raw, "music", "dir"):
        music_dir = (base_dir / str(raw["music"]["dir"])).expanduser().resolve()
        if not music_dir.is_dir():
            problems.append(f"music.dir: {music_dir} is not a directory")
        else:
            music = sorted(str(p) for p in music_dir.rglob("*") if p.suffix.lower() in MUSIC_EXTENSIONS)
            if not music:
                problems.append(f"music.dir: {music_dir} holds no audio files")

    output_dir = _get(raw, "output", "dir")
    if problems:
        raise ConfigError(problems)

    return {
        "brand": brand,
        "facts_file": str(facts) if facts else None,
        "logo_file": str(logo) if logo else None,
        "font_files": font_files,
        "voice": {"provider": provider, "voice_id": voice_id, "model": _get(raw, "voice", "model"), "timings": timings},
        "format": fmt.to_dict() if fmt else None,
        "length_s": {"min": length_min, "max": length_max},
        "stock": {"provider": stock},
        "music": {"dir": str(music_dir) if music_dir else None, "tracks": music},
        "output_dir": str((base_dir / str(output_dir)).expanduser().resolve()) if output_dir else None,
    }


def digest(raw_text: str) -> str:
    return hashlib.sha256(raw_text.encode()).hexdigest()[:16]


def load_resolved(artifacts_dir: Path) -> dict:
    """Read the copy preflight wrote. Every node after preflight uses this."""
    return json.loads((artifacts_dir / "config.json").read_text())
