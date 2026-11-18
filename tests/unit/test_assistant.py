"""Catalogue search and link checking of the assistant."""

from grc_api.domain import assistant as asst

CAT = [
    asst.Entry("step", "P-008/T3", "Sanktionslisten prüfen", "Export · Zoll (R)", "x"),
    asst.Entry("processes", "P-008", "Exportkontrolle", "Kernprozess", "Ausfuhr Zoll"),
    asst.Entry("role", "RO-001", "Datenschutzbeauftragter", "Rolle", "DSGVO Beratung"),
]


def test_search_finds_compound_words_and_ranks_labels() -> None:
    hits = asst.search(CAT, "Wo finde ich die Sanktionslistenprüfung?")
    assert hits[0].id == "P-008/T3"
    assert asst.search(CAT, "wer ist für die DSGVO zuständig")[0].id == "RO-001"
    assert asst.search(CAT, "wo ist der") == []


def test_checked_links() -> None:
    text = "Siehe [[step:P-008/T3|Prüfung]] und [[risk:R-1|Geheim]] sowie [[role:RO-001|DSB]]."
    assert asst.checked_links(text, CAT) == (
        "Siehe [[step:P-008/T3|Prüfung]] und Geheim sowie [[role:RO-001|DSB]]."
    )


def test_prompts() -> None:
    system = asst.system_prompt("en", CAT)
    assert "Answer in English" in system
    assert "[[role:RO-001|Datenschutzbeauftragter]] — Rolle" in system
    q = asst.question_prompt("Frage?", "Anna (Einkauf)", CAT[:1])
    assert q.endswith("Question: Frage?")
    assert "Anna (Einkauf)" in q
