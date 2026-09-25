"""A numbered contact sheet: one cell per candidate, three frames each."""

from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from ..fonts import label_font

FRAME_H = 300
COLUMNS = 3
PAD = 16
LABEL_H = 56


def _fetch(url: str) -> Image.Image:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def build(candidates: list[dict], dest: Path, out_width: int, out_height: int) -> Path:
    urls = [u for c in candidates for u in c["previews"]]
    with ThreadPoolExecutor(max_workers=8) as pool:
        images = list(pool.map(_fetch, urls))
    frames = [images[i * 3:(i + 1) * 3] for i in range(len(candidates))]

    aspect = out_width / out_height
    frame_w = int(FRAME_H * aspect)
    cell_w = frame_w * 3 + PAD * 2
    cell_h = FRAME_H + LABEL_H
    rows = (len(candidates) + COLUMNS - 1) // COLUMNS
    sheet = Image.new("RGB", (COLUMNS * cell_w + PAD, rows * (cell_h + PAD) + PAD), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    font = label_font(36)
    for n, (c, imgs) in enumerate(zip(candidates, frames)):
        x0 = PAD + (n % COLUMNS) * cell_w
        y0 = PAD + (n // COLUMNS) * (cell_h + PAD)
        draw.text((x0, y0 + 8), f"#{n + 1}   {c['duration']:.0f}s", fill=(255, 214, 10), font=font)
        for k, img in enumerate(imgs):
            # Centre-crop each preview to the output aspect so the sheet shows what survives the frame.
            img_aspect = img.width / img.height
            if img_aspect > aspect:
                w = int(img.height * aspect)
                img = img.crop(((img.width - w) // 2, 0, (img.width - w) // 2 + w, img.height))
            sheet.paste(img.resize((frame_w, FRAME_H)), (x0 + k * (frame_w + 4), y0 + LABEL_H))
    sheet.save(dest, quality=88)
    return dest
