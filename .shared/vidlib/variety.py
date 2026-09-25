"""Near-duplicate shots, within a video and against recent videos.

A 64-bit difference hash of each beat's middle frame. Two shots within
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


def repeats_within(hashes: dict[str, str]) -> dict[str, str]:
    """beat id -> the earlier beat it repeats."""
    ids = list(hashes)
    found = {}
    for i, later in enumerate(ids):
        for earlier in ids[:i]:
            if distance(hashes[later], hashes[earlier]) <= MAX_DISTANCE:
                found[later] = earlier
                break
    return found


def repeats_across(hashes: dict[str, str], library: list[dict]) -> dict[str, str]:
    """beat id -> run id of a recent stored video with a matching shot."""
    found = {}
    for bid, h in hashes.items():
        for row in library:
            if any(distance(h, other) <= MAX_DISTANCE for other in row.get("frame_hashes", [])):
                found[bid] = row["run_id"]
                break
    return found
