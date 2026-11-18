"""Audit rules and the quality checks of the I&A cockpit."""

from datetime import date

from grc_api.domain import audits as ad
from grc_api.domain import quality as q

TODAY = date(2026, 11, 18)


def test_open_and_overdue() -> None:
    assert ad.is_open("Minor nonconformity", "Implemented")
    assert not ad.is_open("Positive finding", "Open")
    assert not ad.is_open("Observation", "Closed")
    assert ad.is_overdue("Observation", "Open", date(2026, 1, 1), TODAY)
    assert not ad.is_overdue("Observation", "Open", None, TODAY)


def test_responsible_may_document_but_not_verify() -> None:
    assert ad.responsible_may_change({"root_cause": "x", "status": "Implemented"})
    assert not ad.responsible_may_change({"status": "Closed"})
    assert not ad.responsible_may_change({"due_date": "2027-01-01"})


def test_independence() -> None:
    procs = [
        ad.AuditedProcess("P-1", "RO-OWN", frozenset({"RO-R"})),
        ad.AuditedProcess("P-2", None, frozenset()),
    ]
    found = ad.independence(["U-1", "U-2", "U-1", ""], {"U-1": {"RO-OWN"}, "U-2": {"RO-R"}}, procs)
    assert [(c.user_id, c.process_id, c.role_id) for c in found] == [
        ("U-1", "P-1", "RO-OWN"),
        ("U-2", "P-1", "RO-R"),
    ]


def empty() -> q.Snapshot:
    return q.Snapshot([], [], [], [], [], [], [], [], [], [])


def by_key(found: list[q.Check]) -> dict[str, list[q.Item]]:
    return {c.key: c.items for c in found}


def test_all_checks_present_and_empty_without_data() -> None:
    found = q.checks(empty(), TODAY)
    assert len(found) == 33
    assert len({c.key for c in found}) == 33
    assert all(not c.items for c in found)


def test_process_and_risk_checks() -> None:
    d = empty()
    d.processes.append(
        q.ProcessRec(
            "P-1", "P-1 A", None, "", None, (("T1", "Step"), ("T2", "Other")), frozenset({"T1"})
        )
    )
    d.risks.append(
        q.RiskRec(
            "R-1",
            "R-1 X",
            None,
            12,
            "d",
            "c",
            "",
            "",
            "",
            "Reduce",
            (("Act", None),),
            "In treatment",
            date(2026, 1, 1),
        )
    )
    d.controls.append(q.ControlRec("K-1", "K-1", "RO-1", (), "Partially effective", True, None))
    found = by_key(q.checks(d, TODAY))
    assert [i.id for i in found["proc-owner"]] == ["P-1"]
    assert [i.element_id for i in found["proc-steps"]] == ["T2"]
    assert {"risk-owner", "risk-control", "risk-high", "risk-reason", "risk-treat"} <= {
        k for k, v in found.items() if v
    }
    assert found["review"][0].detail == "2026-01-01"
    assert found["ctl-key"][0].vars == {}  # translatable detail
    assert [i.id for i in found["ctl-risk"]] == ["K-1"]


def test_certificates_only_latest_per_standard() -> None:
    d = empty()
    old = q.AuditRec(
        "A-1",
        "A-1",
        "A-1",
        "Certification audit",
        "Completed",
        None,
        None,
        ("ISO 9001",),
        date(2026, 1, 1),
        0,
    )
    new = q.AuditRec(
        "A-2",
        "A-2",
        "A-2",
        "Certification audit",
        "Completed",
        None,
        None,
        ("ISO 9001",),
        date(2027, 3, 1),
        0,
    )
    d.audits.extend([old, new])
    items = by_key(q.checks(d, TODAY))["audit-cert"]
    assert [(i.id, i.detail) for i in items] == [("A-2", "2027-03-01")]
    d.audits.remove(new)
    items = by_key(q.checks(d, TODAY))["audit-cert"]
    assert items[0].detail == "expired on {date}"


def test_grades() -> None:
    d = empty()
    d.roles.extend(
        [
            q.RoleRec("RO-1", "RO-1", None, "x", "x", 1, False, None),
            q.RoleRec("RO-2", "RO-2", "U-1", "x", "x", 1, False, None),
        ]
    )
    grades = q.grades(q.checks(d, TODAY), {"role": ["RO-1", "RO-2"]})
    assert grades["role"] == 50
    assert grades["process"] == 100
