from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .xml import index_tree, local_name, parse_svg


class PatchError(ValueError):
    pass


@dataclass(frozen=True)
class PatchOperation:
    op: str
    targets: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()
    names: tuple[str, ...] = ()
    parent: str | None = None
    after: str | None = None
    element: str | None = None

    @property
    def attributes_dict(self) -> dict[str, str]:
        return dict(self.attributes)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"op": self.op}
        if self.targets:
            result["targets"] = list(self.targets)
        if self.attributes:
            result["attributes"] = dict(self.attributes)
        if self.names:
            result["names"] = list(self.names)
        if self.parent is not None:
            result["parent"] = self.parent
        if self.after is not None:
            result["after"] = self.after
        if self.element is not None:
            result["element"] = self.element
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PatchOperation":
        if not isinstance(value, dict) or not isinstance(value.get("op"), str):
            raise PatchError("every operation requires a string 'op'")
        allowed_keys = {"op", "targets", "attributes", "names", "parent", "after", "element"}
        unknown_keys = set(value) - allowed_keys
        if unknown_keys:
            raise PatchError(f"unknown operation fields: {sorted(unknown_keys)}")
        targets = value.get("targets", [])
        attributes = value.get("attributes", {})
        names = value.get("names", [])
        if not isinstance(targets, list) or not all(isinstance(item, str) for item in targets):
            raise PatchError("operation targets must be a list of node IDs")
        if not isinstance(attributes, dict) or not all(
            isinstance(key, str)
            and isinstance(item, (str, int, float))
            and not isinstance(item, bool)
            for key, item in attributes.items()
        ):
            raise PatchError("operation attributes must be a scalar-valued object")
        if not isinstance(names, list) or not all(isinstance(item, str) for item in names):
            raise PatchError("operation names must be a list of attribute names")
        return cls(
            op=value["op"],
            targets=tuple(targets),
            attributes=tuple(sorted((key, str(item)) for key, item in attributes.items())),
            names=tuple(names),
            parent=value.get("parent"),
            after=value.get("after"),
            element=value.get("element"),
        )


@dataclass(frozen=True)
class Patch:
    operations: tuple[PatchOperation, ...]
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "operations": [operation.to_dict() for operation in self.operations],
        }

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Patch":
        if not isinstance(value, dict):
            raise PatchError("patch must be a JSON object")
        unknown_keys = set(value) - {"version", "operations"}
        if unknown_keys:
            raise PatchError(f"unknown patch fields: {sorted(unknown_keys)}")
        version = value.get("version", 1)
        if version not in (1, 2):
            raise PatchError(f"unsupported patch version: {version}")
        operations = value.get("operations")
        if not isinstance(operations, list):
            raise PatchError("patch requires an operations list")
        parsed = tuple(PatchOperation.from_dict(item) for item in operations)
        if version == 1:
            for op in parsed:
                if op.op == "remove_element":
                    raise PatchError("remove_element requires patch version 2")
        return cls(parsed, version=version)


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_object(text: str) -> dict[str, Any]:
    candidates = [match.group(1) for match in _JSON_FENCE.finditer(text)]
    candidates.append(text)
    decoder = json.JSONDecoder()
    for candidate in candidates:
        stripped = candidate.strip()
        try:
            value = json.loads(stripped)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
        for index, character in enumerate(candidate):
            if character != "{":
                continue
            try:
                value, _ = decoder.raw_decode(candidate[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
    raise PatchError("model response does not contain a valid JSON object")


def parse_patch(text: str) -> Patch:
    return Patch.from_dict(extract_json_object(text))


def _diff_elements(
    orig_elem: Any,
    ans_elem: Any,
    id_map: dict[int, str],
    set_groups: dict,
    remove_groups: dict,
    remove_elements: list[str],
) -> None:
    """Recursively diff two element trees collecting attribute changes and removals."""
    node_id = id_map[id(orig_elem)]
    orig_attrs = orig_elem.attrib
    ans_attrs = ans_elem.attrib
    changed = tuple(
        sorted(
            (name, value)
            for name, value in ans_attrs.items()
            if orig_attrs.get(name) != value
        )
    )
    removed_attrs = tuple(sorted(name for name in orig_attrs if name not in ans_attrs))
    if changed:
        set_groups.setdefault(changed, []).append(node_id)
    if removed_attrs:
        remove_groups.setdefault(removed_attrs, []).append(node_id)

    orig_children = list(orig_elem)
    ans_children = list(ans_elem)
    ans_used = [False] * len(ans_children)
    for orig_child in orig_children:
        orig_tag = local_name(orig_child.tag)
        matched = None
        for j, ans_child in enumerate(ans_children):
            if ans_used[j]:
                continue
            if local_name(ans_child.tag) == orig_tag:
                ans_used[j] = True
                matched = ans_child
                break
        if matched is None:
            child_id = id_map.get(id(orig_child))
            if child_id:
                remove_elements.append(child_id)
        else:
            _diff_elements(orig_child, matched, id_map, set_groups, remove_groups, remove_elements)


def derive_patch(original_svg: str, answer_svg: str) -> Patch:
    """Derive gold operations by diffing original and answer SVG trees."""
    original_root = parse_svg(original_svg)
    answer_root = parse_svg(answer_svg)
    original_nodes = index_tree(original_root)
    id_map: dict[int, str] = {id(node.element): node.node_id for node in original_nodes}

    set_groups: dict[tuple[tuple[str, str], ...], list[str]] = {}
    remove_groups: dict[tuple[str, ...], list[str]] = {}
    remove_elements: list[str] = []

    _diff_elements(original_root, answer_root, id_map, set_groups, remove_groups, remove_elements)

    operations: list[PatchOperation] = []
    for attributes, targets in set_groups.items():
        operations.append(PatchOperation("set_attributes", tuple(targets), attributes))
    for names, targets in remove_groups.items():
        operations.append(PatchOperation("remove_attributes", tuple(targets), names=names))
    for node_id in remove_elements:
        operations.append(PatchOperation("remove_element", (node_id,)))

    version = 2 if remove_elements else 1
    return Patch(tuple(operations), version=version)
