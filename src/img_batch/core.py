"""Image pipeline: trim, square-pad, resize, flatten, strip metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageChops

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass
class Result:
    width: int
    height: int
    padded: bool = False


def flatten(img: Image.Image, background: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Flatten transparency onto a solid background."""
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        canvas = Image.new("RGB", img.size, background)
        canvas.paste(img, mask=img.split()[-1])
        return canvas
    return img.convert("RGB")


def trim_border(img: Image.Image, threshold: int = 245) -> Image.Image:
    """Crop uniform near-background border around the product."""
    gray = img.convert("L")
    # pixels darker than threshold are considered "product"
    mask = gray.point(lambda p: 255 if p < threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def square_pad(img: Image.Image, background: Tuple[int, int, int] = (255, 255, 255),
               margin: float = 0.04) -> Image.Image:
    """Pad to a square with a small margin around the product."""
    width, height = img.size
    side = max(width, height)
    side = int(side * (1 + 2 * margin))
    canvas = Image.new("RGB", (side, side), background)
    canvas.paste(img, ((side - width) // 2, (side - height) // 2))
    return canvas


def fit(img: Image.Image, size: int) -> Tuple[Image.Image, bool]:
    """Resize down to size; never upscale (returns flag instead)."""
    if max(img.size) <= size:
        return img, True if max(img.size) < size else False
    return img.resize((size, size), Image.LANCZOS), False


def process(path: Path, out_path: Path, size: int = 1600, quality: int = 90,
            threshold: int = 245, background: Tuple[int, int, int] = (255, 255, 255)) -> Result:
    """Full pipeline for one file. Writes JPEG without metadata.

    Output is always exactly size x size. A product smaller than the target is
    never upscaled (no blur) — it is centred on a background canvas instead and
    reported as padded.
    """
    with Image.open(path) as raw:
        img = flatten(raw, background)
    img = trim_border(img, threshold)
    img = square_pad(img, background)
    img, small = fit(img, size)

    if small:
        canvas = Image.new("RGB", (size, size), background)
        canvas.paste(img, ((size - img.size[0]) // 2, (size - img.size[1]) // 2))
        img = canvas

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=quality, progressive=True,
             optimize=True, exif=b"", icc_profile=None)
    return Result(width=img.size[0], height=img.size[1], padded=small)


def collect(source: Path) -> list:
    """All supported image files below source, sorted."""
    if source.is_file():
        return [source]
    return sorted(p for p in source.rglob("*") if p.suffix.lower() in SUPPORTED and p.is_file())
