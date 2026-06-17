#!/usr/bin/env python3
"""Kaggle T4 pipeline for a locality-preserving SVG patch editor.

Architecture (SVG-Patch spec §1–§5):

    input SVG + instruction → patch (flat JSON op array) → byte-span applier → output SVG

Core invariants
---------------
1. Preservation by construction: bytes of untouched elements are NEVER re-serialized.
   The applier performs byte-level span splicing on the original byte string.
2. The model emits a patch (flat JSON array of ops). The deterministic applier is the
   only component that writes to the document.
3. Fail-closed: any invalid patch (bad eid, malformed SVG, schema violation) returns
   the original document unchanged.

Patch op taxonomy (§2.1)
-------------------------
set     – set / add attribute(s) on an element
unset   – remove attribute(s) from an element
replace – replace entire element (incl. children) with new markup
delete  – delete element and its subtree
insert  – insert new markup relative to an anchor (before/after/first-child/last-child)
move    – relocate an element (z-order / reparenting), bytes copied verbatim
text    – replace text content of a text/tspan node

EID scheme (§1.2, 3-tier)
--------------------------
Tier 1  #author-id           if element has an id= attribute
Tier 2  tag:path             structural path, e.g. rect:0.3.2
Tier 3  tag:path@xxxx        4-hex hash appended on collision

Preservation theorem (§2.2)
----------------------------
For any element e ∉ T(P) whose span does not contain a targeted span, the byte range
of e in the output is identical to its byte range in the input, up to a uniform offset.
Proof: the applier's only mutation primitive is splicing at spans derived from T(P);
disjoint element spans are copied verbatim. ∎

Pipeline stages
---------------
00_source_svgs  build / import / deduplicate / fingerprint SVGs
01_tasks        split sources, synthesize grounded edit tasks
02_sft          build annotated-view → patch-JSON SFT rows
03_baselines    noop / instruction-copy / oracle / drifted-global
04_model        QLoRA train (Qwen2.5-Coder-1.5B, 4-bit) + batched inference
05_reports      EP-score, edit metrics, comparison table, download zips

Kaggle quick start (SVGEditBench by default; auto-clones repo if needed):
    python kaggle_patchsvg_t4_smoke.py --install-deps \\
        --n-train 512 --n-val 64 --n-eval 128

SVGEditBench training set from a paper PDF / explicit repo path:
    python kaggle_patchsvg_t4_smoke.py --install-deps \\
        --svg-editbench "/kaggle/input/2404.13710v1.pdf" \\
        --n-train 420 --n-val 60 --n-eval 120 --max-seq-length 2048

Colab one-script run (upload only this .py file, no notebook needed):
    python kaggle_patchsvg_t4_smoke.py --colab \\
        --n-train 420 --n-val 60 --n-eval 120 --max-seq-length 2048
    Trainer checkpoints are saved under 04_model/trainer/checkpoint-* every
    --save-steps optimizer steps, all are kept by default, and reruns auto-resume.
    On Colab/Kaggle the T4 memory saver enables reentrant gradient
    checkpointing and caps default long contexts to 2048 tokens. Pass
    --no-gradient-checkpointing to disable recomputation; in that mode the
    memory saver uses a shorter 1536-token cap to avoid T4 backward-pass OOM.

Colab + Google Drive persistent checkpoints:
    python kaggle_patchsvg_t4_smoke.py --colab --gdrive \\
        --n-train 420 --n-val 60 --n-eval 120 --max-seq-length 2048
    Checkpoints persist under:
        /content/drive/MyDrive/patchsvg_svgeditbench/04_model/trainer/checkpoint-*
    Rerunning the same command auto-resumes from the latest Drive checkpoint.

Apply a trained patch editor to one SVG:
    python kaggle_patchsvg_t4_smoke.py --reuse-checkpoint \\
        --edit-svg input.svg --edit-instruction "Make the sun red." \\
        --edit-output-svg edited.svg

Local synthetic smoke (no GPU / no model; explicit debug fallback):
    python kaggle_patchsvg_t4_smoke.py --synthetic-smoke --skip-train \\
        --n-source 24 --n-train 32 --n-val 8 --n-eval 8

TODO (beyond this smoke test):
  - Grammar-constrained decoding via outlines/xgrammar with dynamic eid trie (§2.3)
  - VLM image input (Qwen2-VL) for visual grounding (§1.2)
  - Full element matcher: geometry + render-feature stages for VectorEdits (§3.3–3.4)
"""

from __future__ import annotations

# ── GPU environment — must come before any torch / CUDA import ────────────────
# Kaggle T4x2 kernels expose 2 GPUs. The HuggingFace Trainer wraps in
# DataParallel when torch.cuda.device_count() > 1, which is incompatible with
# bitsandbytes 4-bit LoRA (cudaErrorIllegalAddress / CUBLAS_STATUS_EXECUTION_FAILED).
# Restricting to GPU 0 here ensures the Trainer always sees exactly one device.
# Use a hard assignment (not setdefault) so we override any Kaggle pre-set value.
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")

import argparse
import contextlib
import gc
import glob
import hashlib
import importlib.metadata
import inspect
import json
import math
import random
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
SVGEDITBENCH_REPO_URL = "https://github.com/mti-lab/SVGEditBench.git"
DEFAULT_GDRIVE_OUTPUT_DIR = Path("/content/drive/MyDrive/patchsvg_svgeditbench")
TRAINER_FINGERPRINT_FILE = "patchsvg_run_fingerprint.json"
T4_CHECKPOINTING_SEQ_LENGTH = 2048
T4_NO_CHECKPOINTING_SEQ_LENGTH = 1536
PROMPT_FORMAT_VERSION = 2
PROMPT_VIEW_FULL_CHAR_LIMIT = 6000
PROMPT_ATTR_VALUE_LIMIT = 96

PALETTE = [
    "#ef4444", "#f59e0b", "#10b981", "#2563eb", "#7c3aed",
    "#ec4899", "#111827", "#f8fafc", "#06b6d4", "#84cc16",
]
COLOR_NAMES = {
    "#ef4444": "red",   "#f59e0b": "amber",  "#10b981": "emerald",
    "#2563eb": "blue",  "#7c3aed": "violet",  "#ec4899": "pink",
    "#111827": "charcoal", "#f8fafc": "off-white",
    "#06b6d4": "cyan",  "#84cc16": "lime",
}
SYNTHETIC_TEMPLATE_COUNT = 8
ALLOWED_SET_ATTRS = {
    "fill", "stroke", "opacity", "fill-opacity", "stroke-opacity",
    "stroke-width", "x", "y", "cx", "cy", "r", "rx", "ry", "width", "height",
    "viewBox", "transform",
}
VALID_OPS = {"set", "unset", "replace", "delete", "insert", "move", "text"}
VALID_WHERE = {"before", "after", "first-child", "last-child"}
DEFAULT_TASK_TYPES = ("color", "opacity", "stroke_width", "geometry", "multi_style")
EDITABLE_TAGS = {
    "svg", "g", "path", "rect", "circle", "ellipse", "line",
    "polyline", "polygon", "text", "use",
}
PROMPT_SUMMARY_ATTRS = (
    "id", "aria-label", "data-label", "inkscape:label", "class",
    "fill", "stroke", "stroke-width", "opacity", "fill-opacity",
    "stroke-opacity", "x", "y", "x1", "y1", "x2", "y2",
    "cx", "cy", "r", "rx", "ry", "width", "height", "viewBox",
    "transform", "style",
)
SVGEDITBENCH_TASK_DIRS = {
    "1_ChangeColor": "change_color",
    "2_SetContour": "set_contour",
    "3_Compression": "compression",
    "4_UpSideDown": "upside_down",
    "5_Transparency": "transparency",
    "6_CropToHalf": "crop_to_half",
}

# ── ElementRecord (§1.1) ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ElementRecord:
    """Position-preserving record for a single SVG element (§1.1)."""
    eid: str
    tag: str
    attrs: dict[str, str]
    span: tuple[int, int]               # byte span of full element (open → end of close tag)
    open_span: tuple[int, int]          # byte span of opening tag only
    close_span: tuple[int, int] | None  # byte span of </tag>; None for self-closing
    attr_spans: dict[str, tuple[int, int]]  # each attr's byte span within the document
    parent_eid: str | None
    index: int                          # child index within parent
    depth: int
    path: str                           # structural path, e.g. "0.3.2"
    is_self_closing: bool


@dataclass
class _StackFrame:
    """Mutable parser stack entry for tracking open (non-self-closing) elements."""
    tag: str
    open_start: int
    open_end: int
    parent_eid: str | None
    depth: int
    path: str
    child_count: int                    # editable children seen so far
    eid: str
    attrs: dict[str, str]
    attr_spans: dict[str, tuple[int, int]]
    index: int                          # this element's own child index within its parent


# ── Byte-span parser (§1.1) ───────────────────────────────────────────────────

_TAG_NAME_RE = re.compile(rb"</?([A-Za-z_:][\w:.-]*)")
_ATTR_BYTES_RE = re.compile(
    rb"""([A-Za-z_:][\w:.-]*)\s*=\s*("([^"]*)"|'([^']*)')""",
    re.DOTALL,
)


def _find_open_tag_end(data: bytes, start: int) -> int:
    """Return the byte index AFTER the closing > or /> of the opening tag at start."""
    i = start + 1
    n = len(data)
    in_quote: int | None = None
    while i < n:
        c = data[i]
        if in_quote is not None:
            if c == in_quote:
                in_quote = None
        elif c == ord('"'):
            in_quote = ord('"')
        elif c == ord("'"):
            in_quote = ord("'")
        elif c == ord('>'):
            return i + 1
        i += 1
    return n


def _parse_attrs(tag_bytes: bytes, tag_doc_start: int) -> tuple[dict[str, str], dict[str, tuple[int, int]]]:
    """Return (attrs_dict, attr_spans) where spans are in document bytes."""
    attrs: dict[str, str] = {}
    attr_spans: dict[str, tuple[int, int]] = {}
    for m in _ATTR_BYTES_RE.finditer(tag_bytes):
        name = m.group(1).decode("utf-8", errors="replace")
        raw = m.group(3) if m.group(3) is not None else m.group(4)
        attrs[name] = (raw or b"").decode("utf-8", errors="replace")
        attr_spans[name] = (tag_doc_start + m.start(), tag_doc_start + m.end())
    return attrs, attr_spans


def _build_records(data: bytes) -> list[ElementRecord]:
    """Parse SVG bytes into a list of ElementRecords (document order, §1.1)."""
    records: list[ElementRecord] = []
    stack: list[_StackFrame] = []
    used_eids: set[str] = set()
    root_child_count = 0

    i = 0
    n = len(data)

    while i < n:
        if data[i:i + 1] != b"<":
            i += 1
            continue

        # Skip comments
        if data[i:i + 4] == b"<!--":
            end = data.find(b"-->", i + 4)
            i = end + 3 if end != -1 else n
            continue
        # Skip processing instructions
        if data[i:i + 2] == b"<?":
            end = data.find(b"?>", i + 2)
            i = end + 2 if end != -1 else n
            continue
        # Skip DOCTYPE / CDATA / other declarations
        if data[i:i + 2] == b"<!" or data[i:i + 9] == b"<![CDATA[":
            end = data.find(b">", i)
            i = end + 1 if end != -1 else n
            continue

        # End tag — ALWAYS consume the full </tag> token before doing anything else.
        # Without this guard, unrecognised end tags fall through to the start-tag
        # branch and get mis-parsed as opening tags (the ^ anchor in _TAG_NAME_RE
        # only anchors to byte 0 of `data`, not to the `pos` argument of match()).
        if data[i:i + 2] == b"</":
            close_end = data.find(b">", i)
            if close_end == -1:
                i += 1
                continue
            close_end += 1
            m = _TAG_NAME_RE.match(data, i)   # works without ^ for any pos
            if m:
                close_name = m.group(1).decode("utf-8", errors="replace").split(":")[-1].lower()
                # Pop the matching open frame (handle mismatched tags gracefully)
                if stack and stack[-1].tag == close_name:
                    frame = stack.pop()
                    full_span = (frame.open_start, close_end)
                    close_span = (i, close_end)
                    rec = ElementRecord(
                        eid=frame.eid,
                        tag=frame.tag,
                        attrs=frame.attrs,
                        span=full_span,
                        open_span=(frame.open_start, frame.open_end),
                        close_span=close_span,
                        attr_spans=frame.attr_spans,
                        parent_eid=frame.parent_eid,
                        index=frame.index,
                        depth=frame.depth,
                        path=frame.path,
                        is_self_closing=False,
                    )
                    records.append(rec)
            i = close_end   # always skip past this end tag
            continue        # always continue — never fall through to start-tag branch

        # Start or self-closing tag
        open_end = _find_open_tag_end(data, i)
        tag_bytes = data[i:open_end]
        m = _TAG_NAME_RE.match(tag_bytes)
        if not m:
            i += 1
            continue

        tag_name = m.group(1).decode("utf-8", errors="replace").split(":")[-1].lower()
        is_self_closing = tag_bytes.rstrip().endswith(b"/>")
        attrs, attr_spans = _parse_attrs(tag_bytes, i)

        # Determine parent, path, index
        if stack:
            frame_parent = stack[-1]
            parent_eid = frame_parent.eid
            child_idx = frame_parent.child_count
            frame_parent.child_count += 1
            path = f"{frame_parent.path}.{child_idx}"
        else:
            parent_eid = None
            child_idx = root_child_count
            root_child_count += 1
            path = str(child_idx)

        depth = len(stack)

        # 3-tier EID assignment (§1.2)
        if "id" in attrs:
            candidate = f"#{attrs['id']}"
        else:
            candidate = f"{tag_name}:{path}"

        if candidate in used_eids:
            sig = f"{tag_name}:{path}:{sorted(attrs.items())}".encode()
            candidate = f"{candidate}@{hashlib.sha1(sig).hexdigest()[:4]}"
        used_eids.add(candidate)
        eid = candidate

        if is_self_closing:
            rec = ElementRecord(
                eid=eid,
                tag=tag_name,
                attrs=attrs,
                span=(i, open_end),
                open_span=(i, open_end),
                close_span=None,
                attr_spans=attr_spans,
                parent_eid=parent_eid,
                index=child_idx,
                depth=depth,
                path=path,
                is_self_closing=True,
            )
            records.append(rec)
            i = open_end
        else:
            stack.append(_StackFrame(
                tag=tag_name,
                open_start=i,
                open_end=open_end,
                parent_eid=parent_eid,
                depth=depth,
                path=path,
                child_count=0,
                eid=eid,
                attrs=attrs,
                attr_spans=attr_spans,
                index=child_idx,
            ))
            i = open_end

    # Handle unclosed tags as self-closing for robustness
    for frame in reversed(stack):
        rec = ElementRecord(
            eid=frame.eid,
            tag=frame.tag,
            attrs=frame.attrs,
            span=(frame.open_start, frame.open_end),
            open_span=(frame.open_start, frame.open_end),
            close_span=None,
            attr_spans=frame.attr_spans,
            parent_eid=frame.parent_eid,
            index=frame.index,
            depth=frame.depth,
            path=frame.path,
            is_self_closing=True,
        )
        records.append(rec)

    records.sort(key=lambda r: r.open_span[0])
    return records


def parse_svg(source: str) -> tuple[bytes, dict[str, ElementRecord]]:
    """Parse SVG string into (bytes, eid→ElementRecord map).

    The returned bytes are the canonical encoding used for all splice operations.
    All byte spans in ElementRecord are offsets into this byte string.
    """
    data = source.encode("utf-8")
    records = _build_records(data)
    return data, {r.eid: r for r in records}


# ── Annotated view (§1.2) ────────────────────────────────────────────────────

def annotated_view(source: str, records: dict[str, ElementRecord]) -> str:
    """Return the SVG with [eid] comment markers prepended to each element.

    The annotated view is shown to the model so it can ground semantic
    references ('the sun in the corner') to concrete eids.
    """
    data = source.encode("utf-8")
    ordered = sorted(records.values(), key=lambda r: r.open_span[0])
    # Build splice: prepend b'[eid] ' before each element's open tag
    splices: list[tuple[int, int, bytes]] = []
    for rec in ordered:
        if rec.tag not in EDITABLE_TAGS:
            continue
        marker = f"[{rec.eid}] ".encode("utf-8")
        splices.append((rec.open_span[0], rec.open_span[0], marker))
    result = _apply_splices(data, splices)
    return result.decode("utf-8")


def eid_vocabulary(records: dict[str, ElementRecord]) -> str:
    """Return a compact list of valid eids for the model prompt (§2.3 trie approximation)."""
    eids = sorted(
        r.eid for r in records.values() if r.tag in EDITABLE_TAGS
    )
    return ", ".join(eids)


# ── Opening-tag byte manipulation helpers ────────────────────────────────────

def _escape_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
             .replace('"', "&quot;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
    )


def _set_one_attr(tag_bytes: bytes, name: str, value: str) -> bytes:
    """Set or add a single attribute in opening-tag bytes."""
    escaped = _escape_attr(value).encode("utf-8")
    name_b = name.encode("utf-8")
    pattern = re.compile(
        rb"(" + re.escape(name_b) + rb"\s*=\s*)" + rb"""("([^"]*)"|'([^']*)')""",
        re.DOTALL,
    )
    if pattern.search(tag_bytes):
        return pattern.sub(rb"\1" + b'"' + escaped + b'"', tag_bytes, count=1)
    insert_at = (
        tag_bytes.rfind(b"/") if tag_bytes.rstrip().endswith(b"/>")
        else tag_bytes.rfind(b">")
    )
    return tag_bytes[:insert_at] + b' ' + name_b + b'="' + escaped + b'"' + tag_bytes[insert_at:]


def _unset_one_attr(tag_bytes: bytes, name: str) -> bytes:
    """Remove a single attribute (and its leading whitespace) from opening-tag bytes."""
    name_b = name.encode("utf-8")
    pattern = re.compile(
        rb"\s+" + re.escape(name_b) + rb"""\s*=\s*("([^"]*)"|'([^']*)')""",
        re.DOTALL,
    )
    return pattern.sub(b"", tag_bytes, count=1)


def _set_attrs_on_tag(tag_bytes: bytes, attrs: dict[str, str]) -> bytes:
    for name, value in attrs.items():
        tag_bytes = _set_one_attr(tag_bytes, name, value)
    return tag_bytes


