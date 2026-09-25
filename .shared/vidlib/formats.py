"""Named output formats.

The config picks a format by name. Render, captions and QC read dimensions and
the caption safe zone from here, so a new format is one entry in FORMATS plus
whatever check proves it renders well. A format with `supported=False` is known
by name but refused at preflight: it fails clearly instead of rendering badly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SafeZone:
    """Pixels to keep clear of platform UI, measured from each edge."""

    top: int
    bottom: int
    left: int
    right: int


@dataclass(frozen=True)
class Format:
    name: str
    width: int
    height: int
    aspect: str
    fps: int
    safe: SafeZone
    # Longest video the platform accepts in this slot. Config lengths must fit.
    max_duration_s: int
    supported: bool

    def to_dict(self) -> dict:
        return asdict(self)


# 9:16 safe zone: keep captions and critical text inside the centred 900x1400 box
# that clears the TikTok, Reels and Shorts UI with one master (research: models §6).
_VERTICAL_SAFE = SafeZone(top=260, bottom=260, left=90, right=90)

FORMATS: dict[str, Format] = {
    f.name: f
    for f in (
        Format("shorts", 1080, 1920, "9:16", 30, _VERTICAL_SAFE, 180, True),
        Format("reels", 1080, 1920, "9:16", 30, _VERTICAL_SAFE, 180, True),
        Format("tiktok", 1080, 1920, "9:16", 30, _VERTICAL_SAFE, 600, True),
        Format("youtube", 1920, 1080, "16:9", 30, SafeZone(60, 90, 96, 96), 3600, False),
        Format("square", 1080, 1080, "1:1", 30, SafeZone(60, 120, 60, 60), 600, False),
    )
}


def get_format(name: str) -> Format:
    try:
        return FORMATS[name]
    except KeyError:
        known = ", ".join(FORMATS)
        raise ValueError(f"unknown format {name!r}; known formats: {known}") from None
