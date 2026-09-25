"""Load and resolve video.config.yaml.

Preflight is the only reader of the YAML file. It writes the resolved result to
$ARTIFACTS_DIR/config.json and every later node reads that copy, so editing the
config mid-run cannot change a run.

Validation is deliberately light: it rejects only what a later script needs and
cannot guess (an unknown provider, a missing key, a missing file, a format or
source this version cannot render). Everything under `brand` passes through.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .formats import FORMATS, get_format
from .voice import KEYS as VOICE_KEYS

# What this version of the pack can produce. Anything else is refused at
# preflight with "not supported yet" rather than half-built.
SUPPORTED_KINDS = {"social"}
PLANNED_KINDS = {"product", "marketing", "ugc"}
TIMINGS = {"auto", "align"}
# Providers whose voice is chosen by voice_id; Deepgram names the voice in `model`.
NEEDS_VOICE_ID = {"cartesia", "elevenlabs"}
SOURCE_MODES = {"stock"}
PLANNED_SOURCE_MODES = {"mixed", "ai"}
STOCK_PROVIDERS = {"pexels": "PEXELS_API_KEY"}
MUSIC_EXTENSIONS = {".mp3", ".wav", ".m4a"}


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


def resolve(raw: dict, kind: str, base_dir: Path, env: dict[str, str]) -> dict:
    """Return the resolved config, or raise ConfigError listing every problem."""
    problems: list[str] = []

    if raw.get("version") != 1:
        problems.append(f"version must be 1 (got {raw.get('version')!r})")

    if kind in PLANNED_KINDS:
        problems.append(f"kind {kind!r} is not supported yet; this version makes: {', '.join(sorted(SUPPORTED_KINDS))}")
    elif kind not in SUPPORTED_KINDS:
        problems.append(f"unknown kind {kind!r}; known kinds: {', '.join(sorted(SUPPORTED_KINDS | PLANNED_KINDS))}")

    brand = raw.get("brand")
    if not isinstance(brand, dict) or not brand.get("name"):
        problems.append("brand.name is required")
        brand = brand if isinstance(brand, dict) else {}

    def existing_file(value: Any, field: str) -> str | None:
        if value in (None, ""):
            return None
        p = (base_dir / str(value)).expanduser().resolve()
        if not p.exists():
            problems.append(f"{field}: {p} does not exist")
        return str(p)

    facts_path = existing_file(brand.get("facts"), "brand.facts")
    caption_font = _get(brand, "tokens", "fonts", "captions", default={}) or {}
    font_file = existing_file(caption_font.get("file"), "brand.tokens.fonts.captions.file")

    if _get(raw, "kinds", "ugc", "avatar", "enabled", default=False):
        problems.append("kinds.ugc.avatar.enabled: the synthetic avatar is not supported yet")

    # Voice
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

    # Format
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

    # Source
    mode = _get(raw, "source", "mode", default="stock")
    if mode in PLANNED_SOURCE_MODES:
        problems.append(f"source.mode {mode!r} (AI video) is not supported yet; use stock")
    elif mode not in SOURCE_MODES:
        problems.append(f"unknown source.mode {mode!r}")
    if _get(raw, "source", "motion", default=False):
        problems.append("source.motion: motion-graphics beats are not supported yet; set it to false")
    stock = _get(raw, "source", "stock", "provider", default="pexels")
    if stock not in STOCK_PROVIDERS:
        problems.append(f"unknown source.stock.provider {stock!r}")
    elif not env.get(STOCK_PROVIDERS[stock]):
        problems.append(f"source.stock.provider {stock} needs {STOCK_PROVIDERS[stock]} in Archon's env (~/.archon/.env)")

    # Music: optional. The mood folders that hold at least one track are the choices.
    music_dir = None
    moods: list[str] = []
    if _get(raw, "music", "dir"):
        music_dir = (base_dir / str(raw["music"]["dir"])).expanduser().resolve()
        if not music_dir.is_dir():
            problems.append(f"music.dir: {music_dir} is not a directory")
        else:
            moods = sorted(
                d.name
                for d in music_dir.iterdir()
                if d.is_dir() and any(f.suffix.lower() in MUSIC_EXTENSIONS for f in d.iterdir())
            )
            if not moods:
                problems.append(f"music.dir: {music_dir} has no <mood>/ folder with a track in it")

    output_dir = _get(raw, "output", "dir")

    if problems:
        raise ConfigError(problems)

    return {
        "kind": kind,
        "brand": brand,
        "facts_file": facts_path,
        "kind_options": _get(raw, "kinds", kind, default={}) or {},
        "voice": {
            "provider": provider,
            "voice_id": voice_id,
            "model": _get(raw, "voice", "model"),
            "timings": timings,
        },
        "format": fmt.to_dict() if fmt else None,
        "length_s": {"min": length_min, "max": length_max},
        "source": {"mode": mode, "motion": False, "stock": {"provider": stock}},
        "music": {
            "dir": str(music_dir) if music_dir else None,
            "moods": moods,
            "duck": bool(_get(raw, "music", "duck", default=True)),
        },
        "captions": {
            "font_family": caption_font.get("family") or "Arial Black",
            "font_file": font_file,
            "uppercase": bool(_get(brand, "tokens", "captions", "uppercase", default=True)),
            "text": _get(brand, "tokens", "colors", "text", default="#FFFFFF"),
            "accent": _get(brand, "tokens", "colors", "accent", default="#FFD60A"),
            "outline": _get(brand, "tokens", "colors", "outline", default="#000000"),
        },
        "output_dir": str((base_dir / str(output_dir)).expanduser().resolve()) if output_dir else None,
    }


def digest(raw_text: str) -> str:
    return hashlib.sha256(raw_text.encode()).hexdigest()[:16]


def load_resolved(artifacts_dir: Path) -> dict:
    """Read the copy preflight wrote. Every node after preflight uses this."""
    return json.loads((artifacts_dir / "config.json").read_text())
