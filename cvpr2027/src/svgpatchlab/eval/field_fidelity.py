"""Numerical contour audit, with explicit coverage and unsupported-feature status.

Coordinates are root SVG user units, not raster pixels. This checks sampled
geometry, not arbitrary CSS, occlusion, semantic labels, or mathematical truth.
Never interpret ``geometry_pass`` as a complete drawing certificate.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np
from svgpathtools import Arc, Line, Path as SVGPath, parse_path

from svgpatchlab.core.xml import local_name, parse_svg

VERSION = "field-fidelity-v2"
NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?"


def numbers(text: str) -> list[float]:
    if re.sub(NUMBER, "", text).strip(" ,\t\r\n"):
        raise ValueError(f"invalid numeric list: {text[:80]}")
    vals = [float(x) for x in re.findall(NUMBER, text)]
    if not np.isfinite(vals).all():
        raise ValueError("nonfinite numeric list")
    return vals


def transform_matrix(text: str) -> np.ndarray:
    """SVG transform list using column vectors: parent @ local @ point."""
    result = np.eye(3)
    pos = 0
    for m in re.finditer(r"([A-Za-z]+)\s*\(([^()]*)\)", text):
        if text[pos:m.start()].strip(" ,\t\r\n"):
            raise ValueError("malformed SVG transform")
        pos = m.end()
        name, a = m[1], numbers(m[2])
        t = np.eye(3)
        if name == "matrix" and len(a) == 6:
            t = np.array([[a[0], a[2], a[4]], [a[1], a[3], a[5]], [0, 0, 1.]])
        elif name == "translate" and len(a) in (1, 2):
            t[:2, 2] = [a[0], a[1] if len(a) == 2 else 0]
        elif name == "scale" and len(a) in (1, 2):
            t[0, 0], t[1, 1] = a[0], a[-1]
        elif name == "rotate" and len(a) in (1, 3):
            theta = math.radians(a[0]); c, s = math.cos(theta), math.sin(theta)
            t[:2, :2] = [[c, -s], [s, c]]
            if len(a) == 3:
                center = np.array(a[1:]); t[:2, 2] = center - t[:2, :2] @ center
        elif name in ("skewX", "skewY") and len(a) == 1:
            t[0 if name == "skewX" else 1, 1 if name == "skewX" else 0] = math.tan(math.radians(a[0]))
        else:
            raise ValueError(f"unsupported SVG transform: {name}")
        result = result @ t
    if text[pos:].strip(" ,\t\r\n") or not np.isfinite(result).all():
        raise ValueError("malformed SVG transform")
    return result


def element_path(element) -> SVGPath:
    tag, a = local_name(element.tag), element.attrib
    if tag == "path":
        d = a.get("d", "")
        # svgpathtools intentionally tolerates some unknown characters; fail closed.
        if re.sub(NUMBER + r"|[MmLlHhVvCcSsQqTtAaZz]|[\s,]", "", d):
            raise ValueError("invalid path token")
        return parse_path(d)
    if tag in ("polyline", "polygon"):
        v = numbers(a.get("points", ""))
        if len(v) < 4 or len(v) % 2:
            raise ValueError("invalid polyline points")
        pts = [complex(x, y) for x, y in zip(v[::2], v[1::2])]
        if tag == "polygon" and pts[-1] != pts[0]:
            pts.append(pts[0])
        return SVGPath(*[Line(p, q) for p, q in zip(pts, pts[1:])])
    if tag == "line":
        return SVGPath(Line(complex(float(a.get("x1", 0)), float(a.get("y1", 0))),
                            complex(float(a.get("x2", 0)), float(a.get("y2", 0)))))
    if tag in ("circle", "ellipse"):
        cx, cy = float(a.get("cx", 0)), float(a.get("cy", 0))
        rx = float(a.get("r" if tag == "circle" else "rx", 0))
        ry = rx if tag == "circle" else float(a.get("ry", 0))
        if min(rx, ry) <= 0:
            raise ValueError("nonpositive contour radius")
        return parse_path(f"M{cx+rx},{cy} A{rx},{ry} 0 1 0 {cx-rx},{cy} A{rx},{ry} 0 1 0 {cx+rx},{cy}")
    raise ValueError(f"unsupported contour element: {tag}")


def sample_segments(path: SVGPath, matrix: np.ndarray, max_step: float,
                    min_intervals: int = 8, max_points: int = 200_000):
    """Sample with an upper bound on physical speed, including all endpoints.

    For Beziers the derivative lies in the convex hull of derivative control
    points. For arcs use the largest radius and the affine operator norm.
    The resulting sample spacing in physical arc length is at most max_step.
    Trapezoidal weights approximate arc-length integration; no cross-subpath edges.
    """
    if max_step <= 0 or not np.isfinite(max_step):
        raise ValueError("max_step must be positive and finite")
    chunks, weights = [], []
    count = 0
    linear = matrix[:2, :2]
    for seg in path:
        if isinstance(seg, Arc):
            speed = abs(math.radians(seg.delta)) * max(abs(seg.radius.real), abs(seg.radius.imag)) * np.linalg.norm(linear, 2)
        else:
            b = seg.bpoints()
            diff = np.array([[z.real, z.imag] for z in np.diff(b)]) @ linear.T
            speed = (len(b)-1) * np.linalg.norm(diff, axis=1).max()
        if not np.isfinite(speed):
            raise ValueError("nonfinite contour geometry")
        n = max(min_intervals, math.ceil(speed / max_step))
        count += n+1
        if count > max_points:
            raise ValueError("contour exceeds sampling resource limit")
        z = np.array([seg.point(t) for t in np.linspace(0, 1, n+1)])
        points = np.column_stack([z.real, z.imag]) @ linear.T + matrix[:2, 2]
        distances = np.linalg.norm(np.diff(points, axis=0), axis=1)
        w = np.zeros(len(points)); w[:-1] += distances/2; w[1:] += distances/2
        chunks.append(points); weights.append(w)
    if not chunks or sum(w.sum() for w in weights) <= 1e-14:
        raise ValueError("empty or degenerate contour")
    return np.vstack(chunks), np.concatenate(weights)


@dataclass
class Contour:
    node_id: str
    level: float
    points: np.ndarray
    weights: np.ndarray
    issues: list[str]


def extract_contours(svg: str, matrix: np.ndarray, max_step: float):
    root = parse_svg(svg)
    contours, issues = [], []
    if any(local_name(e.tag) in {"style", "script", "use", "foreignObject", "animate", "animateTransform", "set"} for e in root.iter()):
        issues.append("unsupported_dynamic_or_stylesheet_content")
    serial = 0

    def visit(e, parent_matrix, inherited, hidden, branch_issues, in_defs=False):
        nonlocal serial
        serial += 1
        tag = local_name(e.tag); node_id = e.get("id", f"node-{serial}")
        local_issues = list(branch_issues)
        style = dict(inherited)
        for k in ("visibility", "stroke", "fill", "stroke-width", "stroke-opacity", "fill-opacity"):
            if k in e.attrib:
                style[k] = e.attrib[k]
        own = dict(e.attrib)
        for item in e.get("style", "").split(";"):
            if ":" in item:
                k, v = item.split(":", 1); own[k.strip()] = v.strip(); style[k.strip()] = v.strip()
        hidden = hidden or own.get("display") == "none" or own.get("opacity") in {"0", "0.0"}
        in_defs = in_defs or tag in {"defs", "symbol", "clipPath", "mask", "marker"}
        if e is not root and tag == "svg":
            local_issues.append("nested_viewport_not_supported")
        if any(k in own for k in ("clip-path", "mask", "filter")):
            local_issues.append("clipping_mask_or_filter_not_evaluated")
        if "transform" in style or any(k in own for k in ("transform-origin", "transform-box")):
            local_issues.append("css_transform_not_supported")
        try:
            current = parent_matrix @ transform_matrix(e.get("transform", ""))
        except ValueError as exc:
            current = parent_matrix
            local_issues.append(str(exc))
        if "data-level" in e.attrib:
            ci = list(local_issues)
            if hidden or in_defs or style.get("visibility") in {"hidden", "collapse"}:
                ci.append("contour_not_visible")
            try:
                level = float(e.get("data-level"))
                if not math.isfinite(level):
                    raise ValueError("nonfinite contour level")
                points, weights = sample_segments(element_path(e), current, max_step)
                contours.append(Contour(node_id, level, points, weights, ci))
            except (ValueError, AssertionError, IndexError, TypeError, ZeroDivisionError) as exc:
                issues.append(f"{node_id}:invalid_contour:{exc}")
        for child in e:
            visit(child, current, style, hidden, local_issues, in_defs)

    visit(root, matrix, {}, False, [])
    return contours, issues


def interpolate_grid(x, y, field, points):
    """Bilinear interpolation; masked contributors with zero weight are ignored."""
    x, y, field, points = map(np.asarray, (x, y, field, points))
    if field.shape != (len(y), len(x)) or min(len(x), len(y)) < 2:
        raise ValueError("reference dimensions do not agree")
    if not (np.all(np.diff(x) > 0) and np.all(np.diff(y) > 0)):
        raise ValueError("reference coordinates must increase")
    px, py = points.T
    tol = 1e-10 * max(x[-1]-x[0], y[-1]-y[0], 1)
    valid = np.isfinite(points).all(axis=1) & (px >= x[0]-tol) & (px <= x[-1]+tol) & (py >= y[0]-tol) & (py <= y[-1]+tol)
    px, py = np.clip(px, x[0], x[-1]), np.clip(py, y[0], y[-1])
    i = np.clip(np.searchsorted(x, px, side="right")-1, 0, len(x)-2)
    j = np.clip(np.searchsorted(y, py, side="right")-1, 0, len(y)-2)
    tx, ty = (px-x[i])/(x[i+1]-x[i]), (py-y[j])/(y[j+1]-y[j])
    values = np.stack([field[j,i], field[j,i+1], field[j+1,i], field[j+1,i+1]], axis=1)
    w = np.stack([(1-tx)*(1-ty), tx*(1-ty), (1-tx)*ty, tx*ty], axis=1)
    valid &= ((w <= 1e-14) | np.isfinite(values)).all(axis=1)
    result = np.sum(np.where(np.isfinite(values), values, 0)*w, axis=1)
    result[~valid] = np.nan
    return result


def score_svg(svg, x, y, field, mapping=(1, 0, 1, 0), expected_levels=(),
              tolerance_pp=0.5, max_step=None, field_range=None):
    x, y, field = map(np.asarray, (x, y, field))
    ax, bx, ay, by = mapping
    if ax == 0 or ay == 0:
        raise ValueError("singular physical coordinate mapping")
    matrix = np.array([[1/ax, 0, -bx/ax], [0, 1/ay, -by/ay], [0, 0, 1.]])
    max_step = max_step or min(np.diff(x).min(), np.diff(y).min())/2
    span = float(np.nanmax(field)-np.nanmin(field)) if field_range is None else float(field_range)
    if not math.isfinite(span) or span <= 0:
        raise ValueError("positive field range required")
    result = {"version": VERSION, "geometry_pass": False,
              "full_drawing_verified": False, "tolerance_pp": tolerance_pp,
              "field_range": span, "max_sample_spacing_physical": float(max_step),
              "limitations": ["occlusion_not_evaluated", "labels_units_and_legends_not_evaluated", "finite_sampling_not_formal_proof"]}
    try:
        contours, issues = extract_contours(svg, matrix, max_step)
    except ValueError as exc:
        contours, issues = [], [f"invalid_svg:{exc}"]
    rows, errors, lengths = [], [], []
    for c in contours:
        values = interpolate_grid(x, y, field, c.points)
        finite = np.isfinite(values)
        errs = np.abs(values-c.level)
        ci = list(c.issues)
        if not finite.all():
            ci.append("samples_outside_reference_or_masked")
        w = c.weights[finite]
        good = errs[finite]
        mean = float(np.average(good, weights=w)) if w.sum() > 0 else None
        row = {"id": c.node_id, "level": c.level, "points": len(values),
               "valid_points": int(finite.sum()), "invalid_points": int((~finite).sum()),
               "physical_length": float(c.weights.sum()), "issues": ci,
               "mean_abs_err": mean, "mean_error_pp": 100*mean/span if mean is not None else None,
               "max_error_pp": float(100*good.max()/span) if len(good) else None}
        rows.append(row)
        if len(good):
            errors.extend(good.tolist()); lengths.extend(w.tolist())
    found = [c.level for c in contours]
    missing = [float(v) for v in expected_levels if not any(np.isclose(v, f, atol=1e-8, rtol=1e-8) for f in found)]
    if missing:
        issues.append("required_contour_levels_missing")
    if not rows:
        issues.append("no_contours")
    mean = float(np.average(errors, weights=lengths)) if sum(lengths) > 0 else None
    result.update(contours_found=len(rows), per_level=rows, issues=issues,
                  missing_levels=missing, mean_abs_err=mean,
                  mean_error_pp=100*mean/span if mean is not None else None,
                  max_error_pp=float(100*max(errors)/span) if errors else None,
                  invalid_points=sum(r["invalid_points"] for r in rows))
    result["geometry_pass"] = bool(rows and not issues and all(
        not r["issues"] and r["max_error_pp"] is not None and r["max_error_pp"] <= tolerance_pp for r in rows))
    return result
