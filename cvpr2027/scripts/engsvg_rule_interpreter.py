"""Deterministic quantity and edit interpreter for the bounded EngSVG schema.

The language model is not asked to perform unit conversion or arithmetic.  This
module converts quantities to mm, N and MPa, resolves relative edits against the
retained design, and returns a strict create/edit/clarify action.
"""
from __future__ import annotations

import re


FIELDS = (
    "width_mm", "height_mm", "section_b_mm", "section_h_mm", "E_mpa",
    "vertical_load_N", "horizontal_load_N",
)

_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
_NUM = r"(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten)"
_LENGTH_UNIT = r"(?:mm|cm|m)"
_FORCE_UNIT = r"(?:n|kn)"


def _clean(text: str) -> str:
    text = text.lower().replace("×", "x").replace("’", "'")
    replacements = {
        "millimetres": "mm", "millimeters": "mm", "millimetre": "mm",
        "millimeter": "mm", "centimetres": "cm", "centimeters": "cm",
        "centimetre": "cm", "centimeter": "cm", "metres": "m",
        "meters": "m", "metre": "m", "meter": "m",
        "kilonewtons": "kn", "kilonewton": "kn", "newtons": "n",
        "newton": "n", "gigapascals": "gpa", "gigapascal": "gpa",
        "megapascals": "mpa", "megapascal": "mpa",
    }
    for old, new in replacements.items():
        text = re.sub(rf"\b{old}\b", new, text)
    return re.sub(r"\s+", " ", text).strip()


def _number(token: str) -> float:
    return float(_WORDS[token]) if token in _WORDS else float(token)


def _canonical(value: float) -> int | float:
    rounded = round(value)
    return int(rounded) if abs(value - rounded) < 1e-9 else value


def length_mm(value: str, unit: str) -> int | float:
    return _canonical(_number(value) * {"mm": 1, "cm": 10, "m": 1000}[unit])


def force_N(value: str, unit: str) -> int | float:
    return _canonical(_number(value) * {"n": 1, "kn": 1000}[unit])


def modulus_mpa(value: str, unit: str) -> int | float:
    return _canonical(_number(value) * {"mpa": 1, "gpa": 1000}[unit])


def _length_match(text: str, patterns: list[str]):
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return length_mm(match.group("v"), match.group("u"))
    return None


def _extract_section(text: str) -> dict:
    result = {}
    pair_patterns = [
        rf"(?:section(?:\s+is|\s+to)?|section\s+of|uses?\s+(?:a\s+)?)\s*"
        rf"(?P<a>{_NUM})\s*(?P<ua>{_LENGTH_UNIT})?\s*(?:x|by)\s*"
        rf"(?P<b>{_NUM})\s*(?P<ub>{_LENGTH_UNIT})(?:\s+(?:rectangular\s+)?section)?",
        rf"(?P<a>{_NUM})\s*(?P<ua>{_LENGTH_UNIT})?\s*(?:x|by)\s*"
        rf"(?P<b>{_NUM})\s*(?P<ub>{_LENGTH_UNIT})\s+(?:member\s+)?section",
        rf"(?:change\s+)?(?:the\s+)?section\s+to\s+"
        rf"(?P<a>{_NUM})\s*(?P<ua>{_LENGTH_UNIT})\s+breadth\s+by\s+"
        rf"(?P<b>{_NUM})\s*(?P<ub>{_LENGTH_UNIT})\s+depth",
    ]
    for pattern in pair_patterns:
        match = re.search(pattern, text)
        if match:
            ua = match.group("ua") or match.group("ub")
            result["section_b_mm"] = length_mm(match.group("a"), ua)
            result["section_h_mm"] = length_mm(match.group("b"), match.group("ub"))
            return result
    breadth = _length_match(text, [
        rf"(?:member\s+)?breadth\s*(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})",
        rf"(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})\s+(?:member\s+)?breadth",
    ])
    depth = _length_match(text, [
        rf"(?:member\s+)?depth\s*(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})",
        rf"(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})\s+(?:member\s+)?depth",
    ])
    if breadth is not None:
        result["section_b_mm"] = breadth
    if depth is not None:
        result["section_h_mm"] = depth
    return result


