"""Risk assessment on the 4×4 matrix."""

import pytest

from grc_api.domain import risk
from grc_api.domain.catalogs import all_catalogs


@pytest.mark.parametrize(
    ("likelihood", "impact", "level"),
    [
        (1, 3, "low"),
        (1, 4, "medium"),
        (2, 2, "medium"),
        (2, 4, "medium"),
        (3, 3, "high"),
        (4, 4, "high"),
    ],
)
def test_level_thresholds(likelihood: int, impact: int, level: str) -> None:
    assert risk.level(risk.score(likelihood, impact)) == level


def test_not_assessed_scores_zero() -> None:
    assert risk.score(0, 4) == 0
    assert risk.level(0) == "low"


def test_title_is_first_sentence() -> None:
    assert (
        risk.title_from_description("Lieferant fällt aus. Produktion steht.")
        == "Lieferant fällt aus"
    )
    assert risk.title_from_description("  Ohne Punkt  ") == "Ohne Punkt"
    assert risk.title_from_description("") == ""
    long = "x" * 120
    assert len(risk.title_from_description(long)) == 80


def test_matrix_catalogue_matches_rule() -> None:
    cells = all_catalogs()["risk_matrix"]
    assert len(cells) == 16
    assert cells[0] == "low"  # 1 × 1
    assert cells[(3 - 1) * 4 + (3 - 1)] == "high"  # 3 × 3 = 9
    assert cells[(2 - 1) * 4 + (4 - 1)] == "medium"  # 2 × 4 = 8
