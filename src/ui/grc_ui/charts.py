"""Small server-rendered SVG charts (no client-side chart library; CSP-friendly)."""

from collections.abc import Sequence
from typing import Any

WIDTH, HEIGHT, PAD = 320, 90, 8


def sparkline(values: Sequence[float], target: float | None = None) -> dict[str, Any] | None:
    """Polyline points of a series scaled into the box, plus the y of the target line."""
    if not values:
        return None
    lo = min([*values, *([target] if target is not None else [])])
    hi = max([*values, *([target] if target is not None else [])])
    span = (hi - lo) or 1.0

    def y(v: float) -> float:
        return round(PAD + (HEIGHT - 2 * PAD) * (1 - (v - lo) / span), 1)

    step = (WIDTH - 2 * PAD) / max(len(values) - 1, 1)
    points = [(round(PAD + i * step, 1), y(v)) for i, v in enumerate(values)]
    return {
        "width": WIDTH,
        "height": HEIGHT,
        "points": " ".join(f"{px},{py}" for px, py in points),
        "dots": points,
        "target_y": y(target) if target is not None else None,
    }
