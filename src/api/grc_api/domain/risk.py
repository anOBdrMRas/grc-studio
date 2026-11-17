"""Risk assessment on the 4×4 matrix of the risk register (pure)."""

from typing import Literal

Level = Literal["low", "medium", "high"]

SCALE = 4
MEDIUM_FROM = 4  # score ≥ 4: medium
HIGH_ABOVE = 8  # score > 8: higher risk – needs treatment or documented acceptance


def score(likelihood: int, impact: int) -> int:
    """Likelihood × impact, 0 while one of them is not assessed."""
    return max(likelihood, 0) * max(impact, 0)


def level(value: int) -> Level:
    if value > HIGH_ABOVE:
        return "high"
    if value >= MEDIUM_FROM:
        return "medium"
    return "low"


def title_from_description(description: str, limit: int = 80) -> str:
    """The first sentence of the description is the list label of a risk."""
    text = " ".join(description.split())
    if not text:
        return ""
    end = min(
        (i for i in (text.find(". "), text.find("? "), text.find("! ")) if i >= 0), default=-1
    )
    first = text[: end + 1] if end >= 0 else text
    first = first.rstrip(".")
    return first if len(first) <= limit else first[: limit - 1].rstrip() + "…"
