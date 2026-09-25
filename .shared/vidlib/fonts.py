"""A bold label font for contact and review sheets, whichever system fonts exist."""

from PIL import ImageFont


def label_font(size: int) -> ImageFont.ImageFont:
    for name in ("Arial Bold.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()