def extract_create_parameters(request: str) -> dict:
    """Extract explicitly supplied canonical values without inventing defaults."""
    text = _clean(request)
    result = {}

    geometry_pair = re.search(
        rf"(?P<w>{_NUM})\s*(?P<uw>{_LENGTH_UNIT})\s+by\s+"
        rf"(?P<h>{_NUM})\s*(?P<uh>{_LENGTH_UNIT})\s+(?:table\s+side\s+)?frame",
        text,
    )
    if geometry_pair:
        result["width_mm"] = length_mm(geometry_pair.group("w"), geometry_pair.group("uw"))
        result["height_mm"] = length_mm(geometry_pair.group("h"), geometry_pair.group("uh"))

    width = _length_match(text, [
        rf"(?:span|width)\s*(?:to|of|is|=)?\s*(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})",
        rf"(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})\s+(?:wide|width|across|span)",
        rf"(?:widen|set\s+the\s+span)\s+(?:it\s+)?(?:to\s+)?(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})",
    ])
    height = _length_match(text, [
        rf"(?:rise|height)\s*(?:to|of|is|=)?\s*(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})",
        rf"(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})\s+(?:tall|high|height)",
    ])
    if width is not None:
        result["width_mm"] = width
    if height is not None:
        result["height_mm"] = height
    result.update(_extract_section(text))

    modulus = re.search(rf"(?P<v>{_NUM})\s*(?P<u>gpa|mpa)", text)
    if modulus:
        result["E_mpa"] = modulus_mpa(modulus.group("v"), modulus.group("u"))

    quantity = re.compile(rf"(?P<v>{_NUM})\s*(?P<u>{_FORCE_UNIT})\b(?P<tail>(?:\s+[a-z]+){{0,4}})")
    for match in quantity.finditer(text):
        tail = match.group("tail")
        value = force_N(match.group("v"), match.group("u"))
        if re.search(r"\b(down|downward|vertically|vertical)\b", tail):
            result["vertical_load_N"] = value
        if re.search(r"\b(right|rightward|horizontally|horizontal|lateral|sideways)\b", tail):
            result["horizontal_load_N"] = value
    if re.search(r"\b(?:no|zero)\s+(?:sideways|lateral|horizontal)(?:\s+force|\s+load)?\b", text):
        result["horizontal_load_N"] = 0
    return result


def _add(changes: dict, field: str, value):
    changes[field] = _canonical(value)


