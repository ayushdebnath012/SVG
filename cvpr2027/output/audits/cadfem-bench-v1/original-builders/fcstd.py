"""Read-only access to FreeCAD .FCStd documents and FreeCAD-written CalculiX decks (no FreeCAD needed)."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import numpy as np


class FCStd:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.zip = zipfile.ZipFile(self.path)
        self.xml = self.zip.read("Document.xml").decode("utf-8")
        i = self.xml.find("<ObjectData")
        self.types = dict((n, t) for t, n in re.findall(r'<Object type="([^"]+)" name="([^"]+)"', self.xml[:i]))
        self.data = {m.group(1): m.group(2) for m in re.finditer(r'<Object name="([^"]+)"[^>]*>(.*?)</Object>', self.xml[i:], re.S)}

    def props(self, obj: str) -> dict:
        out = {}
        for n, t, v in re.findall(r'<Property name="([^"]+)" type="([^"]+)"[^>]*>(.*?)</Property>', self.data.get(obj, ""), re.S):
            out[n] = (t, v)
        return out

    def links(self, obj: str, prop: str = "References") -> list[tuple[str, str]]:
        v = self.props(obj).get(prop, ("", ""))[1]
        return re.findall(r'<Link obj="([^"]+)" sub="([^"]*)"', v)

    def value(self, obj: str, prop: str):
        t, v = self.props(obj).get(prop, ("", ""))
        m = re.search(r'value="([^"]*)"', v)
        return m.group(1) if m else None

    def vector(self, obj: str, prop: str):
        t, v = self.props(obj).get(prop, ("", ""))
        m = re.search(r'valueX="([^"]+)" valueY="([^"]+)" valueZ="([^"]+)"', v)
        return [float(x) for x in m.groups()] if m else None

    def material(self, obj: str) -> dict:
        v = self.props(obj).get("Material", ("", ""))[1]
        return dict(re.findall(r'<Item key="([^"]+)" value="([^"]*)"', v))

    def of_type(self, *suffixes: str) -> list[str]:
        return [n for n, t in self.types.items() if any(t.endswith(s) for s in suffixes)]

    def shape_member(self, obj: str) -> str:
        v = self.props(obj).get("Shape", ("", ""))[1]
        m = re.search(r'file="([^"]+)"', v)
        return m.group(1)

    def extract(self, member: str, dst: Path) -> Path:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(self.zip.read(member))
        return dst


def read_ccx(inp: Path) -> dict:
    """Nodes, named node sets, elastic card, *BOUNDARY entries and per-face CLOAD resultants of a FreeCAD deck."""
    lines = Path(inp).read_text(errors="replace").splitlines()
    nodes, nsets, bnd, face_loads, elastic = {}, {}, [], {}, None
    mode, cur, face = None, None, None
    for ln in lines:
        s = ln.strip()
        if s.startswith("**"):
            m = re.search(r"node loads on shape: (\S+):(Face\d+)", s)
            if m:
                face = m.group(2)
                face_loads.setdefault(face, np.zeros(3))
            continue
        if s.startswith("*"):
            k = s.upper()
            mode = None
            if k.startswith("*NODE") and "PRINT" not in k and "FILE" not in k:
                mode = "node"
            elif k.startswith("*NSET"):
                mode, cur = "nset", re.search(r"NSET=([^,\s]+)", s, re.I).group(1)
                nsets.setdefault(cur, [])
            elif k.startswith("*BOUNDARY"):
                mode = "bnd"
            elif k.startswith("*CLOAD"):
                mode, face = "cload", None
            elif k.startswith("*ELASTIC"):
                mode = "elastic"
            continue
        if not s:
            continue
        p = [x.strip() for x in s.split(",") if x.strip()]
        if mode == "node":
            nodes[int(p[0])] = [float(x) for x in p[1:4]]
        elif mode == "nset":
            nsets[cur] += [int(x) for x in p]
        elif mode == "bnd":
            bnd.append(p)
        elif mode == "cload" and face:
            face_loads[face][int(p[1]) - 1] += float(p[2])
        elif mode == "elastic" and elastic is None:
            elastic = [float(x) for x in p[:2]]
    return dict(nodes=nodes, nsets=nsets, boundary=bnd, face_loads={k: v.tolist() for k, v in face_loads.items()}, elastic=elastic)


def nodes_on_faces(coords: np.ndarray, face_list: list, tol: float = 0.02, sample: int = 80) -> float:
    """Fraction of (sampled) nodes lying within tol mm of the union of the given faces."""
    from OCP.BRep import BRep_Builder
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.TopoDS import TopoDS_Compound
    from OCP.gp import gp_Pnt
    comp, b = TopoDS_Compound(), BRep_Builder()
    b.MakeCompound(comp)
    for f in face_list:
        b.Add(comp, f)
    idx = np.linspace(0, len(coords) - 1, min(sample, len(coords))).astype(int)
    ok = 0
    for i in idx:
        v = BRepBuilderAPI_MakeVertex(gp_Pnt(*map(float, coords[i]))).Vertex()
        d = BRepExtrema_DistShapeShape(v, comp)
        ok += d.Value() <= tol
    return ok / len(idx)
