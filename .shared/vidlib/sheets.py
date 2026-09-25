"""Labelled frame sheets: how agents look at clips and cuts without watching video."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from . import media
from .fonts import label_font

FRAME_H = 400


def frame(video: Path, t: float, dest: Path) -> Path:
    media.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(video),
               "-frames:v", "1", "-vf", f"scale=-2:{FRAME_H}", "-q:v", "3", str(dest)])
    return dest


def build(groups: list[tuple[str, list[Path]]], dest_dir: Path, name: str, per_sheet: int = 6, columns: int = 2) -> list[Path]:
    """One cell per (label, frames) group, `per_sheet` cells per image."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    font = label_font(34)
    out = []
    for s in range(0, len(groups), per_sheet):
        chunk = groups[s:s + per_sheet]
        images = [[Image.open(p) for p in paths] for _, paths in chunk]
        fh = FRAME_H
        widths = [sum(im.width for im in ims) + 4 * (len(ims) - 1) for ims in images]
        pad, label_h = 14, 48
        cell_w = max(widths) + pad
        cell_h = fh + label_h + pad
        rows = (len(chunk) + columns - 1) // columns
        sheet = Image.new("RGB", (min(columns, len(chunk)) * cell_w + pad, rows * cell_h + pad), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        for n, ((label, _), ims) in enumerate(zip(chunk, images)):
            x0, y0 = pad + (n % columns) * cell_w, pad + (n // columns) * cell_h
            draw.text((x0, y0 + 4), label, fill=(255, 214, 10), font=font)
            x = x0
            for im in ims:
                sheet.paste(im, (x, y0 + label_h))
                x += im.width + 4
        path = dest_dir / f"{name}-{s // per_sheet + 1}.jpg"
        sheet.save(path, quality=85)
        out.append(path)
    return out