def extract_edit_changes(request: str, source: dict) -> dict:
    """Resolve explicit and relative changes against an existing design."""
    text = _clean(request)
    changes = {}

    # Explicit section and material edits.
    changes.update(_extract_section(text))
    modulus = re.search(rf"(?P<v>{_NUM})\s*(?P<u>gpa|mpa)", text)
    if modulus and re.search(r"\b(?:modulus|stiffness|material|e\s*=)\b", text):
        changes["E_mpa"] = modulus_mpa(modulus.group("v"), modulus.group("u"))

    # Explicit geometry values.
    if re.search(r"\b(?:set|make|change)\b", text):
        supplied = extract_create_parameters(text)
        for field in ("width_mm", "height_mm"):
            if field in supplied:
                changes[field] = supplied[field]

    match = re.search(rf"(?:widen(?:\s+it)?\s+by|increase\s+the\s+span\s+by)\s*"
                      rf"(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})|"
                      rf"make\s+it\s+(?P<v2>{_NUM})\s*(?P<u2>{_LENGTH_UNIT})\s+wider", text)
    if match:
        value, unit = (match.group("v"), match.group("u")) if match.group("v") else (match.group("v2"), match.group("u2"))
        _add(changes, "width_mm", source["width_mm"] + length_mm(value, unit))
    match = re.search(rf"(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})\s+shorter", text)
    if match:
        _add(changes, "height_mm", source["height_mm"] - length_mm(match.group("v"), match.group("u")))
    match = re.search(rf"(?:section\s+)?depth\s*(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})\s+larger", text)
    if match:
        _add(changes, "section_h_mm", source["section_h_mm"] + length_mm(match.group("v"), match.group("u")))

    percent_patterns = [
        ("height_mm", r"(?:height)"),
        ("vertical_load_N", r"(?:downward|vertical)(?:\s+(?:force|load))?"),
        ("horizontal_load_N", r"(?:horizontal|lateral)(?:\s+(?:force|load))?"),
    ]
    for field, grouped in percent_patterns:
        match = re.search(rf"increase\s+(?:the\s+)?{grouped}\s+by\s+"
                          rf"(?P<p>{_NUM})\s*percent", text)
        if match:
            _add(changes, field, source[field] * (1 + _number(match.group("p")) / 100))
    taller = re.search(rf"(?P<p>{_NUM})\s*percent\s+taller", text)
    if taller:
        _add(changes, "height_mm", source["height_mm"] * (1 + _number(taller.group("p")) / 100))

    directions = {
        "vertical_load_N": r"downward|vertical",
        "horizontal_load_N": r"horizontal|lateral|sideways",
    }
    for field, direction in directions.items():
        if re.search(rf"double\s+(?:only\s+)?(?:the\s+)?(?:{direction})(?:\s+force|\s+load)?", text):
            _add(changes, field, source[field] * 2)
        if re.search(rf"remove\s+(?:the\s+)?(?:{direction})(?:\s+force|\s+load)?", text):
            changes[field] = 0
        if re.search(rf"reduce\s+(?:the\s+)?(?:{direction})(?:\s+force|\s+load)?\s+by\s+(?:one\s+)?quarter", text):
            _add(changes, field, source[field] * 0.75)

    delta_pattern = re.compile(
        rf"(?P<op>add|increase|reduce|decrease)\s+(?P<v>{_NUM})\s*(?P<u>{_FORCE_UNIT})"
        rf"(?:\s+(?:to|from))?\s+(?:the\s+)?(?P<direction>lateral|horizontal|sideways|downward|vertical)"
    )
    for match in delta_pattern.finditer(text):
        field = "horizontal_load_N" if match.group("direction") in {"lateral", "horizontal", "sideways"} else "vertical_load_N"
        sign = 1 if match.group("op") in {"add", "increase"} else -1
        _add(changes, field, source[field] + sign * force_N(match.group("v"), match.group("u")))

    reverse_delta = re.compile(
        rf"(?P<op>increase|reduce|decrease)\s+(?:the\s+)?"
        rf"(?P<direction>lateral|horizontal|sideways|downward|vertical)(?:\s+force|\s+load)?\s+by\s+"
        rf"(?P<v>{_NUM})\s*(?P<u>{_FORCE_UNIT})"
    )
    for match in reverse_delta.finditer(text):
        field = "horizontal_load_N" if match.group("direction") in {"lateral", "horizontal", "sideways"} else "vertical_load_N"
        sign = 1 if match.group("op") == "increase" else -1
        _add(changes, field, source[field] + sign * force_N(match.group("v"), match.group("u")))

    depth_delta = re.search(
        rf"add\s+(?P<v>{_NUM})\s*(?P<u>{_LENGTH_UNIT})\s+to\s+(?:the\s+)?(?:section\s+)?depth",
        text,
    )
    if depth_delta:
        _add(changes, "section_h_mm", source["section_h_mm"] + length_mm(depth_delta.group("v"), depth_delta.group("u")))

    return changes


def interpret(request: str, source: dict | None = None) -> dict:
    """Return a strict schema action using deterministic conversion and arithmetic."""
    if source is None:
        parameters = extract_create_parameters(request)
        missing = [field for field in FIELDS if field not in parameters]
        if missing:
            return {"action": "clarify", "missing": missing}
        return {"action": "create", "parameters": parameters}
    changes = extract_edit_changes(request, source)
    if not changes:
        raise ValueError("no supported edit found")
    return {"action": "edit", "changes": changes}


def change_summary(source: dict | None, action: dict) -> list[str]:
    """Produce a compact, visible audit trail for a proposed action."""
    if action["action"] == "clarify":
        return ["Missing: " + ", ".join(action["missing"])]
    values = action["parameters"] if action["action"] == "create" else action["changes"]
    lines = []
    for field, value in values.items():
        if source is None or field not in source:
            lines.append(f"{field} = {value}")
        else:
            lines.append(f"{field}: {source[field]} -> {value}")
    return lines
