from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageOps, ImageFilter, ImageEnhance


@dataclass(frozen=True)
class FilterResult:
    image: Image.Image
    info: str


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else float(x)


def apply_filter(img: Image.Image, name: str, strength: float = 0.5) -> FilterResult:
    """
    Apply a filter by name on a PIL Image and return (new_image, info_message).
    strength is expected in [0..1] (like your Tkinter Scale).

    Supported names (must match UI button labels):
      - Grayscale
      - Blur
      - Sharpen
      - Edge Detect
      - Emboss
      - Sepia
      - Invert
      - Threshold
      - Brightness +
      - Brightness -
      - Contrast +
      - Contrast -
      - Reset
    """
    s = _clamp01(strength)
    n = name.strip()

    src = img.copy()

    if n == "Grayscale":
        out = ImageOps.grayscale(src).convert("RGB")
        return FilterResult(out, f"Grayscale (strength={s:.2f})")

    if n == "Blur":
        radius = 0.0 + 5.0 * s
        out = src.filter(ImageFilter.GaussianBlur(radius=radius))
        return FilterResult(out, f"Blur radius={radius:.2f}")

    if n == "Sharpen":
        sharp = src.filter(ImageFilter.SHARPEN)
        out = Image.blend(src, sharp, alpha=s)
        return FilterResult(out, f"Sharpen mix={s:.2f}")

    if n == "Edge Detect":
        edges = src.filter(ImageFilter.FIND_EDGES)
        out = Image.blend(src, edges, alpha=s)
        return FilterResult(out, f"Edge Detect mix={s:.2f}")

    if n == "Emboss":
        emb = src.filter(ImageFilter.EMBOSS)
        out = Image.blend(src, emb, alpha=s)
        return FilterResult(out, f"Emboss mix={s:.2f}")

    if n == "Sepia":
        gray = ImageOps.grayscale(src)
        sepia = ImageOps.colorize(gray, black="#2b1900", white="#f7d7a6").convert("RGB")
        base = src.convert("RGB")
        out = Image.blend(base, sepia, alpha=s)
        return FilterResult(out, f"Sepia mix={s:.2f}")

    if n == "Invert":
        base = src.convert("RGB")
        inv = ImageOps.invert(base)
        out = Image.blend(base, inv, alpha=s)
        return FilterResult(out, f"Invert mix={s:.2f}")

    if n == "Threshold":
        thresh = int(255 * s)
        gray = ImageOps.grayscale(src)
        bw = gray.point(lambda p: 255 if p >= thresh else 0).convert("RGB")
        return FilterResult(bw, f"Threshold={thresh}")

    if n == "Brightness +":
        factor = 1.0 + 1.2 * s
        out = ImageEnhance.Brightness(src).enhance(factor)
        return FilterResult(out, f"Brightness factor={factor:.2f}")

    if n == "Brightness -":
        factor = 1.0 - 0.8 * s
        out = ImageEnhance.Brightness(src).enhance(factor)
        return FilterResult(out, f"Brightness factor={factor:.2f}")

    if n == "Contrast +":
        factor = 1.0 + 1.2 * s
        out = ImageEnhance.Contrast(src).enhance(factor)
        return FilterResult(out, f"Contrast factor={factor:.2f}")

    if n == "Contrast -":
        factor = 1.0 - 0.8 * s
        out = ImageEnhance.Contrast(src).enhance(factor)
        return FilterResult(out, f"Contrast factor={factor:.2f}")

    if n == "Reset":
        return FilterResult(src, "Reset should be handled in UI (restore original).")

    return FilterResult(src, f"Unknown filter: {n} (no changes applied)")
