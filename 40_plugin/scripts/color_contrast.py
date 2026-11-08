#!/usr/bin/env python3
"""
Colour helpers shared by the validator and renderers (`40_plugin/scripts/color_contrast.py`):
WCAG contrast, OKLab distance, and colour-vision-deficiency simulation (`PRIN-DSN-006`).
"""

from __future__ import annotations

import colorsys
import math
import re
from typing import Optional, Tuple

# Machado, Oliveira & Fernandes (2009) dichromacy matrices at full severity, applied to linear RGB.
CVD_MATRICES = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, -0.691367, 1.687168)),
}


def hex_rgb01(hex_str: str) -> Optional[Tuple[float, float, float]]:
    clean = str(hex_str or "").strip().lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", clean):
        return None
    return tuple(int(clean[i:i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def relative_luminance(rgb: Tuple[float, float, float]) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_hex: str, bg_hex: str) -> Optional[float]:
    fg, bg = hex_rgb01(fg_hex), hex_rgb01(bg_hex)
    if fg is None or bg is None:
        return None
    l1, l2 = sorted((relative_luminance(fg), relative_luminance(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def readable_text_hex(fg_hex: str, bg_hex: str = "#FFFFFF", min_ratio: float = 3.0) -> str:
    """Darken `fg_hex` toward black (same hue) until it reaches `min_ratio` contrast on `bg_hex`."""
    rgb = hex_rgb01(fg_hex)
    if rgb is None or (contrast_ratio(fg_hex, bg_hex) or 0) >= min_ratio:
        return fg_hex
    h, l, s = colorsys.rgb_to_hls(*rgb)
    while l > 0:
        l = max(0.0, l - 0.02)
        cand = "#" + "".join(f"{round(c * 255):02X}" for c in colorsys.hls_to_rgb(h, l, s))
        if (contrast_ratio(cand, bg_hex) or 0) >= min_ratio:
            return cand
    return "#000000"


def inside_label_hex(fill_hex: str, dark_hex: str = "#1F2937") -> str:
    """D-057 B4, D-060: white ink on saturated fills that reach 3:1 with white; dark ink on greys and pale tints."""
    if not is_neutral(fill_hex) and (contrast_ratio("#FFFFFF", fill_hex) or 0) >= 3.0:
        return "#FFFFFF"
    return dark_hex


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def oklab(hex_str: str, cvd: Optional[str] = None) -> Optional[Tuple[float, float, float]]:
    """OKLab (L, a, b) of a colour, optionally as seen with `cvd` in {'protan', 'deutan', 'tritan'}."""
    rgb = hex_rgb01(hex_str)
    if rgb is None:
        return None
    lin = [_linear(c) for c in rgb]
    if cvd:
        lin = [sum(m * v for m, v in zip(row, lin)) for row in CVD_MATRICES[cvd]]
    r, g, b = (min(max(v, 0.0), 1.0) for v in lin)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (x ** (1 / 3) for x in (l, m, s))
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def worst_case_delta_e(hex_a: str, hex_b: str) -> Optional[Tuple[float, str]]:
    """Smallest OKLab distance between two colours over normal vision and the three dichromacies,
    with the vision type that produced it."""
    results = []
    for vision in (None, "protan", "deutan", "tritan"):
        a, b = oklab(hex_a, vision), oklab(hex_b, vision)
        if a is None or b is None:
            return None
        results.append((math.dist(a, b), vision or "normal"))
    return min(results)


def oklab_lightness(hex_str: str) -> Optional[float]:
    lab = oklab(hex_str)
    return lab[0] if lab else None


def hsv(hex_str: str) -> Optional[Tuple[float, float, float]]:
    """(hue in degrees, saturation 0–1, value 0–1)."""
    rgb = hex_rgb01(hex_str)
    if rgb is None:
        return None
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    return h * 360.0, s, v


def is_neutral(hex_str: str) -> bool:
    """True for greys (and near-greys) that read as 'no colour'."""
    hsv_val = hsv(hex_str)
    return hsv_val is not None and hsv_val[1] < 0.15


def hue_family(hex_str: str) -> Optional[str]:
    """Coarse hue family for identity checks: 'grey' or one of twelve 30-degree sectors (red, orange, …)."""
    hsv_val = hsv(hex_str)
    if hsv_val is None:
        return None
    if hsv_val[1] < 0.15:
        return "grey"
    names = ("red", "orange", "yellow", "chartreuse", "green", "spring", "cyan", "azure", "blue", "violet", "magenta", "rose")
    return names[int(((hsv_val[0] + 15.0) % 360.0) // 30.0)]


def hue_class(hex_str: str) -> Optional[str]:
    """Coarse hue bucket used for colour-blind safety checks: neutral | red | green | other."""
    rgb = hex_rgb01(hex_str)
    if rgb is None:
        return None
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    deg = h * 360
    if s < 0.15:
        return "neutral"
    if (deg <= 15 or deg >= 345) and s >= 0.45 and v >= 0.35:
        return "red"
    if 85 <= deg <= 160 and s >= 0.35 and v >= 0.25:
        return "green"
    return "other"
