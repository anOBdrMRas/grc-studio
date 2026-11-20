"""Rich text of work instructions: only the markup the editor produces is kept (no scripts, no
event handlers, no foreign styles); images only as http(s) or embedded raster/vector data."""

import re

import nh3

MAX_BYTES = 8 * 1024 * 1024  # the text with its embedded images

TAGS = {
    "p", "br", "h1", "h2", "h3", "strong", "b", "em", "i", "u", "s", "mark", "code", "pre",
    "ul", "ol", "li", "blockquote", "hr", "a", "img",
    "table", "colgroup", "col", "thead", "tbody", "tr", "th", "td",
}  # fmt: skip
ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title", "width", "height"},
    "th": {"colspan", "rowspan", "colwidth"},
    "td": {"colspan", "rowspan", "colwidth"},
    "col": {"style"},
    "table": {"style"},
    "p": {"style"},
    "h1": {"style"},
    "h2": {"style"},
    "h3": {"style"},
}
_IMAGE_DATA = re.compile(r"^data:image/(png|jpeg|gif|webp|svg\+xml)(;[a-z0-9=.+-]+)*,", re.I)
_WEB = re.compile(r"^(https?:|mailto:)", re.I)


class RichTextError(ValueError):
    pass


def _filter(tag: str, attr: str, value: str) -> str | None:
    if tag == "img" and attr == "src":
        return (
            value
            if _IMAGE_DATA.match(value) or value.lower().startswith(("https:", "http:"))
            else None
        )
    if tag == "a" and attr == "href":
        return value if _WEB.match(value) else None
    return value


def clean(html: str) -> str:
    """The sanitised HTML; an empty document becomes ""."""
    if len(html.encode()) > MAX_BYTES:
        raise RichTextError("The text with its images is larger than 8 MB")
    out: str = nh3.clean(
        html,
        tags=TAGS,
        attributes=ATTRIBUTES,
        url_schemes={"http", "https", "mailto", "data"},
        attribute_filter=_filter,
        filter_style_properties={"text-align", "width", "min-width"},
        link_rel="noopener noreferrer nofollow",
    )
    return "" if re.fullmatch(r"(\s|<p>\s*</p>|<br\s*/?>)*", out) else out


def plain(html: str) -> str:
    """Text without markup (search, AI, history summaries)."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
