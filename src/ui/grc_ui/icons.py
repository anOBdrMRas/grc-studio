"""Inline SVG icons (Tabler outline subset in icons/)."""

import re
from functools import lru_cache
from pathlib import Path

from markupsafe import Markup

ICON_DIR = Path(__file__).with_name("icons")


@lru_cache
def _inner(name: str) -> str:
    svg = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", svg, flags=re.S)
    return re.sub(r'<path stroke="none" d="M0 0h24v24H0z" fill="none"\s*/>', "", inner).strip()


def icon(name: str, cls: str = "h-4 w-4 shrink-0") -> Markup:
    # the SVG comes from the vendored icon set and `cls` only from templates
    return Markup(  # noqa: S704
        f'<svg xmlns="http://www.w3.org/2000/svg" class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_inner(name)}</svg>'
    )
