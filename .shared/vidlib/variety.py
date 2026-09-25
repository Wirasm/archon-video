"""Near-duplicate shots against recent videos.

A 64-bit difference hash of frames sampled through the video. Two frames within
Hamming distance MAX_DISTANCE read as the same shot to a viewer, which is the
repetition YouTube's inauthentic-content policy targets.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

MAX_DISTANCE = 6


def dhash(path: Path) -> str:
    img = Image.open(path).convert("L").resize((9, 8), Image.LANCZOS)
    px = list(img.getdata())
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (px[row * 9 + col] > px[row * 9 + col + 1])
    return f"{bits:016x}"


def distance(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def repeats_across(hashes: dict[str, str], library: list[dict]) -> dict[str, str]:
    """label -> run id of a recent stored video with a matching frame."""
    found = {}
    for bid, h in hashes.items():
        for row in library:
            if any(distance(h, other) <= MAX_DISTANCE for other in row.get("frame_hashes", [])):
                found[bid] = row["run_id"]
                break
    return found
