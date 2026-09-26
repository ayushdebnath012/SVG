from __future__ import annotations

from dataclasses import dataclass
import re
import xml.etree.ElementTree as ET

from .patch import Patch, PatchError
from .xml import local_name


@dataclass(frozen=True)
class PatchPolicy:
    allowed_operations: frozenset[str] = frozenset(
        {"set_attributes", "remove_attributes", "insert_primitive", "remove_element", "set_text",
         "insert_subtree", "replace_geometry"}
    )
    allowed_attributes: frozenset[str] = frozenset(
        {
            "fill",
            "stroke",
            "stroke-width",
            "opacity",
            "transform",
            "viewBox",
            "x",
            "y",
            "x1",
            "y1",
            "x2",
            "y2",
            "width",
            "height",
            "cx",
            "cy",
            "r",
            "rx",
            "ry",
        }
    )
    allowed_elements: frozenset[str] = frozenset(
        {"line", "rect", "circle", "ellipse"}
    )
    protected_attributes: frozenset[str] = frozenset({"d", "points"})
    max_operations: int = 16
    max_targets: int = 128
    max_text_characters: int = 2_000
    max_subtree_bytes: int = 200_000
    max_subtree_nodes: int = 2_000


TASK_ALLOWED_ATTRIBUTES = {
    "change_color": frozenset({"fill"}),
    "set_contour": frozenset({"stroke", "stroke-width"}),
    "compression": frozenset(),
    "upside_down": frozenset({"transform"}),
    "transparency": frozenset({"opacity"}),
    "crop_to_half": frozenset({"viewBox"}),
    # Plan B
    "rotate": frozenset({"transform"}),
    "flip": frozenset({"transform"}),
    "delete": frozenset(),
}

ROOT_ONLY_TASKS = {"upside_down", "transparency", "crop_to_half"}
DELETE_TASKS = {"delete"}
BENCHMARK_TASKS = set(TASK_ALLOWED_ATTRIBUTES)

SAFE_SUBTREE_ELEMENTS = {
    "g", "line", "rect", "circle", "ellipse", "path", "polyline", "polygon", "text", "tspan",
    "title", "desc", "defs", "marker", "pattern", "linearGradient", "radialGradient", "stop",
    "clipPath",
}
REFERENCE_ATTRIBUTES = {"href", "{http://www.w3.org/1999/xlink}href"}

GENERIC_SVG_ATTRIBUTES = frozenset(
    {
        # Identity hooks are deliberately omitted: rewriting an existing XML id
        # can silently invalidate references elsewhere in the document.
        "class",
        "fill", "fill-opacity", "fill-rule",
        "stroke", "stroke-opacity", "stroke-width", "stroke-linecap", "stroke-linejoin",
        "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset",
        "opacity", "visibility", "display", "vector-effect", "transform",
        "viewBox", "preserveAspectRatio",
        "x", "y", "x1", "y1", "x2", "y2", "dx", "dy",
        "width", "height", "cx", "cy", "r", "rx", "ry",
        "font-family", "font-size", "font-style", "font-weight",
        "text-anchor", "dominant-baseline", "baseline-shift", "letter-spacing",
        "word-spacing", "textLength", "lengthAdjust", "rotate",
        "marker-start", "marker-mid", "marker-end", "clip-path", "mask", "filter",
        "href", "{http://www.w3.org/1999/xlink}href",
    }
)


def generic_svg_policy(max_operations: int = 2_000) -> PatchPolicy:
    """Opt-in policy for ordinary, non-active engineering SVG presentation attributes."""
    return PatchPolicy(allowed_attributes=GENERIC_SVG_ATTRIBUTES, max_operations=max_operations)


def _validate_attribute_value(name: str, value: str) -> None:
    lowered = value.lower().replace(" ", "")
    if any(token in lowered for token in ("javascript:", "data:", "<", ">")):
        raise PatchError(f"unsafe value for {name}")
    if local_name(name).lower() == "href" and value and not value.startswith("#"):
        raise PatchError(f"external reference is not allowed for {name}")
    for reference in re.findall(r"url\((.*?)\)", value, re.I):
        if not reference.strip(" \"'").startswith("#"):
            raise PatchError(f"external URL reference is not allowed for {name}")


def _validate_subtree(value: str, policy: PatchPolicy) -> None:
    if len(value.encode("utf-8")) > policy.max_subtree_bytes:
        raise PatchError("inserted subtree exceeds size limit")
    upper = value.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise PatchError("inserted subtree contains a forbidden declaration")
    try:
        root = ET.fromstring(value)
    except ET.ParseError as exc:
        raise PatchError(f"inserted subtree is not valid XML: {exc}") from exc
    nodes = list(root.iter())
    if len(nodes) > policy.max_subtree_nodes:
        raise PatchError("inserted subtree exceeds node limit")
    for element in nodes:
        if local_name(element.tag) not in SAFE_SUBTREE_ELEMENTS:
            raise PatchError(f"inserted element is not allowed: {local_name(element.tag)}")
        for name, item in element.attrib.items():
            lname = local_name(name).lower()
            lowered = item.lower().replace(" ", "")
            if lname.startswith("on") or "javascript:" in lowered or "data:" in lowered:
                raise PatchError(f"unsafe inserted attribute: {lname}")
            if name in REFERENCE_ATTRIBUTES and item and not item.startswith("#"):
                raise PatchError("inserted references must remain inside the SVG document")
            for reference in re.findall(r"url\((.*?)\)", item, re.I):
                if not reference.strip(" \"'").startswith("#"):
                    raise PatchError("inserted URL references must remain inside the SVG document")