def _unset_attrs_on_tag(tag_bytes: bytes, attr_names: list[str]) -> bytes:
    for name in attr_names:
        tag_bytes = _unset_one_attr(tag_bytes, name)
    return tag_bytes


# ── Byte-splice applier (§2.2) ───────────────────────────────────────────────

def _apply_splices(data: bytes, splices: list[tuple[int, int, bytes]]) -> bytes:
    """Apply (start, end, replacement) splices to data.

    Splices are non-overlapping and processed in ascending start order.
    Elements outside all splice ranges are copied verbatim — this is the
    mechanism that upgrades the preservation claim from a soft promise to
    a hard guarantee (§2.2 preservation theorem).
    """
    ordered = sorted(splices, key=lambda s: s[0])
    for idx in range(len(ordered) - 1):
        if ordered[idx][1] > ordered[idx + 1][0]:
            raise ValueError(
                f"Overlapping splices: {ordered[idx][:2]} and {ordered[idx+1][:2]}"
            )
    result = bytearray()
    pos = 0
    for start, end, replacement in ordered:
        result.extend(data[pos:start])
        result.extend(replacement)
        pos = end
    result.extend(data[pos:])
    return bytes(result)


def _insert_position(anchor: ElementRecord, where: str) -> int:
    if where == "before":
        return anchor.span[0]
    if where == "after":
        return anchor.span[1]
    if where == "first-child":
        if anchor.is_self_closing:
            raise ValueError(f"Cannot insert first-child into self-closing element {anchor.eid!r}")
        return anchor.open_span[1]
    if where == "last-child":
        if anchor.is_self_closing or anchor.close_span is None:
            raise ValueError(f"Cannot insert last-child into self-closing element {anchor.eid!r}")
        return anchor.close_span[0]
    raise ValueError(f"Unknown where: {where!r}; must be one of {VALID_WHERE}")


def _check_wellformed(svg: str) -> None:
    """Raise ValueError if svg is not parseable as XML."""
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError(f"Result is not well-formed XML: {exc}") from exc


def _resolve_ops(
    data: bytes,
    ops: list[dict[str, Any]],
    records: dict[str, ElementRecord],
) -> list[tuple[int, int, bytes]]:
    """Validate ops and return byte-splice list. Raises ValueError on any problem."""
    if not isinstance(ops, list) or not ops:
        raise ValueError("Patch must be a non-empty list of op objects.")

    splices: list[tuple[int, int, bytes]] = []
    targeted: set[str] = set()

    for op in ops:
        if not isinstance(op, dict):
            raise ValueError("Each op must be a JSON object.")
        kind = op.get("op")
        if kind not in VALID_OPS:
            raise ValueError(f"Unknown op {kind!r}; valid ops: {sorted(VALID_OPS)}")

        if kind == "set":
            eid = op.get("eid", "")
            if eid not in records:
                raise ValueError(f"Unknown eid {eid!r}")
            attrs = op.get("attrs", {})
            if not isinstance(attrs, dict):
                raise ValueError("'set' op requires attrs: dict")
            bad = set(attrs) - ALLOWED_SET_ATTRS
            if bad:
                raise ValueError(f"Disallowed attributes in 'set': {sorted(bad)}")
            for v in attrs.values():
                if len(str(v)) > 128:
                    raise ValueError("Attribute value too long (max 128 chars)")
            rec = records[eid]
            new_open = _set_attrs_on_tag(data[rec.open_span[0]:rec.open_span[1]], attrs)
            splices.append((rec.open_span[0], rec.open_span[1], new_open))
            targeted.add(eid)

        elif kind == "unset":
            eid = op.get("eid", "")
            if eid not in records:
                raise ValueError(f"Unknown eid {eid!r}")
            attr_names = op.get("attrs", [])
            if not isinstance(attr_names, list):
                raise ValueError("'unset' op requires attrs: list")
            rec = records[eid]
            new_open = _unset_attrs_on_tag(data[rec.open_span[0]:rec.open_span[1]], attr_names)
            splices.append((rec.open_span[0], rec.open_span[1], new_open))
            targeted.add(eid)

        elif kind == "replace":
            eid = op.get("eid", "")
            if eid not in records:
                raise ValueError(f"Unknown eid {eid!r}")
            new_svg = op.get("svg", "")
            if not isinstance(new_svg, str):
                raise ValueError("'replace' op requires svg: str")
            rec = records[eid]
            splices.append((rec.span[0], rec.span[1], new_svg.encode("utf-8")))
            targeted.add(eid)

        elif kind == "delete":
            eid = op.get("eid", "")
            if eid not in records:
                raise ValueError(f"Unknown eid {eid!r}")
            rec = records[eid]
            splices.append((rec.span[0], rec.span[1], b""))
            targeted.add(eid)

        elif kind == "insert":
            anchor_eid = op.get("anchor", "")
            if anchor_eid not in records:
                raise ValueError(f"Unknown anchor eid {anchor_eid!r}")
            where = op.get("where", "after")
            if where not in VALID_WHERE:
                raise ValueError(f"Unknown where {where!r}; must be one of {VALID_WHERE}")
            new_svg = op.get("svg", "")
            if not isinstance(new_svg, str):
                raise ValueError("'insert' op requires svg: str")
            anchor = records[anchor_eid]
            pos = _insert_position(anchor, where)
            splices.append((pos, pos, new_svg.encode("utf-8")))

        elif kind == "move":
            eid = op.get("eid", "")
            anchor_eid = op.get("anchor", "")
            if eid not in records:
                raise ValueError(f"Unknown eid {eid!r}")
            if anchor_eid not in records:
                raise ValueError(f"Unknown anchor eid {anchor_eid!r}")
            where = op.get("where", "after")
            if where not in VALID_WHERE:
                raise ValueError(f"Unknown where {where!r}")
            rec = records[eid]
            anchor = records[anchor_eid]
            moved_bytes = data[rec.span[0]:rec.span[1]]
            insert_pos = _insert_position(anchor, where)
            splices.append((rec.span[0], rec.span[1], b""))
            splices.append((insert_pos, insert_pos, moved_bytes))
            targeted.add(eid)

        elif kind == "text":
            eid = op.get("eid", "")
            if eid not in records:
                raise ValueError(f"Unknown eid {eid!r}")
            rec = records[eid]
            if rec.is_self_closing or rec.close_span is None:
                raise ValueError(f"Cannot set text on self-closing element {eid!r}")
            content = op.get("content", "")
            if not isinstance(content, str):
                raise ValueError("'text' op requires content: str")
            content_start = rec.open_span[1]
            content_end = rec.close_span[0]
            splices.append((content_start, content_end, content.encode("utf-8")))
            targeted.add(eid)

    return splices


def apply_patch(source: str, ops: list[dict[str, Any]]) -> str:
    """Apply a flat list of patch ops to source SVG. Fail-closed: raises on any error.

    The applier is the ONLY component that writes to the document. The model
    never emits SVG — it emits patch ops.
    """
    if not ops:
        return source
    data, records = parse_svg(source)
    splices = _resolve_ops(data, ops, records)
    result_bytes = _apply_splices(data, splices)
    result = result_bytes.decode("utf-8")
    _check_wellformed(result)
    return result


