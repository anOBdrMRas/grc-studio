"""Rendering of assistant answers."""

from grc_ui.assistant import answer_html, href


def test_links_and_escaping() -> None:
    html = str(
        answer_html(
            "Im Schritt [[step:P-001/T1|Bestellung <prüfen>]] und **wichtig** "
            "[[role:RO-1|Rolle]] [[evil:x|<script>]] <b>x</b>"
        )
    )
    assert '<a class="link link-secondary font-medium" href="/processes/P-001?step=T1">' in html
    assert "Bestellung &lt;prüfen&gt;</a>" in html
    assert '<a class="link link-secondary font-medium" href="/roles/RO-1">Rolle</a>' in html
    assert "<strong>wichtig</strong>" in html
    assert "<script>" not in html
    assert "&lt;b&gt;x&lt;/b&gt;" in html


def test_href() -> None:
    assert href("mandate", "DV-001") == "/delegations/DV-001"
    assert href("processes", "P-002") == "/processes/P-002"
