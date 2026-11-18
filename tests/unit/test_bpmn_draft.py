"""Process draft: steps from text, generated BPMN, role matching, JSON from AI answers."""

from grc_api.domain import assistant as asst
from grc_api.domain import bpmn_draft as bd
from grc_api.domain.bpmn import activities, is_bpmn


def test_steps_from_text() -> None:
    steps = bd.steps_from_text(
        "1. Retoure erfassen (Vertrieb)\n- Ware prüfen (Lager)\nWare in Ordnung?\n\n"
        "Gutschrift erstellen; Kunden informieren"
    )
    assert [(s.name, s.type, s.role) for s in steps] == [
        ("Retoure erfassen", "task", "Vertrieb"),
        ("Ware prüfen", "task", "Lager"),
        ("Ware in Ordnung?", "decision", ""),
        ("Gutschrift erstellen", "task", ""),
        ("Kunden informieren", "task", ""),
    ]


def test_generate_is_valid_bpmn_with_ids_per_step() -> None:
    steps = [
        bd.Step("Retoure <erfassen>", "task"),
        bd.Step("Ware ok?", "decision", no="Abgelehnt"),
        bd.Step("Gutschrift buchen", "system"),
    ]
    xml, ids = bd.generate('Retoure & "Gutschrift"', steps, "P009", "Start", "Ende")
    assert is_bpmn(xml)
    assert ids == ["P009_T1", "P009_G2", "P009_T3"]
    assert dict(activities(xml)) == {
        "P009_T1": "Retoure <erfassen>",
        "P009_T3": "Gutschrift buchen",
    }
    assert 'name="nein"' in xml
    assert 'name="Abgelehnt"' in xml


def test_match_role() -> None:
    roles = {"RO-001": "Einkäufer", "RO-002": "Wareneingang / Lager"}
    assert bd.match_role("einkäufer", roles) == "RO-001"
    assert bd.match_role("RO-002", roles) == "RO-002"
    assert bd.match_role("Lager", roles) == "RO-002"
    assert bd.match_role("Vorstand", roles) == ""


def test_json_object() -> None:
    assert asst.json_object('Hier: ```json\n{"a": "x}{", "b": {"c": 1}}\n```') == {
        "a": "x}{",
        "b": {"c": 1},
    }
    assert asst.json_object("kein JSON") is None
    assert asst.json_object("[1, 2]") is None