def safe_apply_patch(source: str, ops: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Apply patch fail-closed: returns (original, error_msg) on failure."""
    try:
        return apply_patch(source, ops), None
    except Exception as exc:
        return source, str(exc)


# ── EP-score: Element-level Preservation (§4.1) ───────────────────────────────

def _ancestor_eids(eid: str, records: dict[str, ElementRecord]) -> set[str]:
    """Return eids of all ancestors of the given eid."""
    result: set[str] = set()
    if eid not in records:
        return result
    parent = records[eid].parent_eid
    while parent is not None:
        result.add(parent)
        parent = records[parent].parent_eid if parent in records else None
    return result


def ep_score(
    input_src: str,
    output_src: str,
    targeted_eids: set[str],
) -> dict[str, Any]:
    """Compute Element-level Preservation score (§4.1).

    EP-recall  = fraction of should-be-unchanged elements that are byte-identical
                 in the output. For our method this is 1.0 whenever the model
                 correctly identifies the target — the theorem guarantees it.
    EP-precision = fraction of output elements that weren't spuriously modified.
    """
    input_bytes, input_records = parse_svg(input_src)
    output_bytes, output_records = parse_svg(output_src)

    # touched = targeted + their ancestors (ancestors' open tags are unchanged,
    # but their content byte range shifts — honest carve-out from §2.2)
    touched: set[str] = set(targeted_eids)
    for eid in targeted_eids:
        touched |= _ancestor_eids(eid, input_records)

    # U = elements that should be unchanged
    U = {eid: rec for eid, rec in input_records.items() if eid not in touched}

    preserved = 0
    for eid, rec in U.items():
        elem_bytes = input_bytes[rec.span[0]:rec.span[1]]
        if eid in output_records:
            out_rec = output_records[eid]
            out_bytes = output_bytes[out_rec.span[0]:out_rec.span[1]]
            if elem_bytes == out_bytes:
                preserved += 1

    ep_recall = preserved / len(U) if U else 1.0

    # EP-precision: output elements not in touched set that are byte-identical to input
    output_untouched = {eid: rec for eid, rec in output_records.items() if eid not in touched}
    not_spurious = 0
    for eid, out_rec in output_untouched.items():
        if eid in input_records:
            in_rec = input_records[eid]
            in_bytes = input_bytes[in_rec.span[0]:in_rec.span[1]]
            out_bytes = output_bytes[out_rec.span[0]:out_rec.span[1]]
            if in_bytes == out_bytes:
                not_spurious += 1

    ep_precision = not_spurious / len(output_untouched) if output_untouched else 1.0
    f1_denom = ep_recall + ep_precision
    ep_f1 = 2 * ep_recall * ep_precision / f1_denom if f1_denom > 0 else 0.0

    return {
        "ep_recall": ep_recall,
        "ep_precision": ep_precision,
        "ep_f1": ep_f1,
        "untouched_elements": len(U),
        "preserved_byte_identical": preserved,
    }


# ── Source / task utilities ───────────────────────────────────────────────────

@dataclass(frozen=True)
class SourceRecord:
    path: Path
    source_id: str
    source_hash: str
    group_key: str
    origin: str


def normalized_svg_hash(source: str) -> str:
    compact = re.sub(r">\s+<", "><", source.strip())
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def structural_fingerprint(source: str) -> str:
    _, records = parse_svg(source)
    signature = [
        (rec.tag, sorted(k for k in rec.attrs if k not in {"id", "class", "style"}))
        for rec in sorted(records.values(), key=lambda r: r.open_span[0])
        if rec.tag in EDITABLE_TAGS
    ]
    payload = json.dumps(signature, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def humanize_label(value: str) -> str:
    value = re.sub(r"[_:.-]+", " ", value)
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def semantic_label(rec: ElementRecord) -> str:
    for name in ("aria-label", "data-label", "inkscape:label", "id"):
        if rec.attrs.get(name):
            return humanize_label(rec.attrs[name])
    return f"{rec.tag} element {rec.index + 1}"


def annotate_synthetic_ids(source: str, rng: random.Random) -> str:
    """Replace author IDs with random hex IDs, preserving aria-label for grounding."""
    data, records = parse_svg(source)
    recs_with_id = [r for r in records.values() if "id" in r.attrs]
    recs_with_id.sort(key=lambda r: r.open_span[0])
    splices: list[tuple[int, int, bytes]] = []
    for rec in recs_with_id:
        tag_bytes = data[rec.open_span[0]:rec.open_span[1]]
        if "aria-label" not in rec.attrs:
            tag_bytes = _set_one_attr(tag_bytes, "aria-label", humanize_label(rec.attrs["id"]))
        tag_bytes = _set_one_attr(tag_bytes, "id", f"el_{rng.getrandbits(48):012x}")
        splices.append((rec.open_span[0], rec.open_span[1], tag_bytes))
    return _apply_splices(data, splices).decode("utf-8")


# ── Color / geometry helpers ──────────────────────────────────────────────────

def hex_rgb(value: str) -> tuple[int, int, int] | None:
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", value.strip())
    if not m:
        return None
    raw = m.group(1)
    return tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def relative_luminance(value: str) -> float | None:
    rgb = hex_rgb(value)
    if rgb is None:
        return None

    def ch(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    if la is None or lb is None:
        return 1.0
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def likely_background_color(records: dict[str, ElementRecord], skip_eid: str | None = None) -> str | None:
    for rec in sorted(records.values(), key=lambda r: r.open_span[0]):
        if skip_eid and rec.eid == skip_eid:
            continue
        fill = rec.attrs.get("fill", "").lower()
        if rec.tag == "rect" and fill and fill not in {"none", "transparent"}:
            if rec.attrs.get("x", "0") == "0" and rec.attrs.get("y", "0") == "0":
                return fill
    return None


def choose_other_color(current: str, rng: random.Random, background: str | None = None) -> str:
    current = current.lower()
    candidates = [c for c in PALETTE if c.lower() != current]
    visible = [
        c for c in candidates
        if contrast_ratio(c, current) >= 1.8
        and (background is None or contrast_ratio(c, background) >= 2.2)
    ]
    return rng.choice(visible or candidates)


def format_number(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=1e-9):
        return str(int(round(value)))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def display_color(value: str, rng: random.Random) -> str:
    name = COLOR_NAMES.get(value.lower())
    if name and rng.random() < 0.65:
        return name
    return value


# ── Scene SVG templates ───────────────────────────────────────────────────────

def scene_svg(kind: int, rng: random.Random) -> str:
    sky = rng.choice(["#dbeafe", "#e0f2fe", "#fef3c7", "#fce7f3"])
    ground = rng.choice(["#22c55e", "#84cc16", "#65a30d", "#2f855a"])
    sun = rng.choice(["#f59e0b", "#facc15", "#fb923c"])
    house = rng.choice(["#ef4444", "#f97316", "#7c3aed", "#2563eb"])
    roof = rng.choice(["#7f1d1d", "#991b1b", "#581c87", "#1e3a8a"])
    water = rng.choice(["#38bdf8", "#06b6d4", "#2563eb"])
    tree = rng.choice(["#166534", "#15803d", "#16a34a"])

    templates = [
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="sky" x="0" y="0" width="128" height="128" fill="{sky}"/>
  <circle id="sun" cx="24" cy="24" r="14" fill="{sun}"/>
  <path id="hill" d="M0 92 C32 70 62 82 90 72 C108 66 120 76 128 70 L128 128 L0 128 Z" fill="{ground}"/>
  <rect id="house-body" x="46" y="62" width="34" height="32" fill="{house}"/>
  <polygon id="house-roof" points="42,64 63,45 84,64" fill="{roof}"/>
  <rect id="door" x="58" y="74" width="10" height="20" fill="#78350f"/>
  <circle id="window" cx="73" cy="73" r="5" fill="#f8fafc" stroke="#111827"/>
  <path id="bird" d="M94 28 Q100 22 106 28 Q112 22 118 28" fill="none" stroke="#111827" stroke-width="3"/>
</svg>""",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="background" x="0" y="0" width="128" height="128" fill="{sky}"/>
  <path id="sea" d="M0 82 C20 76 38 90 58 82 C78 74 98 90 128 80 L128 128 L0 128 Z" fill="{water}"/>
  <path id="sand" d="M0 100 C28 94 54 103 82 96 C104 91 118 96 128 94 L128 128 L0 128 Z" fill="#fde68a"/>
  <circle id="sunset" cx="98" cy="35" r="18" fill="{sun}"/>
  <rect id="boat-hull" x="36" y="72" width="38" height="9" rx="4" fill="#92400e"/>
  <polygon id="sail-main" points="55,38 55,72 78,72" fill="#f8fafc" stroke="#111827"/>
  <polygon id="sail-small" points="52,45 52,72 35,72" fill="#e0f2fe" stroke="#111827"/>
  <line id="mast" x1="55" y1="35" x2="55" y2="82" stroke="#111827" stroke-width="3"/>
</svg>""",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="night" x="0" y="0" width="128" height="128" fill="#111827"/>
  <circle id="moon" cx="100" cy="25" r="13" fill="#f8fafc"/>
  <path id="mountain-back" d="M0 95 L26 50 L48 95 Z" fill="#334155"/>
  <path id="mountain-mid" d="M28 98 L68 34 L108 98 Z" fill="#475569"/>
  <path id="snowcap" d="M68 34 L56 54 L80 54 Z" fill="#e2e8f0"/>
  <rect id="cabin" x="26" y="80" width="30" height="24" fill="#b45309"/>
  <polygon id="cabin-roof" points="22,82 41,66 60,82" fill="#7f1d1d"/>
  <rect id="cabin-window" x="44" y="88" width="7" height="7" fill="#facc15"/>
</svg>""",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="field" x="0" y="0" width="128" height="128" fill="#dcfce7"/>
  <path id="stem" d="M64 58 C60 78 62 94 58 118" fill="none" stroke="#15803d" stroke-width="7"/>
  <ellipse id="leaf-left" cx="48" cy="86" rx="15" ry="8" fill="{tree}" transform="rotate(-25 48 86)"/>
  <ellipse id="leaf-right" cx="76" cy="92" rx="15" ry="8" fill="{tree}" transform="rotate(25 76 92)"/>
  <circle id="flower-center" cx="64" cy="44" r="12" fill="#78350f"/>
  <ellipse id="petal-top" cx="64" cy="22" rx="10" ry="20" fill="{sun}"/>
  <ellipse id="petal-left" cx="43" cy="44" rx="20" ry="10" fill="{sun}"/>
  <ellipse id="petal-right" cx="85" cy="44" rx="20" ry="10" fill="{sun}"/>
</svg>""",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="city-sky" x="0" y="0" width="128" height="128" fill="{sky}"/>
  <rect id="tower-left" x="12" y="52" width="28" height="76" fill="#475569"/>
  <rect id="tower-center" x="48" y="30" width="34" height="98" fill="#334155"/>
  <rect id="tower-right" x="91" y="63" width="25" height="65" fill="#64748b"/>
  <rect id="window-left" x="20" y="64" width="9" height="12" fill="#facc15"/>
  <rect id="window-center" x="59" y="45" width="11" height="14" fill="#facc15"/>
  <rect id="window-right" x="98" y="75" width="10" height="12" fill="#f8fafc"/>
  <circle id="city-moon" cx="104" cy="24" r="12" fill="#f8fafc"/>
</svg>""",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="robot-background" x="0" y="0" width="128" height="128" fill="#e2e8f0"/>
  <rect id="robot-head" x="38" y="20" width="52" height="38" rx="8" fill="#94a3b8" stroke="#111827" stroke-width="3"/>
  <circle id="robot-eye-left" cx="53" cy="38" r="6" fill="{water}"/>
  <circle id="robot-eye-right" cx="75" cy="38" r="6" fill="{water}"/>
  <rect id="robot-body" x="31" y="64" width="66" height="46" rx="8" fill="#64748b" stroke="#111827" stroke-width="3"/>
  <circle id="robot-button" cx="64" cy="83" r="7" fill="{sun}"/>
  <line id="robot-arm-left" x1="31" y1="75" x2="13" y2="94" stroke="#111827" stroke-width="6"/>
  <line id="robot-arm-right" x1="97" y1="75" x2="115" y2="94" stroke="#111827" stroke-width="6"/>
</svg>""",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="table-background" x="0" y="0" width="128" height="128" fill="#fef3c7"/>
  <ellipse id="bowl" cx="64" cy="92" rx="43" ry="22" fill="#0f766e"/>
  <circle id="apple-left" cx="43" cy="67" r="18" fill="#ef4444"/>
  <circle id="orange-center" cx="66" cy="61" r="19" fill="#f97316"/>
  <circle id="apple-right" cx="88" cy="70" r="17" fill="#84cc16"/>
  <path id="fruit-leaf" d="M62 42 Q72 29 84 40 Q73 48 62 42" fill="{tree}"/>
  <path id="fruit-stem" d="M66 45 L69 31" fill="none" stroke="#78350f" stroke-width="5"/>
</svg>""",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect id="poster-background" x="0" y="0" width="128" height="128" fill="#f8fafc"/>
  <circle id="poster-circle" cx="38" cy="39" r="25" fill="{house}"/>
  <rect id="poster-square" x="66" y="16" width="43" height="43" fill="{water}"/>
  <polygon id="poster-triangle" points="18,111 49,66 80,111" fill="{sun}"/>
  <ellipse id="poster-ellipse" cx="92" cy="88" rx="25" ry="16" fill="{tree}"/>
  <line id="poster-line" x1="12" y1="14" x2="116" y2="116" stroke="#111827" stroke-width="4"/>
</svg>""",
    ]
    return templates[kind % len(templates)]


# ── Instruction generation ────────────────────────────────────────────────────

def parse_task_types(value: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        requested = tuple(item.strip() for item in value.split(",") if item.strip())
    else:
        requested = tuple(value)
    unknown = sorted(set(requested) - set(DEFAULT_TASK_TYPES))
    if unknown:
        raise ValueError(f"Unknown task types: {', '.join(unknown)}")
    return requested or ("color",)


def _use_direct_id(mode: str, rng: random.Random) -> bool:
    if mode == "direct":
        return True
    if mode == "semantic":
        return False
    if mode != "mixed":
        raise ValueError(f"Unknown instruction mode {mode!r}")
    return rng.random() < 0.15


def make_edit_instruction(
    rec: ElementRecord,
    edit_type: str,
    ops: list[dict[str, Any]],
    rng: random.Random,
    mode: str,
    delta: float | None = None,
) -> tuple[str, str]:
    label = semantic_label(rec)

    if _use_direct_id(mode, rng):
        if rec.attrs.get("id"):
            ref = f"element id `{rec.attrs['id']}`"
        else:
            ref = f"element `{rec.eid}`"
        details = " and ".join(
            f"set {k} to {v}" for k, v in ops[0].get("attrs", {}).items()
        )
        return f"For {ref}, {details}.", "direct"

    if edit_type == "set_fill":
        val = display_color(list(ops[0]["attrs"].values())[0], rng)
        templates = [
            f"Make the {label} {val}.",
            f"Set the fill of the {label} to {val}.",
            f"Recolor the {label} using {val}.",
        ]
    elif edit_type == "set_stroke":
        val = display_color(list(ops[0]["attrs"].values())[0], rng)
        templates = [
            f"Change the outline of the {label} to {val}.",
            f"Give the {label} a {val} stroke.",
            f"Set the stroke color of the {label} to {val}.",
        ]
    elif edit_type == "set_opacity":
        percent = round(float(list(ops[0]["attrs"].values())[0]) * 100)
        templates = [
            f"Make the {label} {percent}% opaque.",
            f"Set the opacity of the {label} to {percent}%.",
        ]
    elif edit_type == "set_stroke_width":
        val = list(ops[0]["attrs"].values())[0]
        templates = [
            f"Set the outline width of the {label} to {val}.",
            f"Make the {label}'s stroke {val} pixels wide.",
        ]
    elif edit_type.startswith("move_"):
        amount = abs(delta or 0)
        direction = edit_type.removeprefix("move_")
        templates = [
            f"Move the {label} {format_number(amount)} pixels {direction}.",
            f"Shift the {label} {format_number(amount)} pixels to the {direction}.",
        ]
    elif edit_type == "multi_style":
        color = display_color(ops[0]["attrs"].get("fill", ""), rng)
        percent = round(float(ops[0]["attrs"].get("opacity", "1")) * 100)
        templates = [
            f"Make the {label} {color} and {percent}% opaque.",
            f"Recolor the {label} {color}, then set its opacity to {percent}%.",
        ]
    else:
        attrs_str = " and ".join(f"set {k} to {v}" for k, v in ops[0].get("attrs", {}).items())
        templates = [f"For the {label}, {attrs_str}."]

    return rng.choice(templates), "semantic"


# ── Patch generation (flat op array, §2.1) ────────────────────────────────────

def make_patch_for_source(
    source: str,
    rng: random.Random,
    task_types: str | tuple[str, ...] | list[str] = ("color",),
    instruction_mode: str = "semantic",
) -> tuple[list[dict[str, Any]], ElementRecord, str, str]:
    """Return (ops, target_record, instruction, edit_type:style).

    ops is a flat list of patch op dicts matching the §2.1 grammar.
    Only 'set' ops are generated here; the full op set is exercised by
    the baselines and round-trip tests.
    """
    _, records = parse_svg(source)
    enabled = set(parse_task_types(task_types))
    candidates: list[tuple[ElementRecord, str, str | None]] = []

    for rec in records.values():
        if rec.tag not in EDITABLE_TAGS or rec.tag == "svg":
            continue
        fill = rec.attrs.get("fill", "").lower()
        stroke = rec.attrs.get("stroke", "").lower()

        if "color" in enabled:
            if fill and fill not in {"none", "transparent"}:
                candidates.append((rec, "set_fill", "fill"))
            if stroke and stroke not in {"none", "transparent"}:
                candidates.append((rec, "set_stroke", "stroke"))
        if "opacity" in enabled:
            candidates.append((rec, "set_opacity", None))
        if "stroke_width" in enabled and stroke and stroke not in {"none", "transparent"}:
            candidates.append((rec, "set_stroke_width", None))
        if "geometry" in enabled:
            for attr in ("x", "cx", "y", "cy"):
                try:
                    float(rec.attrs.get(attr, ""))
                except ValueError:
                    continue
                candidates.append((rec, "move", attr))
        if "multi_style" in enabled and fill and fill not in {"none", "transparent"}:
            candidates.append((rec, "multi_style", None))

    if not candidates:
        raise ValueError("No candidates for the requested task types.")

    rec, candidate_type, attr = rng.choice(candidates)
    delta: float | None = None

    if candidate_type in {"set_fill", "set_stroke"}:
        assert attr is not None
        current = rec.attrs[attr]
        bg = likely_background_color(records, skip_eid=rec.eid)
        value = choose_other_color(current, rng, bg)
        ops = [{"op": "set", "eid": rec.eid, "attrs": {attr: value}}]
        edit_type = candidate_type

    elif candidate_type == "set_opacity":
        current = rec.attrs.get("opacity", "1")
        values = [v for v in ("0.35", "0.55", "0.75", "0.9") if v != current]
        ops = [{"op": "set", "eid": rec.eid, "attrs": {"opacity": rng.choice(values)}}]
        edit_type = candidate_type

    elif candidate_type == "set_stroke_width":
        current = rec.attrs.get("stroke-width", "1")
        values = [v for v in ("1", "2", "4", "6", "8") if v != current]
        ops = [{"op": "set", "eid": rec.eid, "attrs": {"stroke-width": rng.choice(values)}}]
        edit_type = candidate_type

    elif candidate_type == "move":
        assert attr is not None
        current = float(rec.attrs[attr])
        delta = float(rng.choice((-10, -6, 6, 10)))
        value = format_number(current + delta)
        ops = [{"op": "set", "eid": rec.eid, "attrs": {attr: value}}]
        edit_type = "move_right" if attr in {"x", "cx"} and delta > 0 else \
                    "move_left"  if attr in {"x", "cx"} else \
                    "move_down"  if delta > 0 else "move_up"

    else:  # multi_style
        current_fill = rec.attrs["fill"]
        bg = likely_background_color(records, skip_eid=rec.eid)
        color = choose_other_color(current_fill, rng, bg)
        opacity = rng.choice(("0.5", "0.7", "0.85"))
        ops = [{"op": "set", "eid": rec.eid, "attrs": {"fill": color, "opacity": opacity}}]
        edit_type = "multi_style"

    # Dry-run validation
    apply_patch(source, ops)
    instruction, style = make_edit_instruction(rec, edit_type, ops, rng, instruction_mode, delta)
    return ops, rec, instruction, f"{edit_type}:{style}"


# ── Prompt construction (annotated view, §1.2) ────────────────────────────────

def _prompt_attr_value(value: str) -> str:
    """Trim very long attribute values for element-summary prompts."""
    if len(value) <= PROMPT_ATTR_VALUE_LIMIT:
        return value
    keep = max(0, PROMPT_ATTR_VALUE_LIMIT - 3)
    return value[:keep] + "..."


def element_summary_view(records: dict[str, ElementRecord]) -> str:
    """Compact prompt view for long SVGs with heavy path geometry."""
    lines: list[str] = []
    for rec in sorted(records.values(), key=lambda r: r.open_span[0]):
        if rec.tag not in EDITABLE_TAGS:
            continue
        attrs = []
        for name in PROMPT_SUMMARY_ATTRS:
            if name not in rec.attrs:
                continue
            value = _escape_attr(_prompt_attr_value(rec.attrs[name]))
            attrs.append(f'{name}="{value}"')
        attr_text = (" " + " ".join(attrs)) if attrs else ""
        parent_text = f' parent="{rec.parent_eid}"' if rec.parent_eid else ""
        lines.append(f"[{rec.eid}] depth={rec.depth}{parent_text} <{rec.tag}{attr_text}>")
    return "\n".join(lines)


def prompt_document_view(source: str, records: dict[str, ElementRecord]) -> tuple[str, str, str]:
    """Return (label, fence_language, view) for the SVG part of the prompt."""
    view = annotated_view(source, records)
    if len(view) <= PROMPT_VIEW_FULL_CHAR_LIMIT:
        return "Annotated SVG (element IDs shown as [eid] markers)", "svg", view
    return (
        "Element summary (long geometry omitted; element IDs shown as [eid] markers)",
        "text",
        element_summary_view(records),
    )

def make_patch_prompt(input_svg: str, instruction: str) -> str:
    """Build the model prompt using the annotated view (§1.2).

    The annotated view shows [eid] markers so the model can ground
    semantic references to concrete element IDs. The eid vocabulary
    approximates the grammar-constrained decoding trie (§2.3 TODO).
    """
    _, records = parse_svg(input_svg)
    view_label, view_fence, view = prompt_document_view(input_svg, records)
    vocab = eid_vocabulary(records)
    return (
        "You are a locality-preserving SVG patch editor.\n"
        "Return ONLY a JSON array of patch ops. Do NOT regenerate the full SVG.\n\n"
        "Op schema (use exactly these keys):\n"
        '  {"op":"set",    "eid":"<eid>", "attrs":{"name":"value",...}}\n'
        '  {"op":"unset",  "eid":"<eid>", "attrs":["name",...]}\n'
        '  {"op":"replace","eid":"<eid>", "svg":"<markup>"}\n'
        '  {"op":"delete", "eid":"<eid>"}\n'
        '  {"op":"insert", "anchor":"<eid>","where":"before|after|first-child|last-child","svg":"<markup>"}\n'
        '  {"op":"move",   "eid":"<eid>","anchor":"<eid>","where":"before|after|first-child|last-child"}\n'
        '  {"op":"text",   "eid":"<eid>","content":"<text>"}\n\n'
        f"Valid eids for this document: {vocab}\n\n"
        "Allowed attributes for 'set': fill, stroke, opacity, fill-opacity, stroke-opacity, "
        "stroke-width, x, y, cx, cy, r, rx, ry, width, height, viewBox, transform.\n\n"
        "Ground the instruction to an eid from the list above. "
        "Change ONLY the requested element and attributes.\n\n"
        f"Instruction:\n{instruction}\n\n"
        f"{view_label}:\n"
        f"```{view_fence}\n"
        f"{view}\n"
        "```\n"
    )


def extract_json_array(text: str) -> list[dict[str, Any]]:
    """Extract the first JSON array from model output."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    decoder = json.JSONDecoder()
    for i, char in enumerate(text):
        if char != "[":
            continue
        try:
            obj, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, list):
            return obj
    raise ValueError(f"No JSON array found in: {text[:200]!r}")


# ── Task / SFT row builders ───────────────────────────────────────────────────

def make_task_from_source(
    task_id: str,
    source_path: Path,
    rng: random.Random,
    source_record: SourceRecord | None = None,
    task_types: str | tuple[str, ...] | list[str] = ("color",),
    instruction_mode: str = "semantic",
) -> dict[str, Any]:
    source = source_path.read_text(encoding="utf-8")
    ops, rec, instruction, edit_type = make_patch_for_source(
        source, rng, task_types=task_types, instruction_mode=instruction_mode,
    )
    gold = apply_patch(source, ops)
    source_hash = source_record.source_hash if source_record else normalized_svg_hash(source)
    group_key = source_record.group_key if source_record else structural_fingerprint(source)
    targeted_eids = [op["eid"] for op in ops if "eid" in op]
    return {
        "task_id": task_id,
        "source_path": str(source_path),
        "source_id": source_record.source_id if source_record else source_path.name,
        "source_hash": source_hash,
        "source_group": group_key,
        "instruction": instruction,
        "input_svg": source,
        "gold_svg": gold,
        "ops": ops,
        "targeted_eids": targeted_eids,
        "target_eid": rec.eid,
        "target_label": semantic_label(rec),
        "target_id": rec.attrs.get("id"),
        "edit_type": edit_type.split(":", 1)[0],
        "instruction_style": edit_type.split(":", 1)[1],
        "target_text": json.dumps(ops, ensure_ascii=False),
    }


def make_task(task_id: str, rng: random.Random) -> dict[str, Any]:
    source = annotate_synthetic_ids(scene_svg(rng.randrange(SYNTHETIC_TEMPLATE_COUNT), rng), rng)
    temp_path = Path(f"synthetic_{task_id}.svg")
    ops, rec, instruction, edit_type = make_patch_for_source(
        source, rng, task_types=DEFAULT_TASK_TYPES, instruction_mode="semantic",
    )
    gold = apply_patch(source, ops)
    targeted_eids = [op["eid"] for op in ops if "eid" in op]
    return {
        "task_id": task_id,
        "source_path": str(temp_path),
        "source_id": temp_path.name,
        "source_hash": normalized_svg_hash(source),
        "source_group": structural_fingerprint(source),
        "instruction": instruction,
        "input_svg": source,
        "gold_svg": gold,
        "ops": ops,
        "targeted_eids": targeted_eids,
        "target_eid": rec.eid,
        "target_label": semantic_label(rec),
        "target_id": rec.attrs.get("id"),
        "edit_type": edit_type.split(":", 1)[0],
        "instruction_style": edit_type.split(":", 1)[1],
        "target_text": json.dumps(ops, ensure_ascii=False),
    }


# ── SVGEditBench rows (paper arXiv:2404.13710) ───────────────────────────────

def is_svgeditbench_dir(path: Path) -> bool:
    return path.is_dir() and all((path / name / "query").is_dir() for name in SVGEDITBENCH_TASK_DIRS)


def clone_svgeditbench_repo(target: Path) -> Path:
    target = target.expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    if target.exists() and is_svgeditbench_dir(target):
        return target
    if target.exists():
        raise SystemExit(f"Cannot clone SVGEditBench into existing non-dataset path: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning benchmark dataset from {SVGEDITBENCH_REPO_URL} -> {target}")
    subprocess.check_call([
        "git", "clone", "--depth", "1", SVGEDITBENCH_REPO_URL, str(target)
    ])
    if not is_svgeditbench_dir(target):
        raise SystemExit(f"Cloned repository does not look like SVGEditBench: {target}")
    return target


def resolve_svgeditbench_dir(path: Path, out_dir: Path) -> Path:
    """Resolve an SVGEditBench repo/dataset dir from either a dir or the paper PDF."""
    path = path.expanduser()
    if path.is_dir():
        if not is_svgeditbench_dir(path):
            raise SystemExit(f"{path} is not an SVGEditBench dataset directory.")
        return path

    if path.is_file() and path.suffix.lower() == ".pdf":
        candidates = [
            Path.cwd() / "SVGEditBench",
            path.parent / "SVGEditBench",
            out_dir / "SVGEditBench",
            out_dir / "00_source_svgs" / "SVGEditBench",
        ]
        for candidate in candidates:
            if is_svgeditbench_dir(candidate):
                print(f"SVGEditBench paper -> {path}")
                print(f"Using existing dataset repo -> {candidate}")
                return candidate

        target = out_dir / "00_source_svgs" / "SVGEditBench"
        print(f"SVGEditBench paper -> {path}")
        return clone_svgeditbench_repo(target)

    auto_names = {"auto", "svgeditbench"}
    if str(path).lower() in auto_names or path.name.lower() == "svgeditbench":
        return clone_svgeditbench_repo(path if str(path).lower() != "auto" else out_dir / "00_source_svgs" / "SVGEditBench")

    raise SystemExit(
        f"{path} must be an SVGEditBench directory, 'SVGEditBench' for auto-clone, "
        "or the 2404.13710v1.pdf paper path."
    )


