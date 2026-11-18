"""Rules of the content administration (pure domain)."""

import pytest

from grc_api.domain import content as ct


def _cfg(*fields: ct.CustomField, kind: str = "risk") -> ct.Config:
    return ct.Config(fields={kind: list(fields)})


def test_custom_key_from_label() -> None:
    assert ct.custom_key("Größe der Anlage", set()) == "x_groesse_der_anlage"
    assert ct.custom_key("Größe der Anlage", {"x_groesse_der_anlage"}) == "x_groesse_der_anlage_2"
    assert ct.custom_key("!!!", set()) == "x_field"


def test_checked_assigns_keys_and_keeps_removed_fields() -> None:
    old = _cfg(ct.CustomField("x_old", "Old", "text"))
    new = _cfg(ct.CustomField("", "New", "select", options=["a", " a ", "", "b"]))
    out = ct.checked(new, old, {"risk": {"category"}})
    fields = {f.key: f for f in out.fields["risk"]}
    assert fields["x_new"].options == ["a", "b"]
    assert fields["x_old"].removed is True


@pytest.mark.parametrize(
    "new",
    [
        _cfg(ct.CustomField("", "", "text")),
        _cfg(ct.CustomField("", "X", "color")),
        _cfg(ct.CustomField("", "X", "select")),
        _cfg(ct.CustomField("bad key", "X", "text")),
        _cfg(ct.CustomField("x_a", "A", "text"), ct.CustomField("x_a", "B", "text")),
        _cfg(ct.CustomField("", "X", "text"), kind="nope"),
        ct.Config(options={"risk.unknown": ["x"]}),
    ],
)
def test_checked_rejects(new: ct.Config) -> None:
    with pytest.raises(ct.ContentError):
        ct.checked(new, ct.Config(), {"risk": {"category"}})


def test_type_of_existing_field_is_fixed() -> None:
    old = _cfg(ct.CustomField("x_a", "A", "text"))
    with pytest.raises(ct.ContentError):
        ct.checked(_cfg(ct.CustomField("x_a", "A", "number")), old, {})


def test_values() -> None:
    cfg = _cfg(
        ct.CustomField("x_n", "N", "number"),
        ct.CustomField("x_d", "D", "date"),
        ct.CustomField("x_b", "B", "bool"),
        ct.CustomField("x_s", "S", "select", options=["a"]),
        ct.CustomField("x_m", "M", "multiselect", options=["a", "b"]),
        ct.CustomField("x_gone", "G", "text", removed=True),
    )
    assert ct.values(
        cfg, "risk", {"x_n": 3, "x_d": "2026-01-31", "x_b": True, "x_s": "a", "x_m": ["b"]}, {}
    ) == {"x_n": 3, "x_d": "2026-01-31", "x_b": True, "x_s": "a", "x_m": ["b"]}
    assert ct.values(cfg, "risk", {"x_n": "", "x_m": None, "x_b": None}, {}) == {
        "x_n": None,
        "x_m": [],
        "x_b": False,
    }
    # a value removed from the list stays valid where it is stored
    assert ct.values(cfg, "risk", {"x_s": "old"}, {"x_s": "old"}) == {"x_s": "old"}
    for bad in ({"x_n": True}, {"x_d": "31.01."}, {"x_s": "z"}, {"x_m": "a"}, {"x_gone": "x"}):
        with pytest.raises(ct.ContentError):
            ct.values(cfg, "risk", bad, {})
