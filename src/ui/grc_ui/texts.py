"""Translated texts for the stable error codes of the API."""

from grc_ui.i18n import N_, gettext

ERRORS = {
    "not_authenticated": N_("Please sign in."),
    "csrf_failed": N_("Your session has expired. Please reload the page."),
    "forbidden": N_("You are not allowed to do this."),
    "not_found": N_("The element no longer exists."),
    "version_conflict": N_(
        "Someone else changed this element in the meantime. Load the current values."
    ),
    "version_required": N_("The version of the element is missing."),
    "invalid": N_("Please check your entries."),
    "login_failed": N_("Sign-in failed."),
    "demo_login_disabled": N_("The demo sign-in is switched off."),
    "four_eyes": N_(
        "Four-eyes principle: whoever gave the business approval may not give the quality approval."
    ),
    "workflow_state": N_("This step is not possible in the current status."),
    "conflict": N_("This is not possible."),
}


def error_text(code: str, detail: str = "") -> str:
    msg = ERRORS.get(code)
    return gettext(msg) if msg else (detail or gettext("Something went wrong."))