def extract_svg_block(text: str) -> str:
    m = re.search(r"```svg\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        raise ValueError("No ```svg ... ``` block found in SVGEditBench query.")
    return m.group(1).strip()


def extract_svgeditbench_instruction(text: str) -> str:
    m = re.search(r"```svg", text, flags=re.IGNORECASE)
    if not m:
        raise ValueError("No SVG code fence found in SVGEditBench query.")
    return re.sub(r"\s+", " ", text[:m.start()]).strip()


def _svg_root_record(records: dict[str, ElementRecord]) -> ElementRecord:
    roots = [
        rec for rec in records.values()
        if rec.tag == "svg" and rec.parent_eid is None
    ]
    if not roots:
        raise ValueError("No root <svg> element found.")
    return min(roots, key=lambda rec: rec.open_span[0])


def _same_svg_attr_value(a: str, b: str) -> bool:
    return a.strip().lower() == b.strip().lower()


def _records_with_fill(records: dict[str, ElementRecord], color: str) -> list[ElementRecord]:
    matches = [
        rec for rec in records.values()
        if rec.tag != "svg" and _same_svg_attr_value(rec.attrs.get("fill", ""), color)
    ]
    matches.sort(key=lambda rec: rec.open_span[0])
    if not matches:
        raise ValueError(f"No elements with fill={color!r}.")
    return matches


def make_svgeditbench_ops(
    source: str,
    instruction: str,
    task_dir_name: str,
) -> list[dict[str, Any]]:
    """Convert one SVGEditBench full-SVG edit task into patch ops."""
    _, records = parse_svg(source)

    if task_dir_name == "1_ChangeColor":
        m = re.search(
            r"with a\s+([#A-Za-z0-9]+)\s+color\s+to\s+([#A-Za-z0-9]+)",
            instruction,
            flags=re.IGNORECASE,
        )
        if not m:
            raise ValueError(f"Could not parse Change Color instruction: {instruction!r}")
        color_from, color_to = m.groups()
        return [
            {"op": "set", "eid": rec.eid, "attrs": {"fill": color_to}}
            for rec in _records_with_fill(records, color_from)
        ]

    if task_dir_name == "2_SetContour":
        m = re.search(
            r"with a\s+([#A-Za-z0-9]+)\s+color",
            instruction,
            flags=re.IGNORECASE,
        )
        if not m:
            raise ValueError(f"Could not parse Set Contour instruction: {instruction!r}")
        area_color = m.group(1)
        return [
            {"op": "set", "eid": rec.eid, "attrs": {"stroke": "black", "stroke-width": "1"}}
            for rec in _records_with_fill(records, area_color)
        ]

    if task_dir_name == "3_Compression":
        return []

    root = _svg_root_record(records)
    if task_dir_name == "4_UpSideDown":
        return [{"op": "set", "eid": root.eid, "attrs": {"transform": "translate(0,36) scale(1,-1)"}}]
    if task_dir_name == "5_Transparency":
        return [{"op": "set", "eid": root.eid, "attrs": {"opacity": "0.5"}}]
    if task_dir_name == "6_CropToHalf":
        return [{"op": "set", "eid": root.eid, "attrs": {"viewBox": "0 0 18 36"}}]

    raise ValueError(f"Unsupported SVGEditBench task directory: {task_dir_name}")


def make_svgeditbench_task(
    task_id: str,
    query_path: Path,
    answer_path: Path,
    task_dir_name: str,
) -> dict[str, Any]:
    query_text = query_path.read_text(encoding="utf-8")
    instruction = extract_svgeditbench_instruction(query_text)
    source = extract_svg_block(query_text)
    answer = answer_path.read_text(encoding="utf-8").strip()
    ops = make_svgeditbench_ops(source, instruction, task_dir_name)
    gold = apply_patch(source, ops)
    gold_changes = changed_attributes(source, gold)
    answer_changes = changed_attributes(source, answer)
    if gold_changes != answer_changes:
        raise ValueError(
            f"Patch/answer mismatch for {query_path}: "
            f"patch changes={gold_changes}, answer changes={answer_changes}"
        )

    _, records = parse_svg(source)
    source_hash = normalized_svg_hash(source)
    targeted_eids = [op["eid"] for op in ops if "eid" in op]
    first_target = records.get(targeted_eids[0]) if targeted_eids else None
    edit_type = SVGEDITBENCH_TASK_DIRS[task_dir_name]
    return {
        "task_id": task_id,
        "benchmark_task_id": f"{task_dir_name}/{query_path.stem}",
        "source_path": str(query_path),
        "answer_path": str(answer_path),
        "source_id": query_path.stem,
        "source_hash": source_hash,
        "source_group": source_hash,
        "instruction": instruction,
        "input_svg": source,
        "gold_svg": gold,
        "ops": ops,
        "targeted_eids": targeted_eids,
        "target_eid": first_target.eid if first_target else None,
        "target_label": semantic_label(first_target) if first_target else "document unchanged",
        "target_id": first_target.attrs.get("id") if first_target else None,
        "edit_type": edit_type,
        "instruction_style": "svgeditbench",
        "target_text": json.dumps(ops, ensure_ascii=False),
    }


def load_svgeditbench_tasks(dataset_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_dir_name in SVGEDITBENCH_TASK_DIRS:
        task_dir = dataset_dir / task_dir_name
        query_dir = task_dir / "query"
        answer_dir = task_dir / "answer"
        if not query_dir.is_dir() or not answer_dir.is_dir():
            raise SystemExit(f"Missing query/answer folders under {task_dir}")
        for query_path in sorted(query_dir.glob("*.txt")):
            answer_path = answer_dir / f"{query_path.stem}.svg"
            if not answer_path.exists():
                raise SystemExit(f"Missing SVGEditBench answer for {query_path}")
            rows.append(make_svgeditbench_task(
                f"svgeditbench_{len(rows):06d}",
                query_path,
                answer_path,
                task_dir_name,
            ))
    if not rows:
        raise SystemExit(f"No SVGEditBench rows found in {dataset_dir}")
    return rows


def _scaled_counts_to_available(
    n_train: int,
    n_val: int,
    n_eval: int,
    available: int,
) -> dict[str, int]:
    requested = {"train": n_train, "val": n_val, "eval": n_eval}
    total_requested = sum(requested.values())
    if total_requested <= available:
        return requested
    if total_requested <= 0:
        return requested

    raw = {name: value * available / total_requested for name, value in requested.items()}
    scaled = {name: int(math.floor(value)) for name, value in raw.items()}
    remaining = available - sum(scaled.values())
    order = sorted(raw, key=lambda name: raw[name] - scaled[name], reverse=True)
    for name in order[:remaining]:
        scaled[name] += 1
    print(
        "SVGEditBench has only "
        f"{available} rows; scaled requested counts from {requested} to {scaled}."
    )
    return scaled


def _split_fixed_rows_by_source(
    rows: list[dict[str, Any]],
    n_train: int,
    n_val: int,
    n_eval: int,
    seed: int,
    split_strategy: str,
) -> dict[str, list[dict[str, Any]]]:
    counts = _scaled_counts_to_available(n_train, n_val, n_eval, len(rows))
    group_field = "source_group" if split_strategy == "group" else "source_id"
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row[group_field]), []).append(row)

    rng = random.Random(seed)
    keys = list(groups)
    rng.shuffle(keys)
    result: dict[str, list[dict[str, Any]]] = {"train": [], "val": [], "eval": []}

    def take_groups(target_count: int) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        while keys and len(selected) < target_count:
            selected.extend(groups[keys.pop(0)])
        rng.shuffle(selected)
        return selected[:target_count]

    # Hold out eval/val first; train receives the remaining source groups.
    result["eval"] = take_groups(counts["eval"])
    result["val"] = take_groups(counts["val"])
    train_pool: list[dict[str, Any]] = []
    for key in keys:
        train_pool.extend(groups[key])
    rng.shuffle(train_pool)
    result["train"] = train_pool[:counts["train"]]
    if len(result["train"]) < counts["train"]:
        print(
            f"SVGEditBench source-disjoint split supplied {len(result['train'])}/"
            f"{counts['train']} requested train rows."
        )

    for split, split_rows in result.items():
        for idx, row in enumerate(split_rows):
            row["task_id"] = f"{split}_{idx:06d}"
            row["split"] = split
    return result


def build_svgeditbench_tasks(
    dataset_dir: Path,
    out_dir: Path,
    n_train: int,
    n_eval: int,
    seed: int,
    n_val: int = 0,
    split_strategy: str = "group",
) -> tuple[Path, Path, Path, Path]:
    tasks_dir = out_dir / "01_tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    rows = load_svgeditbench_tasks(dataset_dir)
    splits = _split_fixed_rows_by_source(
        rows,
        n_train=n_train,
        n_val=n_val,
        n_eval=n_eval,
        seed=seed,
        split_strategy=split_strategy,
    )
    train, val, eval_rows = splits["train"], splits["val"], splits["eval"]
    tasks = train + val + eval_rows

    all_path   = tasks_dir / "all_tasks.jsonl"
    train_path = tasks_dir / "train_tasks.jsonl"
    val_path   = tasks_dir / "val_tasks.jsonl"
    eval_path  = tasks_dir / "eval_tasks.jsonl"
    write_jsonl(all_path, tasks)
    write_jsonl(train_path, train)
    write_jsonl(val_path, val)
    write_jsonl(eval_path, eval_rows)

    split_hashes = {s: {row["source_hash"] for row in split_rows} for s, split_rows in splits.items()}
    split_groups = {s: {row["source_group"] for row in split_rows} for s, split_rows in splits.items()}
    audit = {
        "dataset": "SVGEditBench",
        "dataset_dir": str(dataset_dir),
        "dataset_url": SVGEDITBENCH_REPO_URL,
        "raw_tasks": len(rows),
        "split_strategy": split_strategy,
        "source_counts": {s: len({row["source_id"] for row in split_rows}) for s, split_rows in splits.items()},
        "task_counts": {"train": len(train), "val": len(val), "eval": len(eval_rows)},
        "task_type_counts": {
            split: {
                name: sum(1 for row in split_rows if row["edit_type"] == name)
                for name in SVGEDITBENCH_TASK_DIRS.values()
            }
            for split, split_rows in splits.items()
        },
        "exact_hash_overlap": {
            "train_val":  len(split_hashes["train"] & split_hashes["val"]),
            "train_eval": len(split_hashes["train"] & split_hashes["eval"]),
            "val_eval":   len(split_hashes["val"]   & split_hashes["eval"]),
        },
        "group_overlap": {
            "train_val":  len(split_groups["train"] & split_groups["val"]),
            "train_eval": len(split_groups["train"] & split_groups["eval"]),
            "val_eval":   len(split_groups["val"]   & split_groups["eval"]),
        },
    }
    (tasks_dir / "split_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(
        f"SVGEditBench patch tasks -> {tasks_dir} "
        f"({len(train)} train, {len(val)} val, {len(eval_rows)} eval; "
        f"train/eval group overlap={audit['group_overlap']['train_eval']})"
    )
    return all_path, train_path, val_path, eval_path


# ── JSONL / IO ────────────────────────────────────────────────────────────────

