"""Change history: field differences and the state of an element after a given change."""

from typing import Any

IGNORED = frozenset({"id", "version", "created_at", "updated_at", "released", "xml"})


def diff(
    before: dict[str, Any], after: dict[str, Any], ignored: frozenset[str] = IGNORED
) -> list[dict[str, Any]]:
    keys = [k for k in after if k not in ignored]
    return [
        {"key": k, "from": before.get(k), "to": after[k]} for k in keys if before.get(k) != after[k]
    ]


def state_at(current: dict[str, Any], later_changes: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """Reverts the changes made after the wanted state (newest first)."""
    out = dict(current)
    for changes in later_changes:
        for c in changes:
            out[c["key"]] = c["from"]
    return out
