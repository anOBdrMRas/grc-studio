"""KPI traffic light and the ICS check of a process step."""

import pytest

from grc_api.domain import ics, kpi


@pytest.mark.parametrize(
    ("value", "light"), [(100, "green"), (101, "green"), (97, "yellow"), (95, "red"), (90, "red")]
)
def test_higher_is_better(value: float, light: str) -> None:
    assert kpi.status(value, "higher", target=100, critical=95) == light


@pytest.mark.parametrize(("value", "light"), [(2, "green"), (3, "yellow"), (5, "red"), (6, "red")])
def test_lower_is_better(value: float, light: str) -> None:
    assert kpi.status(value, "lower", target=2, critical=5) == light


def test_no_value() -> None:
    assert kpi.status(None, "higher", target=1, critical=0) == "none"


def test_gap_when_no_control_of_the_step_mitigates() -> None:
    mitigates = {"K-1": ["R-1"], "K-2": ["R-1", "R-2"], "K-3": ["R-3"]}
    found = ics.gaps(["R-1", "R-2"], ["K-3"], mitigates)
    assert [g.risk_id for g in found] == ["R-1", "R-2"]
    assert found[0].suggestions == ("K-1", "K-2")
    assert ics.gaps(["R-1", "R-2"], ["K-2"], mitigates) == []


def test_risk_without_any_control_has_no_suggestion() -> None:
    assert ics.gaps(["R-9"], [], {"K-1": ["R-1"]})[0].suggestions == ()