def validate_patch(
    patch: Patch,
    scene: dict,
    policy: PatchPolicy | None = None,
    task: str | None = None,
) -> None:
    policy = policy or PatchPolicy()
    if len(patch.operations) > policy.max_operations:
        raise PatchError("patch exceeds operation limit")
    node_ids = {node["id"] for node in scene["nodes"]}
    task_attributes = TASK_ALLOWED_ATTRIBUTES.get(task) if task else None

    for operation in patch.operations:
        if patch.version == 1 and operation.op in {"remove_element", "set_text"}:
            raise PatchError(f"{operation.op} requires patch version 2")
        if patch.version < 3 and operation.op in {"insert_subtree", "replace_geometry"}:
            raise PatchError(f"{operation.op} requires patch version 3")
        if operation.op not in policy.allowed_operations:
            raise PatchError(f"operation is not allowed: {operation.op}")
        if task in BENCHMARK_TASKS:
            if task in DELETE_TASKS and operation.op != "remove_element":
                raise PatchError(f"{task} only permits remove_element operations")
            elif task not in DELETE_TASKS and operation.op != "set_attributes":
                raise PatchError(f"{task} only permits set_attributes operations")
        if len(operation.targets) > policy.max_targets:
            raise PatchError("operation exceeds target limit")
        unknown = sorted(set(operation.targets) - node_ids)
        if unknown:
            raise PatchError(f"unknown target IDs: {', '.join(unknown)}")

        if operation.op == "remove_element":
            root_id = scene["root_id"]
            for target in operation.targets:
                if target == root_id:
                    raise PatchError("cannot remove the root element")
            continue

        if operation.op == "set_text":
            if not operation.targets:
                raise PatchError("set_text requires at least one target")
            if operation.text is None:
                raise PatchError("set_text requires text")
            if len(operation.text) > policy.max_text_characters:
                raise PatchError("set_text exceeds text length limit")
            tags = {node["id"]: node["tag"] for node in scene["nodes"]}
            invalid = [target for target in operation.targets
                       if tags[target] not in {"text", "tspan", "title", "desc"}]
            if invalid:
                raise PatchError(f"set_text targets non-text nodes: {', '.join(invalid)}")
            continue

        if operation.op == "insert_subtree":
            if operation.parent not in node_ids:
                raise PatchError("insert_subtree requires a valid parent")
            if operation.index is None or isinstance(operation.index, bool) or operation.index < 0:
                raise PatchError("insert_subtree requires an insertion index")
            if operation.subtree is None:
                raise PatchError("insert_subtree requires subtree XML")
            _validate_subtree(operation.subtree, policy)
            continue

        if operation.op == "replace_geometry":
            names = set(operation.attributes_dict) | set(operation.names)
            if not operation.targets or not names or not names <= {"d", "points"}:
                raise PatchError("replace_geometry only permits d or points attributes")
            for _, value in operation.attributes:
                lowered = value.lower().replace(" ", "")
                if any(token in lowered for token in ("javascript:", "url(", "data:", "<", ">")):
                    raise PatchError("unsafe geometry value")
            continue

        names = set(operation.attributes_dict) | set(operation.names)
        forbidden = names & policy.protected_attributes
        if forbidden:
            raise PatchError(f"protected attributes cannot be changed: {sorted(forbidden)}")
        disallowed = names - policy.allowed_attributes
        if disallowed:
            raise PatchError(f"attributes are not allowlisted: {sorted(disallowed)}")
        if task_attributes is not None and names - task_attributes:
            raise PatchError(f"attributes are invalid for {task}: {sorted(names - task_attributes)}")
        for name, value in operation.attributes:
            _validate_attribute_value(name, value)
        if task in ROOT_ONLY_TASKS and set(operation.targets) != {scene["root_id"]}:
            raise PatchError(f"{task} may only target the SVG root")

        if operation.op == "set_attributes" and not operation.attributes:
            raise PatchError("set_attributes requires attributes")
        if operation.op == "remove_attributes" and not operation.names:
            raise PatchError("remove_attributes requires names")
        if operation.op == "insert_primitive":
            if operation.element not in policy.allowed_elements:
                raise PatchError(f"element is not allowlisted: {operation.element}")
            if operation.parent not in node_ids:
                raise PatchError("insert_primitive requires a valid parent")
            if operation.after is not None and operation.after not in node_ids:
                raise PatchError("insert_primitive references an unknown sibling")
