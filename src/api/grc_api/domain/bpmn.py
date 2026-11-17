"""Names of BPMN elements (for history notes and checks); pure XML parsing."""

from xml.etree.ElementTree import ParseError

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import fromstring

ACTIVITY_TYPES = frozenset(
    {
        "task",
        "userTask",
        "serviceTask",
        "manualTask",
        "scriptTask",
        "businessRuleTask",
        "sendTask",
        "receiveTask",
        "subProcess",
        "callActivity",
    }
)


def element_names(xml: str) -> dict[str, str]:
    try:
        root = fromstring(xml)
    except (ParseError, DefusedXmlException):
        return {}
    out: dict[str, str] = {}
    for el in root.iter():
        id_ = el.get("id")
        if id_ and el.tag.startswith("{http://www.omg.org/spec/BPMN/20100524/MODEL}"):
            out[id_] = el.get("name") or id_
    return out


def is_bpmn(xml: str) -> bool:
    """A parseable BPMN 2.0 document (root element bpmn:definitions), without DTDs or entities."""
    try:
        root = fromstring(xml, forbid_dtd=True)
    except (ParseError, DefusedXmlException):
        return False
    return bool(root.tag == "{http://www.omg.org/spec/BPMN/20100524/MODEL}definitions")