def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def stage(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def running_in_colab() -> bool:
    return (
        "google.colab" in sys.modules
        or bool(os.environ.get("COLAB_RELEASE_TAG") or os.environ.get("COLAB_GPU"))
        or (Path("/content").exists() and not os.environ.get("KAGGLE_KERNEL_RUN_TYPE"))
    )


def default_output_dir(force_colab: bool = False) -> Path:
    if force_colab or running_in_colab():
        return Path("/content/patchsvg_svgeditbench")
    if os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        return Path("/kaggle/working/patchsvg_t4_smoke")
    return Path("patchsvg_t4_smoke")


def mount_google_drive(force_remount: bool = False) -> None:
    """Mount Google Drive in Colab, or fail with a clear message elsewhere."""
    try:
        from google.colab import drive  # type: ignore[import-not-found]
    except Exception as exc:
        raise SystemExit("--gdrive requires a Google Colab runtime.") from exc
    drive.mount("/content/drive", force_remount=force_remount)


def path_is_google_drive(path: Path | str | None) -> bool:
    if path is None:
        return False
    return Path(path).as_posix().startswith("/content/drive/")


def configure_persistent_output_dir(
    args: argparse.Namespace,
    mount_fn: Any | None = None,
) -> None:
    """Resolve output_dir and optionally mount Drive before any artifacts are written."""
    if bool(getattr(args, "gdrive", False)):
        if getattr(args, "output_dir", None) is None:
            args.output_dir = Path(getattr(args, "gdrive_dir", DEFAULT_GDRIVE_OUTPUT_DIR))
        mounter = mount_google_drive if mount_fn is None else mount_fn
        try:
            mounter(bool(getattr(args, "gdrive_force_remount", False)))
        except Exception as exc:
            if not bool(getattr(args, "gdrive_local_fallback", True)):
                raise
            args.gdrive = False
            args.output_dir = default_output_dir(force_colab=bool(getattr(args, "colab", False)))
            print(
                "[diag] Google Drive mount failed; falling back to local Colab "
                f"output dir -> {args.output_dir}. Drive error: {exc}"
            )
            return
        print(f"[diag] Google Drive output dir -> {args.output_dir}")
        print(f"[diag] Drive Trainer checkpoints -> {args.output_dir / '04_model' / 'trainer'}")
        return

    if getattr(args, "output_dir", None) is None:
        args.output_dir = default_output_dir(force_colab=bool(getattr(args, "colab", False)))


def apply_storage_defaults(args: argparse.Namespace) -> None:
    """Apply quota-friendly checkpoint defaults after output_dir is known."""
    requested = int(getattr(args, "save_total_limit", -1))
    if requested >= 0:
        return

    if bool(getattr(args, "gdrive", False)) or path_is_google_drive(getattr(args, "output_dir", None)):
        args.save_total_limit = 2
        print(
            "[diag] Google Drive output detected; defaulting --save-total-limit "
            "to 2 to avoid filling Drive. Pass --save-total-limit 0 to keep all."
        )
    else:
        args.save_total_limit = 0


def configure_dataset_mode(args: argparse.Namespace) -> None:
    """Default non-edit runs to SVGEditBench; synthetic data is opt-in only."""
    if getattr(args, "edit_svg", None) is not None:
        return

    if bool(getattr(args, "synthetic_smoke", False)):
        if getattr(args, "svg_editbench", None) is not None:
            raise SystemExit("Use only one of --synthetic-smoke or --svg-editbench.")
        return

    if getattr(args, "svg_editbench", None) is None:
        args.svg_editbench = Path("SVGEditBench")
        print(
            "[diag] No --svg-editbench supplied; defaulting to SVGEditBench "
            "(use --synthetic-smoke only for generated debug tasks)."
        )


def apply_runtime_memory_defaults(
    args: argparse.Namespace,
    accelerator_runtime: bool | None = None,
) -> None:
    """Apply conservative T4 defaults before model/tokenizer allocation."""
    if accelerator_runtime is None:
        accelerator_runtime = running_in_colab() or bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE"))

    if not accelerator_runtime:
        return
    if not bool(getattr(args, "t4_memory_saver", True)):
        return

    checkpointing = getattr(args, "gradient_checkpointing", None)
    if checkpointing is None:
        args.gradient_checkpointing = True
        max_t4_seq_length = T4_CHECKPOINTING_SEQ_LENGTH
        reason = (
            "enabled reentrant gradient checkpointing and capped --max-seq-length"
        )
    elif bool(checkpointing):
        return
    else:
        max_t4_seq_length = T4_NO_CHECKPOINTING_SEQ_LENGTH
        reason = (
            "capped --max-seq-length because gradient checkpointing is disabled"
        )

    current = int(getattr(args, "max_seq_length", max_t4_seq_length))
    if current <= max_t4_seq_length:
        if checkpointing is None:
            print("[diag] T4 memory saver enabled reentrant gradient checkpointing.")
        return

    args.max_seq_length = max_t4_seq_length
    print(
        f"[diag] T4 memory saver {reason} "
        f"from {current} to {max_t4_seq_length}. "
        "Use --gradient-checkpointing or --no-t4-memory-saver to keep a longer context."
    )


# ── Source pool (stage 0) ─────────────────────────────────────────────────────

def build_source_pool(
    out_dir: Path,
    n_source: int,
    seed: int,
    source_svg_glob: str = "",
    obfuscate_ids: bool = True,
    max_source_chars: int = 6000,
    max_elements: int = 128,
) -> Path:
    rng = random.Random(seed)
    source_dir = out_dir / "00_source_svgs"
    source_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("synthetic_*.svg", "imported_*.svg"):
        for stale in source_dir.glob(pattern):
            stale.unlink()

    records: list[dict[str, Any]] = []
    written = 0
    for i in range(n_source):
        svg = scene_svg(i, rng)
        if obfuscate_ids:
            svg = annotate_synthetic_ids(svg, rng)
        path = source_dir / f"synthetic_{i:05d}.svg"
        path.write_text(svg, encoding="utf-8")
        records.append({
            "path": str(path),
            "source_id": path.name,
            "source_hash": normalized_svg_hash(svg),
            "group_key": structural_fingerprint(svg),
            "origin": "synthetic",
        })
        written += 1

    imported = 0
    rejected = 0
    if source_svg_glob:
        for src in glob.glob(source_svg_glob, recursive=True):
            path = Path(src)
            if not path.is_file() or path.suffix.lower() != ".svg":
                continue
            try:
                text = path.read_text(encoding="utf-8")
                _, recs = parse_svg(text)
                editable = [r for r in recs.values() if r.tag in EDITABLE_TAGS]
                if "<svg" not in text or not editable:
                    rejected += 1
                    continue
                if len(text) > max_source_chars or len(editable) > max_elements:
                    rejected += 1
                    continue
                imported_path = source_dir / f"imported_{imported:05d}_{path.name}"
                imported_path.write_text(text, encoding="utf-8")
                records.append({
                    "path": str(imported_path),
                    "source_id": imported_path.name,
                    "source_hash": normalized_svg_hash(text),
                    "group_key": structural_fingerprint(text),
                    "origin": "imported",
                })
                imported += 1
            except Exception:
                rejected += 1

    manifest = {
        "synthetic_sources": written,
        "imported_sources": imported,
        "rejected_imports": rejected,
        "source_svg_glob": source_svg_glob,
        "obfuscated_synthetic_ids": obfuscate_ids,
        "max_source_chars": max_source_chars,
        "max_elements": max_elements,
    }
    write_jsonl(source_dir / "sources.jsonl", records)
    (source_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Source pool -> {source_dir} ({written} synthetic, {imported} imported, {rejected} rejected)")
    return source_dir


def load_source_records(source_dir: Path) -> list[SourceRecord]:
    manifest_path = source_dir / "sources.jsonl"
    if manifest_path.exists():
        rows = read_jsonl(manifest_path)
        result = []
        for row in rows:
            p = Path(row["path"])
            if not p.exists():
                p = source_dir / row["source_id"]
            if p.exists():
                result.append(SourceRecord(
                    path=p,
                    source_id=str(row["source_id"]),
                    source_hash=str(row["source_hash"]),
                    group_key=str(row["group_key"]),
                    origin=str(row.get("origin", "unknown")),
                ))
        return result
    result = []
    for p in sorted(source_dir.glob("*.svg")):
        src = p.read_text(encoding="utf-8")
        result.append(SourceRecord(
            path=p,
            source_id=p.name,
            source_hash=normalized_svg_hash(src),
            group_key=structural_fingerprint(src),
            origin="unknown",
        ))
    return result


def deduplicate_sources(records: list[SourceRecord]) -> tuple[list[SourceRecord], int]:
    unique: dict[str, SourceRecord] = {}
    for r in records:
        unique.setdefault(r.source_hash, r)
    return list(unique.values()), len(records) - len(unique)


# ── Task generation (stage 1) ─────────────────────────────────────────────────

def split_source_records(
    records: list[SourceRecord],
    n_train: int,
    n_val: int,
    n_eval: int,
    seed: int,
    split_strategy: str,
) -> dict[str, list[SourceRecord]]:
    rng = random.Random(seed)
    records, _ = deduplicate_sources(records)
    if not records:
        raise SystemExit("No usable unique SVG sources.")

    total = max(1, n_train + n_val + n_eval)
    eval_ratio = n_eval / total
    val_ratio = n_val / max(1, n_train + n_val)

    if split_strategy == "group":
        groups: dict[str, list[SourceRecord]] = {}
        for r in records:
            groups.setdefault(r.group_key, []).append(r)
        group_keys = list(groups)
        rng.shuffle(group_keys)
        if len(group_keys) >= 2 and n_eval > 0:
            n_eg = max(1, math.ceil(len(group_keys) * eval_ratio))
            n_eg = min(n_eg, len(group_keys) - 1)
            eval_keys = set(group_keys[:n_eg])
            eval_records = [r for k in eval_keys for r in groups[k]]
            remaining = [r for k in group_keys[n_eg:] for r in groups[k]]
        else:
            eval_records = []
            remaining = records[:]
    elif split_strategy == "source":
        remaining = records[:]
        rng.shuffle(remaining)
        n_es = 0 if n_eval == 0 else max(1, round(len(records) * eval_ratio))
        n_es = min(n_es, max(0, len(records) - 1))
        eval_records = remaining[:n_es]
        remaining = remaining[n_es:]
    else:
        raise ValueError(f"Unknown split strategy {split_strategy!r}")

    rng.shuffle(remaining)
    if n_val > 0 and len(remaining) >= 2:
        n_vs = max(1, round(len(remaining) * val_ratio))
        n_vs = min(n_vs, len(remaining) - 1)
    else:
        n_vs = 0
    val_records = remaining[:n_vs]
    train_records = remaining[n_vs:]

    if n_train and not train_records:
        raise SystemExit("Source split left no training sources.")
    if n_val and not val_records:
        raise SystemExit("Source split left no validation sources.")
    if n_eval and not eval_records:
        raise SystemExit("Source split left no evaluation sources.")
    return {"train": train_records, "val": val_records, "eval": eval_records}


def generate_tasks_for_split(
    split: str,
    records: list[SourceRecord],
    count: int,
    rng: random.Random,
    task_types: tuple[str, ...],
    instruction_mode: str,
    max_tasks_per_source: int,
) -> list[dict[str, Any]]:
    if count == 0:
        return []
    if not records:
        raise SystemExit(f"No source SVGs for {split} split.")
    if count > len(records) * max_tasks_per_source:
        raise SystemExit(
            f"{split}: {count} tasks requested but per-source cap allows "
            f"{len(records) * max_tasks_per_source}. Increase --max-tasks-per-source."
        )

    tasks: list[dict[str, Any]] = []
    per_source: dict[str, int] = {r.source_id: 0 for r in records}
    seen_sigs: dict[str, set[str]] = {r.source_id: set() for r in records}
    attempts = 0
    max_attempts = max(200, count * 100)

    while len(tasks) < count and attempts < max_attempts:
        attempts += 1
        available = [r for r in records if per_source[r.source_id] < max_tasks_per_source]
        if not available:
            break
        record = rng.choice(available)
        try:
            task = make_task_from_source(
                f"{split}_{len(tasks):06d}", record.path, rng,
                source_record=record, task_types=task_types,
                instruction_mode=instruction_mode,
            )
        except Exception:
            continue
        sig = task["target_text"]
        if sig in seen_sigs[record.source_id]:
            continue
        seen_sigs[record.source_id].add(sig)
        per_source[record.source_id] += 1
        task["split"] = split
        tasks.append(task)

    if len(tasks) < count:
        raise SystemExit(
            f"Only built {len(tasks)}/{count} {split} tasks after {attempts} attempts."
        )
    return tasks


def build_patch_tasks(
    source_dir: Path,
    out_dir: Path,
    n_train: int,
    n_eval: int,
    seed: int,
    n_val: int = 0,
    split_strategy: str = "group",
    task_types: str | tuple[str, ...] | list[str] = DEFAULT_TASK_TYPES,
    instruction_mode: str = "semantic",
    max_tasks_per_source: int = 16,
) -> tuple[Path, Path, Path, Path]:
    rng = random.Random(seed)
    tasks_dir = out_dir / "01_tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    source_records = load_source_records(source_dir)
    if not source_records:
        raise SystemExit(f"No SVG source files in {source_dir}")

    unique_records, dup_count = deduplicate_sources(source_records)
    splits = split_source_records(
        unique_records, n_train=n_train, n_val=n_val, n_eval=n_eval,
        seed=seed, split_strategy=split_strategy,
    )
    enabled = parse_task_types(task_types)
    train = generate_tasks_for_split("train", splits["train"], n_train, rng, enabled, instruction_mode, max_tasks_per_source)
    val   = generate_tasks_for_split("val",   splits["val"],   n_val,   rng, enabled, instruction_mode, max_tasks_per_source)
    eval_rows = generate_tasks_for_split("eval", splits["eval"], n_eval, rng, enabled, instruction_mode, max_tasks_per_source)
    tasks = train + val + eval_rows

    all_path   = tasks_dir / "all_tasks.jsonl"
    train_path = tasks_dir / "train_tasks.jsonl"
    val_path   = tasks_dir / "val_tasks.jsonl"
    eval_path  = tasks_dir / "eval_tasks.jsonl"
    write_jsonl(all_path, tasks)
    write_jsonl(train_path, train)
    write_jsonl(val_path, val)
    write_jsonl(eval_path, eval_rows)

    split_hashes = {s: {r.source_hash for r in recs} for s, recs in splits.items()}
    split_groups = {s: {r.group_key   for r in recs} for s, recs in splits.items()}
    audit = {
        "raw_sources": len(source_records),
        "unique_sources": len(unique_records),
        "exact_duplicates_removed": dup_count,
        "split_strategy": split_strategy,
        "task_types": list(enabled),
        "instruction_mode": instruction_mode,
        "source_counts": {s: len(recs) for s, recs in splits.items()},
        "task_counts": {"train": len(train), "val": len(val), "eval": len(eval_rows)},
        "exact_hash_overlap": {
            "train_val":  len(split_hashes["train"] & split_hashes["val"]),
            "train_eval": len(split_hashes["train"] & split_hashes["eval"]),
            "val_eval":   len(split_hashes["val"]   & split_hashes["eval"]),
        },
        "group_overlap": {
            "train_val":  len(split_groups["train"] & split_groups["val"]),
            "train_eval": len(split_groups["train"] & split_groups["eval"]),
            "val_eval":   len(split_groups["val"]   & split_groups["eval"]),
        },
    }
    (tasks_dir / "split_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(
        f"Patch tasks -> {tasks_dir} "
        f"({len(train)} train, {len(val)} val, {len(eval_rows)} eval; "
        f"train/eval group overlap={audit['group_overlap']['train_eval']})"
    )
    return all_path, train_path, val_path, eval_path


# ── SFT data (stage 2) ────────────────────────────────────────────────────────

def build_sft_rows(train_tasks_path: Path, out_dir: Path) -> Path:
    sft_dir = out_dir / "02_sft"
    sft_dir.mkdir(parents=True, exist_ok=True)
    tasks = read_jsonl(train_tasks_path)
    rows = [
        {
            "task_id": row["task_id"],
            "instruction": row["instruction"],
            "input_svg": row["input_svg"],
            "ops": row["ops"],
            "target_text": row["target_text"],
        }
        for row in tasks
    ]
    sft_path = sft_dir / "train_sft.jsonl"
    write_jsonl(sft_path, rows)
    print(f"SFT rows -> {sft_path} ({len(rows)} rows)")
    return sft_path


# ── Metrics (§4) ──────────────────────────────────────────────────────────────

def element_state(source: str) -> dict[str, dict[str, str]]:
    _, records = parse_svg(source)
    return {eid: rec.attrs for eid, rec in records.items()}


def changed_attributes(before: str, after: str) -> dict[tuple[str, str], str | None]:
    before_state = element_state(before)
    after_state  = element_state(after)
    changes: dict[tuple[str, str], str | None] = {}
    for key in set(before_state) | set(after_state):
        ba = before_state.get(key, {})
        aa = after_state.get(key, {})
        for name in set(ba) | set(aa):
            if ba.get(name) != aa.get(name):
                changes[(key, name)] = aa.get(name)
    return changes


def avg(values: list[float | int | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    return None if not clean else sum(clean) / len(clean)


def evaluate_rows(
    rows: list[dict[str, Any]],
    predictions: dict[str, str],
    out_dir: Path,
) -> dict[str, Any]:
    metrics = []
    for row in rows:
        pred = predictions.get(row["task_id"], row["input_svg"])
        expected = changed_attributes(row["input_svg"], row["gold_svg"])
        predicted = changed_attributes(row["input_svg"], pred)
        correct   = {f for f, v in predicted.items() if f in expected and expected[f] == v}
        collateral = set(predicted) - correct
        missed     = set(expected) - correct
        precision = None if not predicted else len(correct) / len(predicted)
        recall    = None if not expected  else len(correct) / len(expected)
        exact_edit = predicted == expected
        structural_integrity = set(element_state(row["input_svg"])) == set(element_state(pred))

        # EP-score (§4.1) — uses targeted_eids from the ground-truth patch
        targeted_eids = set(row.get("targeted_eids", []))
        ep = ep_score(row["input_svg"], pred, targeted_eids)
        if expected:
            target_success = all(
                element_state(pred).get(k, {}).get(n) == v
                for (k, n), v in expected.items()
            )
        else:
            target_success = not predicted

        metrics.append({
            "task_id": row["task_id"],
            "target_success":       1.0 if target_success else 0.0,
            "exact_edit":           1.0 if exact_edit else 0.0,
            "structural_integrity": 1.0 if structural_integrity else 0.0,
            "edit_precision":       precision,
            "edit_recall":          recall,
            "collateral":           len(collateral),
            "missed":               len(missed),
            "ep_recall":            ep["ep_recall"],
            "ep_precision":         ep["ep_precision"],
            "ep_f1":                ep["ep_f1"],
            "untouched_elements":   ep["untouched_elements"],
            "preserved_byte_identical": ep["preserved_byte_identical"],
            "prediction":           pred,
        })

    summary = {
        "n": len(metrics),
        "target_success":       avg([m["target_success"]       for m in metrics]),
        "exact_edit":           avg([m["exact_edit"]           for m in metrics]),
        "structural_integrity": avg([m["structural_integrity"] for m in metrics]),
        "edit_precision":       avg([m["edit_precision"]       for m in metrics]),
        "edit_recall":          avg([m["edit_recall"]          for m in metrics]),
        "collateral":           avg([m["collateral"]           for m in metrics]),
        "missed":               avg([m["missed"]               for m in metrics]),
        "ep_recall":            avg([m["ep_recall"]            for m in metrics]),
        "ep_precision":         avg([m["ep_precision"]         for m in metrics]),
        "ep_f1":                avg([m["ep_f1"]                for m in metrics]),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "metrics.jsonl", metrics)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


# ── Training infrastructure (stage 4) ────────────────────────────────────────

def run_pip_install() -> None:
    # On Colab, system packages live in /usr/local/lib/python3.x/dist-packages/.
    # pip --upgrade installs the new version to a user directory that does NOT
    # shadow the system path, so PEFT still picks up the old torchao==0.10.0.
    # Uninstalling first frees the system slot so the subsequent install wins.
    try:
        _torchao_ver_str = importlib.metadata.version("torchao")
        _torchao_parts = tuple(
            int(p) for p in _torchao_ver_str.split(".")[:3] if p.isdigit()
        )
        if _torchao_parts < (0, 16, 0):
            subprocess.call(
                [sys.executable, "-m", "pip", "uninstall", "-y", "torchao"],
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass

    packages = [
        "transformers>=4.44.0", "accelerate", "datasets",
        "peft", "bitsandbytes>=0.46.1", "sentencepiece",
        "torchao>=0.16.0",
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--upgrade", *packages])
    # Clear importlib path caches so importlib.metadata.version() reads the newly
    # installed package metadata rather than a pre-install cached result.
    importlib.invalidate_caches()
    # Evict stale module entries that may have been loaded before the upgrade.
    # In notebook kernels, transformers can cache PEFT classes inside Trainer;
    # after pip upgrades that cache may no longer match the freshly imported
    # get_peft_model() class, causing the quantized-model training guard to
    # think LoRA was never attached. Removing the HF stack forces fresh imports.
    for _mod in list(sys.modules):
        if _mod == "torchao" or _mod.startswith("torchao.") \
                or _mod == "peft" or _mod.startswith("peft.") \
                or _mod == "transformers" or _mod.startswith("transformers.") \
                or _mod == "accelerate" or _mod.startswith("accelerate.") \
                or _mod == "datasets" or _mod.startswith("datasets.") \
                or _mod == "bitsandbytes" or _mod.startswith("bitsandbytes."):
            del sys.modules[_mod]


def _torchao_ok() -> bool:
    try:
        ver = importlib.metadata.version("torchao")
        return _version_tuple(ver) >= (0, 16, 0)
    except importlib.metadata.PackageNotFoundError:
        return True  # not installed → peft won't complain


def ensure_kaggle_dependencies() -> None:
    if not os.environ.get("KAGGLE_KERNEL_RUN_TYPE") and not running_in_colab():
        return
    required = ("transformers", "accelerate", "datasets", "peft", "sentencepiece")
    missing = [p for p in required if not _pkg_available(p)]
    if missing or not bitsandbytes_4bit_available() or not _torchao_ok():
        print("Installing training dependencies...")
        run_pip_install()


def _pkg_available(name: str) -> bool:
    try:
        importlib.metadata.version(name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def _version_tuple(version: str) -> tuple[int, ...]:
    parts = []
    for piece in re.split(r"[.+-]", version):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            break
    return tuple(parts)


def bitsandbytes_4bit_available() -> bool:
    try:
        version = importlib.metadata.version("bitsandbytes")
    except importlib.metadata.PackageNotFoundError:
        return False
    if _version_tuple(version) < (0, 46, 1):
        return False
    try:
        import bitsandbytes  # noqa: F401
        return True
    except Exception:
        return False


def cuda_is_usable(torch: Any | None = None) -> bool:
    """Return True only when PyTorch can allocate a CUDA tensor."""
    if torch is None:
        try:
            import torch as torch_module  # type: ignore[no-redef]
        except Exception:
            return False
        torch = torch_module
    cuda = getattr(torch, "cuda", None)
    if cuda is None:
        return False
    try:
        if not cuda.is_available():
            return False
    except Exception:
        return False
    try:
        device_count = getattr(cuda, "device_count", lambda: 1)()
        if int(device_count) <= 0:
            return False
    except Exception:
        return False
    try:
        torch.empty(1, device="cuda")
    except Exception:
        return False
    return True


def model_work_requested(args: argparse.Namespace) -> bool:
    """Return True when this invocation will load the language model."""
    if getattr(args, "edit_svg", None) is not None:
        return True
    if bool(getattr(args, "skip_train", False)):
        return False
    return True


def require_cuda_for_model_work(args: argparse.Namespace) -> None:
    """Fail early when a model run is attempted without a visible CUDA GPU."""
    if not model_work_requested(args):
        return
    try:
        import torch
    except Exception as exc:
        raise SystemExit(
            "Training/inference requires PyTorch with CUDA. Install dependencies "
            "with --install-deps/--colab, then restart the runtime."
        ) from exc

    if cuda_is_usable(torch):
        try:
            name = torch.cuda.get_device_name(0)
        except Exception:
            name = "CUDA device 0"
        print(f"[diag] CUDA accelerator visible to PyTorch -> {name}")
        return

    raise SystemExit(
        "No CUDA GPU is visible to PyTorch, or the visible CUDA device cannot "
        "allocate tensors, so QLoRA/bitsandbytes model work cannot run. In "
        "Colab, choose Runtime -> Change runtime type -> T4 GPU or another "
        "CUDA GPU, then restart the runtime and rerun this script. Use "
        "--skip-train only for CPU/no-model smoke tests."
    )


def clear_notebook_exception_state() -> None:
    """Drop notebook traceback references that can keep old CUDA tensors alive."""
    last_tb = getattr(sys, "last_traceback", None)
    if last_tb is not None:
        try:
            import traceback
            traceback.clear_frames(last_tb)
        except Exception:
            pass
    for name in ("last_type", "last_value", "last_traceback"):
        if hasattr(sys, name):
            try:
                setattr(sys, name, None)
            except Exception:
                pass
    try:
        from IPython import get_ipython  # type: ignore[import-not-found]
        shell = get_ipython()
    except Exception:
        shell = None
    if shell is not None:
        for name in ("_", "__", "___"):
            try:
                shell.user_ns[name] = None
            except Exception:
                pass
        for name in ("_last_traceback",):
            if hasattr(shell, name):
                try:
                    setattr(shell, name, None)
                except Exception:
                    pass


def release_cuda_memory(torch: Any | None = None, label: str = "before model load") -> None:
    """Best-effort CUDA cache cleanup for repeated notebook runs."""
    clear_notebook_exception_state()
    gc.collect()
    if torch is None:
        try:
            import torch as torch_module  # type: ignore[no-redef]
        except Exception:
            return
        torch = torch_module
    try:
        if not torch.cuda.is_available():
            return
        torch.cuda.empty_cache()
        if hasattr(torch.cuda, "ipc_collect"):
            torch.cuda.ipc_collect()
        free, total = torch.cuda.mem_get_info()
        print(
            f"[diag] CUDA free {label}: "
            f"{free / (1024 ** 3):.2f} GiB / {total / (1024 ** 3):.2f} GiB"
        )
    except Exception:
        pass


@contextlib.contextmanager
def disable_transformers_allocator_warmup(enabled: bool = True) -> Any:
    """Temporarily skip Transformers' CUDA allocator warmup allocation.

    Recent Transformers versions pre-allocate a large temporary CUDA tensor when
    loading with a device_map. On a 14-16 GB T4 this can OOM even though the
    actual 4-bit model would fit, especially after notebook reruns.
    """
    if not enabled:
        yield
        return
    try:
        import transformers.modeling_utils as modeling_utils
    except Exception:
        yield
        return

    original = getattr(modeling_utils, "caching_allocator_warmup", None)
    if not callable(original):
        yield
        return

    def _noop_caching_allocator_warmup(*_args: Any, **_kwargs: Any) -> None:
        return None

    setattr(modeling_utils, "caching_allocator_warmup", _noop_caching_allocator_warmup)
    print("[diag] Disabled Transformers CUDA allocator warmup for this model load.")
    try:
        yield
    finally:
        setattr(modeling_utils, "caching_allocator_warmup", original)


def stable_model_dtype(torch: Any) -> Any:
    """fp32 compute dtype for the 4-bit (bitsandbytes) path.

    Qwen2.5-Coder's large output vocabulary produced unstable logits in fp16 on
    T4 during 4-bit training. This dtype is passed to BitsAndBytesConfig only.
    """
    return torch.float32


def _model_weight_dtype(using_4bit: bool, torch: Any) -> Any:
    """dtype for from_pretrained weights.

    4-bit path: fp32 keeps non-quantized layers stable (large-vocab softmax).
    Non-4-bit path: fp16 halves peak memory; a 1.5B model in fp32 (~6 GB) OOMs
    on T4 / Colab when bitsandbytes is unavailable. Training and inference must
    use the same dtype to avoid degenerate outputs after checkpoint reload.
    """
    return torch.float32 if using_4bit else torch.float16


def maybe_quantization_config(load_in_4bit: bool, torch: Any) -> Any:
    if not load_in_4bit:
        return None
    if not cuda_is_usable(torch):
        print("CUDA is not usable; falling back to fp16 instead of bitsandbytes 4-bit.")
        return None
    if not bitsandbytes_4bit_available():
        print("bitsandbytes>=0.46.1 not available; falling back to fp16.")
        return None
    from transformers import BitsAndBytesConfig
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=stable_model_dtype(torch),
        bnb_4bit_use_double_quant=True,
    )


def resolve_training_optim(args: argparse.Namespace) -> str:
    """Resolve --optim=auto to a memory-friendly optimizer when available."""
    requested = str(getattr(args, "optim", "auto") or "auto")
    if requested != "auto":
        return requested
    if (
        bool(getattr(args, "load_in_4bit", True))
        and cuda_is_usable()
        and bitsandbytes_4bit_available()
    ):
        return "paged_adamw_8bit"
    return "adamw_torch"


def require_trainable_params_on_cuda(model: Any, label: str) -> None:
    """Fail before Trainer when LoRA/optimizer tensors are not on CUDA."""
    bad: list[tuple[str, str]] = []
    for name, param in model.named_parameters():
        if not getattr(param, "requires_grad", False):
            continue
        device = getattr(param, "device", None)
        if getattr(device, "type", None) != "cuda":
            bad.append((name, str(device)))
            if len(bad) >= 8:
                break
    if not bad:
        return
    sample = ", ".join(f"{name} on {device}" for name, device in bad)
    raise RuntimeError(
        f"{label} has trainable parameters on non-CUDA devices: {sample}. "
        "This usually means the runtime is not using a CUDA GPU, or the "
        "model was loaded on CPU. Restart the notebook after selecting a GPU "
        "runtime, then rerun this script."
    )


def configure_greedy_generation(model: Any) -> None:
    """Remove sampling-only defaults inherited from the base model config."""
    generation_config = getattr(model, "generation_config", None)
    if generation_config is None:
        return
    generation_config.do_sample = False
    generation_config.temperature = 1.0
    generation_config.top_p = 1.0
    generation_config.top_k = 50


def _current_peft_model_classes() -> tuple[type, ...]:
    """Return live PEFT model classes, or () when PEFT is unavailable."""
    try:
        from peft import PeftModel
    except Exception:
        return ()
    classes: list[type] = [PeftModel]
    try:
        from peft import PeftMixedModel
        classes.append(PeftMixedModel)
    except Exception:
        pass
    return tuple(classes)


def synchronize_transformers_peft_detection(model: Any) -> bool:
    """Make Transformers' Trainer PEFT check agree with the live PEFT import.

    Colab/Jupyter can retain a pre-upgrade transformers.trainer module while
    PEFT has been re-imported from the upgraded package. Trainer's quantized
    training guard uses isinstance(model, PeftModel); when the cached class is
    stale, a valid LoRA-wrapped model is rejected as a pure quantized base model.
    """
    peft_classes = _current_peft_model_classes()
    if not peft_classes or not isinstance(model, peft_classes):
        return False

    patched_modules: list[str] = []
    for module_name in ("transformers.trainer", "transformers.trainer_utils"):
        module = sys.modules.get(module_name)
        if module is None:
            continue

        if hasattr(module, "PeftModel"):
            setattr(module, "PeftModel", peft_classes[0])
        if len(peft_classes) > 1 and hasattr(module, "PeftMixedModel"):
            setattr(module, "PeftMixedModel", peft_classes[1])

        checker = getattr(module, "_is_peft_model", None)
        detected = False
        if callable(checker):
            try:
                detected = bool(checker(model))
            except Exception:
                detected = False

        if callable(checker) and not detected:
            def _compat_is_peft_model(candidate: Any, _classes: tuple[type, ...] = peft_classes) -> bool:
                return isinstance(candidate, _classes)

            setattr(module, "_is_peft_model", _compat_is_peft_model)
            patched_modules.append(module_name)

    detected_by: list[str] = []
    for module_name in ("transformers.trainer", "transformers.trainer_utils"):
        module = sys.modules.get(module_name)
        checker = getattr(module, "_is_peft_model", None) if module is not None else None
        if callable(checker):
            try:
                if checker(model):
                    detected_by.append(module_name)
            except Exception:
                pass

    if patched_modules:
        print(f"[diag] Refreshed Transformers PEFT detection in: {', '.join(patched_modules)}")
    print(
        "[diag] PEFT wrapper: "
        f"{model.__class__.__module__}.{model.__class__.__name__}; "
        f"Trainer detects PEFT={bool(detected_by)}"
    )
    return bool(detected_by)


def collate_batch(tokenizer: Any, features: list[dict[str, list[int]]]) -> dict[str, Any]:
    import torch
    max_len = max(len(item["input_ids"]) for item in features)
    pad_id = tokenizer.pad_token_id
    batch: dict[str, list] = {"input_ids": [], "attention_mask": [], "labels": []}
    for item in features:
        pad = max_len - len(item["input_ids"])
        batch["input_ids"].append(item["input_ids"] + [pad_id] * pad)
        batch["attention_mask"].append(item["attention_mask"] + [0] * pad)
        batch["labels"].append(item["labels"] + [-100] * pad)
    return {k: torch.tensor(v, dtype=torch.long) for k, v in batch.items()}


def tokenize_sft_rows(
    tokenizer: Any,
    rows: list[dict[str, Any]],
    max_seq_length: int,
) -> list[dict[str, list[int]]]:
    examples = []
    skipped = 0
    eos = tokenizer.eos_token or ""
    for row in rows:
        user_prompt = make_patch_prompt(row["input_svg"], row["instruction"])
        if hasattr(tokenizer, "apply_chat_template"):
            prompt_text = tokenizer.apply_chat_template(
                [{"role": "user", "content": user_prompt}],
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt_text = user_prompt + "\n"
        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        target_ids = tokenizer(row["target_text"] + eos, add_special_tokens=False)["input_ids"]
        if len(prompt_ids) + len(target_ids) > max_seq_length:
            skipped += 1
            continue
        input_ids = prompt_ids + target_ids
        examples.append({
            "input_ids": input_ids,
            "attention_mask": [1] * len(input_ids),
            "labels": [-100] * len(prompt_ids) + target_ids,
        })
    if skipped:
        print(f"Skipped {skipped}/{len(rows)} rows exceeding --max-seq-length.")
    if not examples:
        raise SystemExit("No SFT rows fit within --max-seq-length.")
    return examples


def format_generation_prompt(tokenizer: Any, input_svg: str, instruction: str) -> str:
    """Render the inference prompt, including the assistant-generation cue."""
    prompt = make_patch_prompt(input_svg, instruction)
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
    return prompt + "\n"


def write_failed_prediction(
    row: dict[str, Any],
    pred_dir: Path,
    predictions: dict[str, str],
    payload: dict[str, Any],
) -> None:
    """Write a fail-closed prediction and diagnostic patch JSON."""
    task_id = str(row["task_id"])
    pred_svg = row["input_svg"]
    predictions[task_id] = pred_svg
    (pred_dir / f"{task_id}.svg").write_text(pred_svg, encoding="utf-8")
    (pred_dir / f"{task_id}.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def predict_with_loaded_model(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
    pred_dir: Path,
) -> dict[str, str]:
    import torch
    predictions: dict[str, str] = {}
    pred_dir.mkdir(parents=True, exist_ok=True)
    was_training = model.training
    model.eval()
    prev_padding = tokenizer.padding_side
    tokenizer.padding_side = "left"
    batch_size = max(1, int(getattr(args, "inference_batch_size", 4)))
    logged_first_raw = False
    skipped_too_long = 0

    try:
        for start in range(0, len(rows), batch_size):
            batch_rows = rows[start:start + batch_size]
            fit_rows = []
            texts = []
            for row in batch_rows:
                text = format_generation_prompt(tokenizer, row["input_svg"], row["instruction"])
                prompt_ids = tokenizer(text, add_special_tokens=False)["input_ids"]
                if len(prompt_ids) > args.max_seq_length:
                    skipped_too_long += 1
                    write_failed_prediction(
                        row,
                        pred_dir,
                        predictions,
                        {
                            "error": (
                                f"Prompt is {len(prompt_ids)} tokens, exceeding "
                                f"--max-seq-length {args.max_seq_length}; skipped "
                                "inference rather than truncating the assistant cue."
                            ),
                            "prompt_tokens": len(prompt_ids),
                            "max_seq_length": args.max_seq_length,
                        },
                    )
                    continue
                fit_rows.append(row)
                texts.append(text)
            if not fit_rows:
                continue
            inputs = tokenizer(
                texts, return_tensors="pt", padding=True,
                truncation=False,
            ).to(model.device)
            with torch.inference_mode():
                ids = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            prompt_width = inputs["input_ids"].shape[1]
            for row, generated_ids in zip(fit_rows, ids):
                raw = tokenizer.decode(generated_ids[prompt_width:], skip_special_tokens=True)
                if not logged_first_raw:
                    logged_first_raw = True
                    print(f"[diag] First inference raw output ({len(raw)} chars): {raw[:300]!r}")
                try:
                    ops = extract_json_array(raw)
                    pred_svg = apply_patch(row["input_svg"], ops)
                    patch_out: Any = ops
                except Exception as exc:
                    pred_svg = row["input_svg"]
                    patch_out = {"error": str(exc), "raw": raw}
                predictions[row["task_id"]] = pred_svg
                (pred_dir / f"{row['task_id']}.svg").write_text(pred_svg, encoding="utf-8")
                (pred_dir / f"{row['task_id']}.json").write_text(
                    json.dumps(patch_out, indent=2), encoding="utf-8"
                )
    finally:
        tokenizer.padding_side = prev_padding

    if skipped_too_long:
        print(
            f"[diag] Skipped {skipped_too_long}/{len(rows)} inference rows whose "
            "prompts exceeded --max-seq-length without truncation."
        )

    if was_training:
        model.train()
    return predictions


def save_epoch_artifacts(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
    label: str,
) -> Path:
    epoch_dir = args.output_dir / "04_model" / "epoch_outputs" / label
    checkpoint_dir = epoch_dir / "checkpoint"
    pred_dir  = epoch_dir / "svgs"
    eval_dir  = epoch_dir / "eval"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(checkpoint_dir))
    tokenizer.save_pretrained(str(checkpoint_dir))
    preds = predict_with_loaded_model(model, tokenizer, rows, args, pred_dir)
    summary = evaluate_rows(rows, preds, eval_dir)
    summary["method"] = label
    (eval_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    zip_dir(pred_dir, epoch_dir / f"{label}_svgs.zip")
    zip_dir(checkpoint_dir, epoch_dir / f"{label}_checkpoint.zip")
    print(f"Saved {label} checkpoint -> {checkpoint_dir}")
    return epoch_dir


def latest_trainer_checkpoint(trainer_dir: Path) -> Path | None:
    """Return the highest-step Trainer checkpoint under trainer_dir, if any."""
    checkpoints: list[tuple[int, Path]] = []
    if not trainer_dir.exists():
        return None
    for path in trainer_dir.glob("checkpoint-*"):
        if not path.is_dir():
            continue
        m = re.fullmatch(r"checkpoint-(\d+)", path.name)
        if not m:
            continue
        checkpoints.append((int(m.group(1)), path))
    return max(checkpoints, default=(0, None))[1]


def _file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def trainer_run_fingerprint(
    args: argparse.Namespace,
    train_path: Path,
    val_path: Path,
    train_examples: int,
    val_examples: int,
) -> dict[str, Any]:
    """Return the data/run identity used to decide whether auto-resume is safe."""
    return {
        "version": 1,
        "prompt_format_version": PROMPT_FORMAT_VERSION,
        "model": str(getattr(args, "model", "")),
        "svg_editbench": str(getattr(args, "svg_editbench", "") or ""),
        "synthetic_smoke": bool(getattr(args, "synthetic_smoke", False)),
        "max_seq_length": int(getattr(args, "max_seq_length", 0)),
        "lora_r": int(getattr(args, "lora_r", 0)),
        "lora_alpha": int(getattr(args, "lora_alpha", 0)),
        "train_path": str(train_path),
        "train_sha256": _file_sha256(train_path),
        "train_examples_after_token_filter": train_examples,
        "val_path": str(val_path),
        "val_sha256": _file_sha256(val_path),
        "val_examples_after_token_filter": val_examples,
    }


def _fingerprint_path(directory: Path) -> Path:
    return directory / TRAINER_FINGERPRINT_FILE


def write_trainer_run_fingerprint(directory: Path, fingerprint: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    _fingerprint_path(directory).write_text(
        json.dumps(fingerprint, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def read_trainer_run_fingerprint(directory: Path) -> dict[str, Any] | None:
    path = _fingerprint_path(directory)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def latest_compatible_trainer_checkpoint(
    trainer_dir: Path,
    fingerprint: dict[str, Any],
) -> Path | None:
    """Return highest-step checkpoint stamped for this exact data/run."""
    checkpoints: list[tuple[int, Path]] = []
    if not trainer_dir.exists():
        return None
    for path in trainer_dir.glob("checkpoint-*"):
        if not path.is_dir():
            continue
        m = re.fullmatch(r"checkpoint-(\d+)", path.name)
        if not m:
            continue
        if read_trainer_run_fingerprint(path) == fingerprint:
            checkpoints.append((int(m.group(1)), path))
    return max(checkpoints, default=(0, None))[1]


def resolve_resume_checkpoint(
    args: argparse.Namespace,
    run_fingerprint: dict[str, Any] | None = None,
) -> Path | None:
    """Resolve explicit or automatic Trainer checkpoint resume target."""
    trainer_dir = args.output_dir / "04_model" / "trainer"
    requested = str(getattr(args, "resume_from_checkpoint", "") or "").strip()
    if requested:
        if requested.lower() == "latest":
            checkpoint = latest_trainer_checkpoint(trainer_dir)
            if checkpoint is None:
                raise SystemExit(f"--resume-from-checkpoint latest found no checkpoints in {trainer_dir}")
            if run_fingerprint is not None and read_trainer_run_fingerprint(checkpoint) != run_fingerprint:
                print(
                    "[diag] Explicit --resume-from-checkpoint latest does not match "
                    "the current data/run fingerprint; resuming anyway because it "
                    "was explicitly requested."
                )
            return checkpoint

        path = Path(requested).expanduser()
        candidates = [path]
        if not path.is_absolute():
            candidates.append(trainer_dir / path)
        for candidate in candidates:
            if candidate.is_dir():
                if run_fingerprint is not None and read_trainer_run_fingerprint(candidate) != run_fingerprint:
                    print(
                        "[diag] Explicit --resume-from-checkpoint target does not "
                        "match the current data/run fingerprint; resuming anyway "
                        "because it was explicitly requested."
                    )
                return candidate
        raise SystemExit(f"--resume-from-checkpoint does not exist: {requested}")

    if getattr(args, "no_auto_resume", False):
        return None

    if run_fingerprint is None:
        return latest_trainer_checkpoint(trainer_dir)

    checkpoint = latest_compatible_trainer_checkpoint(trainer_dir, run_fingerprint)
    if checkpoint is not None:
        return checkpoint
    if latest_trainer_checkpoint(trainer_dir) is not None:
        print(
            "[diag] Existing Trainer checkpoints do not match the current "
            "data/run fingerprint; starting from the base model. Use "
            "--resume-from-checkpoint latest to force reuse."
        )
    return None


def train_model(args: argparse.Namespace, train_path: Path, val_path: Path) -> None:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer,
        EarlyStoppingCallback, Trainer, TrainerCallback, TrainingArguments,
    )

    if not cuda_is_usable(torch):
        raise RuntimeError(
            "Training requires a usable CUDA GPU. PyTorch could not allocate a "
            "CUDA tensor; select a GPU runtime, restart the notebook, and rerun."
        )

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = maybe_quantization_config(args.load_in_4bit, torch)
    using_4bit = quantization_config is not None

    release_cuda_memory(torch, "before training model load")
    with disable_transformers_allocator_warmup(torch.cuda.is_available()):
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            dtype=_model_weight_dtype(using_4bit, torch),
            device_map={"": 0} if torch.cuda.is_available() else None,  # pin to GPU 0; "auto" triggers DataParallel which breaks 4-bit LoRA
            quantization_config=quantization_config,
            attn_implementation="eager",   # sdpa causes indefinite hangs on this server
            trust_remote_code=True,
            low_cpu_mem_usage=True,        # load shards directly to device; avoids staging full fp32 model in CPU RAM
        )
    release_cuda_memory(torch, "after training model load")
    use_gradient_checkpointing = bool(getattr(args, "gradient_checkpointing", False))
    gradient_checkpointing_kwargs = {
        "use_reentrant": bool(getattr(args, "gradient_checkpointing_use_reentrant", True))
    }
    if using_4bit:
        prepare_kwargs: dict[str, Any] = {
            "use_gradient_checkpointing": use_gradient_checkpointing,
        }
        if use_gradient_checkpointing:
            try:
                prepare_params = inspect.signature(prepare_model_for_kbit_training).parameters
            except (TypeError, ValueError):
                prepare_params = {}
            if "gradient_checkpointing_kwargs" in prepare_params:
                prepare_kwargs["gradient_checkpointing_kwargs"] = gradient_checkpointing_kwargs
        model = prepare_model_for_kbit_training(model, **prepare_kwargs)
    if hasattr(model, "config"):
        model.config.use_cache = False
    if use_gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
        try:
            model.gradient_checkpointing_enable(
                gradient_checkpointing_kwargs=gradient_checkpointing_kwargs
            )
        except TypeError:
            model.gradient_checkpointing_enable()
        mode = "reentrant" if gradient_checkpointing_kwargs["use_reentrant"] else "non-reentrant"
        print(f"[diag] Model gradient checkpointing enabled ({mode}).")
    else:
        print("[diag] Model gradient checkpointing disabled.")

    lora = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora)
    require_trainable_params_on_cuda(model, "LoRA patch editor")
    trainer_sees_peft = synchronize_transformers_peft_detection(model)
    model.print_trainable_parameters()
    if using_4bit and not trainer_sees_peft:
        raise RuntimeError(
            "LoRA adapters were attached, but Transformers Trainer still does "
            "not recognize the model as a PEFT model. Restart the notebook "
            "runtime once, then rerun with --install-deps/--colab so the "
            "upgraded transformers and peft modules are imported together."
        )

    rows = read_jsonl(train_path)
    tokenized = tokenize_sft_rows(tokenizer, rows, args.max_seq_length)
    dataset = Dataset.from_list(tokenized)
    val_rows = read_jsonl(val_path) if val_path.exists() else []
    val_tokenized = tokenize_sft_rows(tokenizer, val_rows, args.max_seq_length) if val_rows else []
    val_dataset = Dataset.from_list(val_tokenized) if val_tokenized else None
    outer_tokenizer = tokenizer
    run_fingerprint = trainer_run_fingerprint(
        args,
        train_path,
        val_path,
        train_examples=len(tokenized),
        val_examples=len(val_tokenized),
    )

    class FirstStepLossCallback(TrainerCallback):
        """Print the first few logged loss values — on_log fires when logging_steps elapses."""
        _count: int = 0

        def on_log(self, cb_args: Any, state: Any, control: Any, logs: Any = None, **kwargs: Any) -> Any:
            if self._count < 3 and logs and "loss" in logs:
                self._count += 1
                print(f"[diag] Step {state.global_step}: training loss = {logs['loss']}"
                      f"  (nan here = forward-pass overflow; adjust dtype/fp16)")
            return control

    class EpochArtifactCallback(TrainerCallback):
        def __init__(self) -> None:
            self.saved_labels: set[str] = set()

        def on_epoch_end(self, trainer_args: Any, state: Any, control: Any, model: Any = None, **kwargs: Any) -> Any:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            cb_tok = kwargs.get("tokenizer") or kwargs.get("processing_class") or outer_tokenizer
            if not args.predict_each_epoch or model is None or cb_tok is None:
                return control
            epoch = state.epoch if state.epoch is not None else 0.0
            label = f"epoch_{epoch:.2f}".replace(".", "_")
            if label in self.saved_labels:
                return control
            self.saved_labels.add(label)
            save_epoch_artifacts(model, cb_tok, val_rows, args, label)
            return control

    class TrainerFingerprintCallback(TrainerCallback):
        def on_save(self, trainer_args: Any, state: Any, control: Any, **kwargs: Any) -> Any:
            checkpoint_dir = Path(trainer_args.output_dir) / f"checkpoint-{state.global_step}"
            write_trainer_run_fingerprint(checkpoint_dir, run_fingerprint)
            return control

    has_validation = val_dataset is not None
    save_steps = int(getattr(args, "save_steps", 25))
    save_strategy = "steps" if save_steps > 0 else "epoch"
    save_total_limit = int(getattr(args, "save_total_limit", 0))
    training_optim = resolve_training_optim(args)
    print(f"[diag] Trainer optimizer: {training_optim}")
    training_kwargs: dict[str, Any] = dict(
        output_dir=str(args.output_dir / "04_model" / "trainer"),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        warmup_steps=10,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps if args.max_steps > 0 else -1,
        logging_steps=5,
        save_strategy=save_strategy,
        save_steps=save_steps if save_strategy == "steps" else 500,
        save_total_limit=None if save_total_limit <= 0 else save_total_limit,
        load_best_model_at_end=has_validation,
        metric_for_best_model="eval_loss" if has_validation else None,
        greater_is_better=False if has_validation else None,
        report_to=[],
        optim=training_optim,
        fp16=False,                     # fp16 AMP caused NaN loss (large-vocab softmax overflow); model runs in fp32
        prediction_loss_only=True,
        eval_accumulation_steps=1,
        remove_unused_columns=False,
    )
    eval_value = save_strategy if has_validation else "no"
    if has_validation and save_strategy == "steps":
        training_kwargs["eval_steps"] = save_steps
    params = inspect.signature(TrainingArguments.__init__).parameters
    if "gradient_checkpointing" in params:
        training_kwargs["gradient_checkpointing"] = use_gradient_checkpointing
    if use_gradient_checkpointing and "gradient_checkpointing_kwargs" in params:
        training_kwargs["gradient_checkpointing_kwargs"] = gradient_checkpointing_kwargs
    if "eval_strategy" in params:
        training_kwargs["eval_strategy"] = eval_value
    elif "evaluation_strategy" in params:
        training_kwargs["evaluation_strategy"] = eval_value
    else:
        print("Warning: Transformers exposes no evaluation strategy argument; disabling.")
        training_kwargs.update(load_best_model_at_end=False, metric_for_best_model=None, greater_is_better=None)
        has_validation = False

    train_args = TrainingArguments(**training_kwargs)
    callbacks: list[Any] = [
        FirstStepLossCallback(),
        EpochArtifactCallback(),
        TrainerFingerprintCallback(),
    ]
    if has_validation and args.early_stopping_patience > 0:
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=args.early_stopping_patience))

    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=dataset,
        eval_dataset=val_dataset,
        data_collator=lambda features: collate_batch(tokenizer, features),
        callbacks=callbacks,
    )
    trainer_root = args.output_dir / "04_model" / "trainer"
    write_trainer_run_fingerprint(trainer_root, run_fingerprint)
    resume_checkpoint = resolve_resume_checkpoint(args, run_fingerprint)
    if resume_checkpoint is not None:
        print(f"Resuming Trainer from checkpoint -> {resume_checkpoint}")
    trainer.train(resume_from_checkpoint=str(resume_checkpoint) if resume_checkpoint else None)
    args.ckpt_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.ckpt_dir))
    tokenizer.save_pretrained(str(args.ckpt_dir))
    write_trainer_run_fingerprint(args.ckpt_dir, run_fingerprint)
    print(f"Saved LoRA patch editor -> {args.ckpt_dir}")
    epoch_outputs = args.output_dir / "04_model" / "epoch_outputs"
    if epoch_outputs.exists():
        zip_dir(epoch_outputs, args.output_dir / "05_reports" / "epoch_outputs_all.zip")


def load_for_inference(model_path: Path, base_model: str, load_in_4bit: bool) -> tuple[Any, Any]:
    import torch
    from peft import AutoPeftModelForCausalLM
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not cuda_is_usable(torch):
        raise RuntimeError(
            "Inference requires a usable CUDA GPU. PyTorch could not allocate a "
            "CUDA tensor; select a GPU runtime, restart the notebook, and rerun."
        )

    tok_path = str(model_path) if model_path.exists() else base_model
    tokenizer = AutoTokenizer.from_pretrained(tok_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = maybe_quantization_config(load_in_4bit, torch)
    using_4bit = quantization_config is not None
    common_kwargs = dict(
        # dtype must match train_model for checkpoint reload; _model_weight_dtype
        # returns fp32 in the 4-bit path (stable softmax) and fp16 otherwise
        # (avoids OOM when bitsandbytes is unavailable on Colab/T4).
        dtype=_model_weight_dtype(using_4bit, torch),
        device_map={"": 0} if torch.cuda.is_available() else None,  # pin to GPU 0; "auto" triggers DataParallel
        quantization_config=quantization_config,
        attn_implementation="eager",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    release_cuda_memory(torch, "before inference model load")
    with disable_transformers_allocator_warmup(torch.cuda.is_available()):
        if (model_path / "adapter_config.json").exists():
            model = AutoPeftModelForCausalLM.from_pretrained(str(model_path), **common_kwargs)
        else:
            model = AutoModelForCausalLM.from_pretrained(base_model, **common_kwargs)
    release_cuda_memory(torch, "after inference model load")
    configure_greedy_generation(model)
    model.eval()
    return model, tokenizer


def predict_with_model(args: argparse.Namespace, eval_path: Path) -> dict[str, str]:
    rows = read_jsonl(eval_path)
    model, tokenizer = load_for_inference(args.ckpt_dir, args.model, args.load_in_4bit)
    pred_dir = args.output_dir / "04_model" / "predictions"
    return predict_with_loaded_model(model, tokenizer, rows, args, pred_dir)


def resolve_edit_instruction_arg(args: argparse.Namespace) -> str:
    if args.edit_instruction and args.edit_instruction_file:
        raise SystemExit("Use only one of --edit-instruction or --edit-instruction-file.")
    if args.edit_instruction_file:
        instruction = args.edit_instruction_file.read_text(encoding="utf-8").strip()
    else:
        instruction = (args.edit_instruction or "").strip()
    if not instruction:
        raise SystemExit("--edit-svg requires --edit-instruction or --edit-instruction-file.")
    return instruction


def edit_single_svg_with_model(args: argparse.Namespace) -> Path:
    """Apply the trained patch editor to one user-provided SVG/instruction pair."""
    input_path = args.edit_svg
    if not input_path.exists():
        raise SystemExit(f"--edit-svg does not exist: {input_path}")
    source = input_path.read_text(encoding="utf-8")
    instruction = resolve_edit_instruction_arg(args)

    output_svg = args.edit_output_svg or (
        args.output_dir / "06_custom_outputs" / f"{input_path.stem}_edited.svg"
    )
    output_patch = args.edit_output_patch or output_svg.with_suffix(".patch.json")
    if input_path.resolve() == output_svg.resolve():
        raise SystemExit("--edit-output-svg must not overwrite --edit-svg.")

    adapter_config = args.ckpt_dir / "adapter_config.json"
    if args.reuse_checkpoint and not adapter_config.exists():
        raise SystemExit(f"--reuse-checkpoint requires an existing adapter at {args.ckpt_dir}")
    if not adapter_config.exists():
        print(
            f"Warning: no LoRA adapter found at {args.ckpt_dir}; "
            f"using base model {args.model} for this edit."
        )

    model, tokenizer = load_for_inference(args.ckpt_dir, args.model, args.load_in_4bit)
    pred_dir = args.output_dir / "06_custom_outputs" / "raw_model_outputs"
    rows = [{
        "task_id": "custom_000000",
        "instruction": instruction,
        "input_svg": source,
    }]
    preds = predict_with_loaded_model(model, tokenizer, rows, args, pred_dir)
    edited_svg = preds["custom_000000"]

    output_svg.parent.mkdir(parents=True, exist_ok=True)
    output_patch.parent.mkdir(parents=True, exist_ok=True)
    output_svg.write_text(edited_svg, encoding="utf-8")

    raw_patch_path = pred_dir / "custom_000000.json"
    if raw_patch_path.exists():
        output_patch.write_text(raw_patch_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        output_patch.write_text(json.dumps({"error": "missing model patch output"}, indent=2), encoding="utf-8")

    prompt_path = output_svg.with_suffix(".prompt.txt")
    prompt_path.write_text(instruction + "\n", encoding="utf-8")
    print(f"Edited SVG -> {output_svg}")
    print(f"Patch JSON -> {output_patch}")
    print(f"Instruction -> {prompt_path}")
    return output_svg


# ── Baselines (stage 3) ───────────────────────────────────────────────────────

def oracle_predictions(eval_path: Path) -> dict[str, str]:
    result = {}
    for row in read_jsonl(eval_path):
        try:
            result[row["task_id"]] = apply_patch(row["input_svg"], row["ops"])
        except Exception:
            result[row["task_id"]] = row["input_svg"]
    return result


def noop_predictions(eval_path: Path) -> dict[str, str]:
    return {row["task_id"]: row["input_svg"] for row in read_jsonl(eval_path)}


def instruction_copy_predictions(eval_path: Path) -> dict[str, str]:
    """Parse direct-style instructions ('For element id `X`, set fill to Y.') into ops."""
    predictions: dict[str, str] = {}
    direct_re = re.compile(r"For element(?:\s+id)?\s+`([^`]+)`,\s+(.+)\.")
    op_re = re.compile(r"set\s+([\w:-]+)\s+to\s+([^,]+?)(?=\s+and\s+set\s+|$)")
    for row in read_jsonl(eval_path):
        source = row["input_svg"]
        ops: list[dict[str, Any]] | None = None
        m = direct_re.fullmatch(row["instruction"])
        if m:
            target_id, details = m.groups()
            # Determine eid from target_id
            _, records = parse_svg(source)
            eid = f"#{target_id}" if f"#{target_id}" in records else target_id
            attrs = {a: v.strip() for a, v in op_re.findall(details)}
            if attrs and eid in records:
                ops = [{"op": "set", "eid": eid, "attrs": attrs}]
        try:
            predictions[row["task_id"]] = apply_patch(source, ops) if ops else source
        except Exception:
            predictions[row["task_id"]] = source
    return predictions


def drifted_global_predictions(eval_path: Path, seed: int) -> dict[str, str]:
    """Oracle patch + one additional spurious edit (tests collateral damage detection)."""
    rng = random.Random(seed)
    predictions: dict[str, str] = {}
    for row in read_jsonl(eval_path):
        try:
            pred = apply_patch(row["input_svg"], row["ops"])
        except Exception:
            predictions[row["task_id"]] = row["input_svg"]
            continue
        try:
            extra_ops, _rec, _instr, _et = make_patch_for_source(pred, rng)
            # Avoid re-targeting the same element
            orig_eids = {op.get("eid") for op in row["ops"]}
            if any(op.get("eid") in orig_eids for op in extra_ops):
                extra_ops, _rec, _instr, _et = make_patch_for_source(pred, rng)
            pred = apply_patch(pred, extra_ops)
        except Exception:
            pass
        predictions[row["task_id"]] = pred
    return predictions


def write_predictions(predictions: dict[str, str], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for task_id, svg in predictions.items():
        path = out_dir / f"{task_id}.svg"
        path.write_text(svg, encoding="utf-8")
        rows.append({"task_id": task_id, "prediction": str(path)})
    write_jsonl(out_dir / "predictions.jsonl", rows)


def read_prediction_patches(pred_dir: Path) -> dict[str, Any]:
    """Read model-emitted patch JSON files written beside predicted SVGs."""
    patches: dict[str, Any] = {}
    if not pred_dir.exists():
        return patches
    for path in pred_dir.glob("*.json"):
        try:
            patches[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            patches[path.stem] = {
                "error": f"Could not read predicted patch JSON: {exc}",
                "path": str(path),
            }
    return patches


def run_baselines(eval_path: Path, out_dir: Path, seed: int) -> list[Path]:
    baselines_dir = out_dir / "03_baselines"
    summaries: list[Path] = []
    rows = read_jsonl(eval_path)
    specs = [
        ("noop",             noop_predictions(eval_path)),
        ("instruction_copy", instruction_copy_predictions(eval_path)),
        ("oracle_patch",     oracle_predictions(eval_path)),
        ("drifted_global",   drifted_global_predictions(eval_path, seed + 991)),
    ]
    for name, preds in specs:
        pred_dir   = baselines_dir / name / "predictions"
        report_dir = baselines_dir / name / "eval"
        print(f"\nBaseline: {name}")
        write_predictions(preds, pred_dir)
        summary = evaluate_rows(rows, preds, report_dir)
        summary["method"] = name
        (report_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        summaries.append(report_dir / "summary.json")
    return summaries


# ── Reports (stage 5) ─────────────────────────────────────────────────────────

def format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_comparison(summary_paths: list[Path], out_dir: Path) -> Path:
    reports_dir = out_dir / "05_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    summaries = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in summary_paths if p.exists()
    ]
    lines = [
        "# PatchSVG Pipeline Comparison",
        "",
        "| Method | Target Success | Exact Edit | Attr Precision | Attr Recall | EP-Recall | EP-Precision | EP-F1 | Collateral | Missed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        method = s.get("method", s.get("name", "unknown"))
        lines.append(
            "| `{}` | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                method,
                format_metric(s.get("target_success")),
                format_metric(s.get("exact_edit")),
                format_metric(s.get("edit_precision")),
                format_metric(s.get("edit_recall")),
                format_metric(s.get("ep_recall")),
                format_metric(s.get("ep_precision")),
                format_metric(s.get("ep_f1")),
                format_metric(s.get("collateral")),
                format_metric(s.get("missed")),
            )
        )
    report_path = reports_dir / "comparison.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (reports_dir / "comparison.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))
    return report_path


def zip_dir(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


def write_edit_triplet_bundle(
    rows: list[dict[str, Any]],
    predictions: dict[str, str],
    zip_path: Path,
    bundle_name: str,
    predicted_patches: dict[str, Any] | None = None,
) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    using_predicted_patches = predicted_patches is not None
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for row in rows:
            task_id = str(row["task_id"])
            edited_svg = predictions.get(task_id, row["input_svg"])
            gold_patch = row.get("ops", [])
            patch_payload = (
                predicted_patches.get(
                    task_id,
                    {"error": "missing predicted patch JSON for this task"},
                )
                if predicted_patches is not None else gold_patch
            )
            task_dir = f"tasks/{task_id}"
            archive.writestr(f"{task_dir}/input.svg", row["input_svg"])
            archive.writestr(f"{task_dir}/change_prompt.txt", str(row["instruction"]).strip() + "\n")
            archive.writestr(f"{task_dir}/model_prompt.txt", make_patch_prompt(row["input_svg"], row["instruction"]))
            archive.writestr(f"{task_dir}/patch.json", json.dumps(patch_payload, indent=2))
            if using_predicted_patches:
                archive.writestr(f"{task_dir}/gold_patch.json", json.dumps(gold_patch, indent=2))
            archive.writestr(f"{task_dir}/edited_output.svg", edited_svg)
            manifest_row = {
                "task_id": task_id,
                "change_prompt": row["instruction"],
                "input": f"{task_dir}/input.svg",
                "patch": f"{task_dir}/patch.json",
                "edited_output": f"{task_dir}/edited_output.svg",
                "source_id": row.get("source_id"),
                "edit_type": row.get("edit_type"),
                "targeted_eids": row.get("targeted_eids", []),
            }
            if using_predicted_patches:
                manifest_row["gold_patch"] = f"{task_dir}/gold_patch.json"
            manifest_rows.append(manifest_row)
        manifest = {
            "name": bundle_name,
            "description": "input SVG + change prompt + patch ops + edited output per task",
            "patch_json": "model-predicted patch or error" if using_predicted_patches else "ground-truth patch",
            "task_count": len(manifest_rows),
            "tasks": manifest_rows,
        }
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        patch_line = (
            "tasks/<id>/patch.json        — model-predicted patch ops or error\n"
            "tasks/<id>/gold_patch.json   — ground-truth patch ops\n"
            if using_predicted_patches else
            "tasks/<id>/patch.json        — ground-truth patch ops\n"
        )
        archive.writestr(
            "README.txt",
            f"{bundle_name}\n{'=' * len(bundle_name)}\n\n"
            "tasks/<id>/input.svg        — original SVG\n"
            "tasks/<id>/change_prompt.txt — natural language instruction\n"
            f"{patch_line}"
            "tasks/<id>/edited_output.svg — result after applying the patch\n",
        )
    print(f"Edit triplet bundle -> {zip_path}")
    return zip_path


def bundle_results(out_dir: Path, trained: bool = False) -> Path:
    """Pack all key outputs into a single patchsvg_results.zip at the output root.

    On Kaggle this file appears at the top of the Output tab — one click to download.
    The bundle deliberately omits large intermediate files (individual trainer
    checkpoints, raw SVG prediction folders) and keeps only what you need to
    inspect or report results.
    """
    bundle_path = out_dir / "patchsvg_results.zip"

    def _add(archive: zipfile.ZipFile, path: Path, arcname: str) -> None:
        if path.exists() and path.is_file():
            archive.write(path, arcname)

    def _add_dir(archive: zipfile.ZipFile, src: Path, prefix: str) -> None:
        if src.exists() and src.is_dir():
            for p in sorted(src.rglob("*")):
                if p.is_file():
                    archive.write(p, f"{prefix}/{p.relative_to(src)}")

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as arc:
        # ── Core results ──────────────────────────────────────────────────────
        _add(arc, out_dir / "05_reports" / "comparison.md",   "comparison.md")
        _add(arc, out_dir / "05_reports" / "comparison.json", "comparison.json")
        _add(arc, out_dir / "01_tasks"   / "split_audit.json","split_audit.json")

        # ── Baseline summaries ────────────────────────────────────────────────
        for bl in ("noop", "instruction_copy", "oracle_patch", "drifted_global"):
            _add(arc,
                 out_dir / "03_baselines" / bl / "eval" / "summary.json",
                 f"baselines/{bl}_summary.json")

        # ── Eval task sample (first 20 rows — human-readable spot check) ──────
        eval_tasks_path = out_dir / "01_tasks" / "eval_tasks.jsonl"
        if eval_tasks_path.exists():
            sample_rows = read_jsonl(eval_tasks_path)[:20]
            # Strip the full SVG body to keep the sample small
            slim = [
                {k: v for k, v in row.items() if k not in {"input_svg", "gold_svg"}}
                for row in sample_rows
            ]
            arc.writestr(
                "eval_tasks_sample.jsonl",
                "\n".join(json.dumps(r, ensure_ascii=False) for r in slim) + "\n",
            )

        if trained:
            # ── Trained-model artefacts ───────────────────────────────────────
            _add(arc,
                 out_dir / "04_model" / "eval" / "summary.json",
                 "model/eval_summary.json")
            _add(arc,
                 out_dir / "05_reports" / "final_model_edit_triplets.zip",
                 "model/edit_triplets.zip")
            # Per-epoch eval metrics (lightweight JSON only, not SVG zips)
            epoch_root = out_dir / "04_model" / "epoch_outputs"
            if epoch_root.exists():
                for ep_dir in sorted(epoch_root.iterdir()):
                    summary = ep_dir / "eval" / "summary.json"
                    _add(arc, summary, f"model/epochs/{ep_dir.name}_summary.json")
        else:
            # ── Reference (oracle) edit triplets ─────────────────────────────
            _add(arc,
                 out_dir / "05_reports" / "reference_edit_triplets.zip",
                 "reference/edit_triplets.zip")

        # ── README ────────────────────────────────────────────────────────────
        arc.writestr("README.txt", (
            "PatchSVG Results Bundle\n"
            "=======================\n\n"
            "comparison.md / .json       main metric table (all methods × all metrics)\n"
            "baselines/                  per-baseline summary JSONs\n"
            "model/                      trained-model eval + edit triplets (if trained)\n"
            "model/epochs/               per-epoch eval summaries (if --predict-each-epoch)\n"
            "reference/                  oracle edit triplets (if --skip-train)\n"
            "eval_tasks_sample.jsonl     first 20 eval tasks (instruction + patch + eids)\n"
            "split_audit.json            train/val/eval source-hash and group-overlap report\n\n"
            "Generated by: kaggle_patchsvg_t4_smoke.py\n"
        ))

    size_kb = bundle_path.stat().st_size // 1024
    sep = "=" * 78
    print(f"\n{sep}")
    print(f"  RESULTS BUNDLE  {bundle_path.name}  ({size_kb} KB)")
    print(f"  Full path: {bundle_path}")
    if os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        print("  Kaggle: Output tab  →  patchsvg_results.zip  →  Download")
    print(sep)
    return bundle_path


def write_download_index(out_dir: Path) -> Path:
    reports_dir = out_dir / "05_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    zips = sorted(out_dir.rglob("*.zip"))
    lines = [
        "PatchSVG downloadable artifacts",
        "================================",
        "",
        "PRIMARY DOWNLOAD: patchsvg_results.zip (root of output dir)",
        "",
        "All zip files in this run:",
        "",
    ]
    lines += [str(p) for p in zips] if zips else ["No zip files yet."]
    index_path = reports_dir / "DOWNLOADS.txt"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Download index -> {index_path}")
    return index_path


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kaggle T4 pipeline for a locality-preserving SVG patch editor."
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--colab",
        action="store_true",
        help=(
            "Use Colab defaults: install dependencies, use/clone SVGEditBench, "
            "and write artifacts under /content/patchsvg_svgeditbench unless "
            "--output-dir is supplied."
        ),
    )
    parser.add_argument(
        "--gdrive",
        action="store_true",
        help=(
            "In Colab, mount Google Drive and write artifacts/checkpoints under "
            "--gdrive-dir unless --output-dir is supplied."
        ),
    )
    parser.add_argument(
        "--gdrive-dir",
        type=Path,
        default=DEFAULT_GDRIVE_OUTPUT_DIR,
        help="Default Google Drive output directory for --gdrive.",
    )
    parser.add_argument(
        "--gdrive-force-remount",
        action="store_true",
        help="Pass force_remount=True to google.colab.drive.mount().",
    )
    parser.add_argument(
        "--gdrive-local-fallback",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "If Google Drive mount fails, continue with local /content output "
            "instead of aborting."
        ),
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--n-source", type=int, default=256)
    parser.add_argument("--n-train", type=int, default=512)
    parser.add_argument("--n-val", type=int, default=64)
    parser.add_argument("--n-eval", type=int, default=128)
    parser.add_argument(
        "--svg-editbench",
        type=Path,
        default=None,
        help=(
            "SVGEditBench repo/dataset directory or 2404.13710v1.pdf path. "
            "If omitted, training/eval runs default to ./SVGEditBench and auto-clone "
            "the benchmark repository when needed."
        ),
    )
    parser.add_argument(
        "--synthetic-smoke",
        action="store_true",
        help=(
            "Use generated synthetic SVG edit tasks instead of SVGEditBench. "
            "This is only for local/debug smoke tests."
        ),
    )
    parser.add_argument(
        "--edit-svg",
        type=Path,
        default=None,
        help="Apply a trained patch editor to this SVG file and write an edited SVG.",
    )
    parser.add_argument(
        "--edit-instruction",
        default="",
        help="Natural-language edit instruction for --edit-svg.",
    )
    parser.add_argument(
        "--edit-instruction-file",
        type=Path,
        default=None,
        help="Text file containing the natural-language edit instruction for --edit-svg.",
    )
    parser.add_argument(
        "--edit-output-svg",
        type=Path,
        default=None,
        help="Output path for the edited SVG produced by --edit-svg.",
    )
    parser.add_argument(
        "--edit-output-patch",
        type=Path,
        default=None,
        help="Output path for the predicted patch JSON produced by --edit-svg.",
    )
    parser.add_argument("--source-svg-glob", default="", help="Optional SVG glob, e.g. /kaggle/input/**/*.svg")
    parser.add_argument("--max-source-chars", type=int, default=6000)
    parser.add_argument("--max-elements", type=int, default=128)
    parser.add_argument("--obfuscate-ids", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--split-strategy", choices=("group", "source"), default="group")
    parser.add_argument("--instruction-mode", choices=("semantic", "mixed", "direct"), default="semantic")
    parser.add_argument("--task-types", default=",".join(DEFAULT_TASK_TYPES))
    parser.add_argument("--max-tasks-per-source", type=int, default=16)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-seq-length", type=int, default=3072)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--inference-batch-size", type=int, default=2)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument(
        "--optim",
        default="auto",
        help=(
            "Trainer optimizer. 'auto' uses paged_adamw_8bit when bitsandbytes "
            "is available, otherwise adamw_torch."
        ),
    )
    parser.add_argument(
        "--t4-memory-saver",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "On Colab/Kaggle, apply conservative QLoRA defaults so training "
            "fits on a 14-16 GB T4."
        ),
    )
    parser.add_argument(
        "--gradient-checkpointing",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Enable model activation recomputation to reduce VRAM. Auto-enabled "
            "by the T4 memory saver on Colab/Kaggle unless explicitly disabled."
        ),
    )
    parser.add_argument(
        "--gradient-checkpointing-use-reentrant",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Use reentrant checkpointing when --gradient-checkpointing is enabled. "
            "This avoids the non-reentrant tensor-count check that can fail with QLoRA."
        ),
    )
    parser.add_argument(
        "--save-steps",
        type=int,
        default=25,
        help=(
            "Save a resumable Trainer checkpoint every N optimizer steps. "
            "Use 0 to save only at epoch boundaries."
        ),
    )
    parser.add_argument(
        "--save-total-limit",
        type=int,
        default=-1,
        help=(
            "Maximum Trainer checkpoints to keep. -1 chooses a storage-aware "
            "default, 0 keeps every checkpoint."
        ),
    )
    parser.add_argument(
        "--resume-from-checkpoint",
        default="",
        help=(
            "Resume training from this Trainer checkpoint directory, a checkpoint-* "
            "name under 04_model/trainer, or 'latest'. Empty means auto-resume latest."
        ),
    )
    parser.add_argument(
        "--no-auto-resume",
        action="store_true",
        help="Start training from the base model even if 04_model/trainer/checkpoint-* exists.",
    )
    parser.add_argument("--early-stopping-patience", type=int, default=2)
    parser.add_argument("--load-in-4bit", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--predict-each-epoch", action=argparse.BooleanOptionalAction, default=False)
    training_mode = parser.add_mutually_exclusive_group()
    training_mode.add_argument("--skip-train", action="store_true")
    training_mode.add_argument(
        "--reuse-checkpoint",
        action="store_true",
        help="Skip training and run model evaluation with an existing 04_model/patchsvg_lora adapter.",
    )
    parser.add_argument("--install-deps", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"Ignoring notebook/kernel args: {unknown}")

    configure_persistent_output_dir(args)
    apply_storage_defaults(args)
    if args.colab:
        args.install_deps = True
    configure_dataset_mode(args)

    apply_runtime_memory_defaults(args)

    if args.install_deps:
        run_pip_install()
    else:
        ensure_kaggle_dependencies()

    require_cuda_for_model_work(args)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.ckpt_dir = args.output_dir / "04_model" / "patchsvg_lora"

    if args.edit_svg is not None:
        stage("Single SVG instruction edit")
        edit_single_svg_with_model(args)
        return 0
    if args.edit_instruction or args.edit_instruction_file or args.edit_output_svg or args.edit_output_patch:
        raise SystemExit("--edit-instruction/--edit-output-* require --edit-svg.")

    if args.svg_editbench is not None:
        stage("Step 0: Resolve SVGEditBench dataset")
        svg_editbench_dir = resolve_svgeditbench_dir(args.svg_editbench, args.output_dir)

        stage("Step 1: Convert SVGEditBench edits to patch tasks")
        _all_path, train_tasks_path, val_path, eval_path = build_svgeditbench_tasks(
            svg_editbench_dir, args.output_dir,
            args.n_train, args.n_eval, args.seed + 1,
            n_val=args.n_val,
            split_strategy=args.split_strategy,
        )
    else:
        stage("Step 0: Build SVG source pool")
        source_dir = build_source_pool(
            args.output_dir, args.n_source, args.seed,
            args.source_svg_glob,
            obfuscate_ids=args.obfuscate_ids,
            max_source_chars=args.max_source_chars,
            max_elements=args.max_elements,
        )

        stage("Step 1: Split sources and generate grounded SVG edit tasks")
        _all_path, train_tasks_path, val_path, eval_path = build_patch_tasks(
            source_dir, args.output_dir,
            args.n_train, args.n_eval, args.seed + 1,
            n_val=args.n_val,
            split_strategy=args.split_strategy,
            task_types=args.task_types,
            instruction_mode=args.instruction_mode,
            max_tasks_per_source=args.max_tasks_per_source,
        )

    stage("Step 2: Build SFT rows")
    sft_path = build_sft_rows(train_tasks_path, args.output_dir)

    stage("Step 3: Run diagnostic baselines")
    summary_paths = run_baselines(eval_path, args.output_dir, args.seed + 2)

    if args.skip_train:
        stage("Step 4: Skip model training")
        print("Skipped. Remove --skip-train on Kaggle T4 to run LoRA SFT.")
        eval_rows = read_jsonl(eval_path)
        oracle_preds = oracle_predictions(eval_path)
        write_edit_triplet_bundle(
            eval_rows, oracle_preds,
            args.output_dir / "05_reports" / "reference_edit_triplets.zip",
            "PatchSVG reference input-prompt-patch-output bundle",
        )
        stage("Step 5: Write comparison report and bundle")
        write_comparison(summary_paths, args.output_dir)
        bundle_results(args.output_dir, trained=False)
        write_download_index(args.output_dir)
        return 0

    if args.reuse_checkpoint:
        adapter_config = args.ckpt_dir / "adapter_config.json"
        if not adapter_config.exists():
            raise SystemExit(
                f"--reuse-checkpoint requires an existing adapter at {args.ckpt_dir}"
            )
        stage("Step 4: Reuse existing LoRA patch editor")
        print(f"Using saved adapter -> {args.ckpt_dir}")
    else:
        stage("Step 4: Train LoRA patch editor")
        gc.collect()   # release baseline data (steps 0-3) before the model is loaded
        train_model(args, sft_path, val_path)

    stage("Step 5: Model inference and evaluation")
    preds = predict_with_model(args, eval_path)
    final_pred_dir = args.output_dir / "04_model" / "predictions"
    write_predictions(preds, final_pred_dir)
    zip_dir(final_pred_dir, args.output_dir / "05_reports" / "final_model_svgs.zip")
    eval_rows = read_jsonl(eval_path)
    predicted_patches = read_prediction_patches(final_pred_dir)
    write_edit_triplet_bundle(
        eval_rows, preds,
        args.output_dir / "05_reports" / "final_model_edit_triplets.zip",
        "PatchSVG final model input-prompt-patch-output bundle",
        predicted_patches=predicted_patches,
    )
    model_eval_dir = args.output_dir / "04_model" / "eval"
    model_summary = evaluate_rows(eval_rows, preds, model_eval_dir)
    model_summary["method"] = "patchsvg_lora"
    (model_eval_dir / "summary.json").write_text(json.dumps(model_summary, indent=2), encoding="utf-8")
    summary_paths.append(model_eval_dir / "summary.json")

    stage("Step 6: Write comparison report and bundle")
    write_comparison(summary_paths, args.output_dir)
    bundle_results(args.output_dir, trained=True)
    write_download_index(args.output_dir)
    print(f"\nArtifacts -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0 or "ipykernel" not in sys.modules:
        raise SystemExit(exit_code)
