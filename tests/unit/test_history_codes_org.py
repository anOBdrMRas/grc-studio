"""History diffs, element codes, segregation of duties, BPMN names."""

from grc_api.domain.bpmn import element_names
from grc_api.domain.codes import full_name, next_code
from grc_api.domain.history import diff, state_at
from grc_api.domain.org import sod_conflicts


def test_diff_ignores_technical_fields() -> None:
    before = {"title": "A", "version": 1, "xml": "<a/>", "note": ""}
    after = {"title": "B", "version": 2, "xml": "<b/>", "note": ""}
    assert diff(before, after) == [{"key": "title", "from": "A", "to": "B"}]


def test_state_at_reverts_later_changes() -> None:
    current = {"title": "C", "note": "x"}
    later = [
        [{"key": "title", "from": "B", "to": "C"}],
        [{"key": "title", "from": "A", "to": "B"}, {"key": "note", "from": "", "to": "x"}],
    ]
    assert state_at(current, later[:1]) == {"title": "B", "note": "x"}
    assert state_at(current, later) == {"title": "A", "note": ""}


def test_next_code() -> None:
    assert next_code(["RO-001", "RO-017", "X-999"], "RO") == "RO-018"
    assert next_code([], "P") == "P-001"


def test_full_name() -> None:
    assert full_name(" Anna ", "Berger") == "Anna Berger"
    assert full_name("", "Berger") == "Berger"


def test_sod_conflicts_symmetric() -> None:
    inc = {"RO-1": ["RO-2"]}
    assert sod_conflicts(["RO-2", "RO-1", "RO-3"], inc) == [("RO-2", "RO-1")]
    assert sod_conflicts(["RO-3"], inc) == []


def test_bpmn_element_names_and_hostile_xml() -> None:
    xml = (
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">'
        '<bpmn:process id="P"><bpmn:task id="T1" name="Prüfen"/><bpmn:task id="T2"/></bpmn:process></bpmn:definitions>'
    )
    names = element_names(xml)
    assert names["T1"] == "Prüfen"
    assert names["T2"] == "T2"
    assert element_names("not xml") == {}
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><x>&a;</x>'
    assert element_names(bomb) == {}


def test_is_bpmn() -> None:
    from grc_api.domain.bpmn import is_bpmn

    assert is_bpmn('<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"/>')
    assert not is_bpmn("<svg/>")
    assert not is_bpmn('<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "a">]><d/>')


def test_org_tree_roots_children_cycles_and_separate() -> None:
    from grc_api.domain.org import tree

    t = tree(
        [
            ("A", None),
            ("B", "A"),
            ("C", "A"),
            ("D", "B"),
            ("X", "Y"),  # cycle X ↔ Y
            ("Y", "X"),
            ("N", "n/a"),
        ]
    )
    assert t.roots == ["A", "X"]
    assert t.children["A"] == ["B", "C"]
    assert t.children["B"] == ["D"]
    assert t.separate == ["N"]
    assert tree([("N", "n/a")]).separate == []
