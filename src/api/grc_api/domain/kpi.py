"""KPI traffic light from the latest measurement (pure)."""

from typing import Literal

Traffic = Literal["green", "yellow", "red", "none"]


def status(last_value: float | None, direction: str, target: float, critical: float) -> Traffic:
    """Green when the target is met, red beyond the critical threshold, yellow in between."""
    if last_value is None:
        return "none"
    if direction == "lower":
        if last_value <= target:
            return "green"
        return "yellow" if last_value < critical else "red"
    if last_value >= target:
        return "green"
    return "yellow" if last_value > critical else "red"
