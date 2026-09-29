"""WCAG 2.x contrast helpers and the locked palette (DESIGN_SYSTEM.md v0.6 §2, derived tokens §12).

Pure Python so the tests run in CI without imaging libraries. ``render.py`` uses these for the
per-pixel measurement of the mockups on the stand-in scans (ticket M0-DSGN-01, AT-2).
"""

from __future__ import annotations

PALETTE = {
    "accent.amber": "#F2A93B",
    "accent.amberLight": "#FFD27A",
    "ink.charcoal": "#1C1F26",
    "surface.charcoal": "#2A2E37",
    "paper.cream": "#F5EFE6",
    "surface.cream": "#EDE5D8",
    "text.muted": "#8A8F99",
    "semantic.teal": "#00585E",
    "semantic.sage": "#7A8F7B",
    "semantic.terracotta": "#C9573D",
}
DERIVED = {"muted-on-cream": "#63676E", "muted-on-charcoal": "#90959F"}
TEXT_MIN = 4.5
ICON_MIN = 3.0

# Machado, Oliveira and Fernandes (2009), severity 1.0, applied in linear RGB.
CVD = {
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_hex(rgb) -> str:
    return "#" + "".join(f"{round(max(0, min(255, c))):02X}" for c in rgb[:3])


def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return 255.0 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def luminance(rgb) -> float:
    r, g, b = (_lin(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def over(fg, alpha: float, bg) -> tuple[float, float, float]:
    """Source-over compositing in sRGB space, as browsers and UI Toolkit blend by default."""
    return tuple(alpha * f + (1 - alpha) * b for f, b in zip(fg[:3], bg[:3]))


def worst_case(fg, scrim, alpha: float) -> float:
    """Lowest contrast of ``fg`` on ``scrim`` at ``alpha`` over any background (black or white is extreme)."""
    return min(ratio(fg, over(scrim, alpha, (0, 0, 0))), ratio(fg, over(scrim, alpha, (255, 255, 255))))


def min_alpha(fg, scrim, target: float, step: float = 0.005) -> float | None:
    """Smallest scrim opacity for which ``fg`` reaches ``target`` over any background, or None."""
    a = 0.0
    while a <= 1.0 + 1e-9:
        if worst_case(fg, scrim, a) >= target:
            return round(a, 3)
        a += step
    return None


def simulate(rgb, kind: str) -> tuple[float, float, float]:
    m = CVD[kind]
    lin = [_lin(c) for c in rgb[:3]]
    return tuple(_gam(sum(m[i][j] * lin[j] for j in range(3))) for i in range(3))
