"""Internal control system check of a process step (pure)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Gap:
    risk_id: str
    # controls that mitigate the risk elsewhere and could be assigned to this step
    suggestions: tuple[str, ...]


def gaps(
    step_risks: list[str], step_controls: list[str], mitigates: dict[str, list[str]]
) -> list[Gap]:
    """Risks of a step that no control of the same step mitigates (`mitigates`: control → risks)."""
    covered = {r for c in step_controls for r in mitigates.get(c, [])}
    return [
        Gap(
            r, tuple(sorted(c for c, rs in mitigates.items() if r in rs and c not in step_controls))
        )
        for r in step_risks
        if r not in covered
    ]
