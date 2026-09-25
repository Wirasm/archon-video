"""Frames from the finished video, per beat: for vision review and the variety check."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from . import media
from .fonts import label_font

FRAME_H = 400
PER_SHEET = 6
COLUMNS = 2


def extract(video: Path, beats: list[dict], dest: Path) -> dict[str, list[Path]]:
    """First, middle and last frame of each beat as it appears in the final cut."""
    dest.mkdir(parents=True, exist_ok=True)
    frames: dict[str, list[Path]] = {}
    for b in beats:
        inset = min(0.15, b["duration"] / 4)
        times = (b["start"] + inset, b["start"] + b["duration"] / 2, b["end"] - inset)
        paths = []
        for k, t in enumerate(times):
            p = dest / f"{b['id']}-{k + 1}.jpg"
            media.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(video),
                       "-frames:v", "1", "-vf", f"scale=-2:{FRAME_H}", "-q:v", "3", str(p)])
            paths.append(p)
        frames[b["id"]] = paths
    return frames


def sheets(frames: dict[str, list[Path]], dest: Path) -> list[Path]:
    """Numbered review sheets, six beats each, three frames per beat."""
    ids = list(frames)
    out = []
    font = label_font(34)
    for s in range(0, len(ids), PER_SHEET):
        chunk = ids[s:s + PER_SHEET]
        first = Image.open(frames[chunk[0]][0])
        fw, fh = first.size
        pad, label = 14, 48
        cell_w, cell_h = fw * 3 + 8 + pad, fh + label + pad
        rows = (len(chunk) + COLUMNS - 1) // COLUMNS
        sheet = Image.new("RGB", (COLUMNS * cell_w + pad, rows * cell_h + pad), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        for n, bid in enumerate(chunk):
            x0, y0 = pad + (n % COLUMNS) * cell_w, pad + (n // COLUMNS) * cell_h
            draw.text((x0, y0 + 4), bid, fill=(255, 214, 10), font=font)
            for k, p in enumerate(frames[bid]):
                sheet.paste(Image.open(p), (x0 + k * (fw + 4), y0 + label))
        path = dest / f"review-{s // PER_SHEET + 1}.jpg"
        sheet.save(path, quality=85)
        out.append(path)
    return out
