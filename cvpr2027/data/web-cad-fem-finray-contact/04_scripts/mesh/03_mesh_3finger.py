"""
단일 핀레이 메쉬를 볼 중심 Y축 둘레로 120도씩 돌려 3핑거 배치를 만든다.

볼은 y=0 과 y=60 에서 잘린 R=40 구이므로 대칭축이 **Y축**이다. 따라서 그리퍼
축도 Y이고, 손가락은 Y축 둘레에 120도 간격으로 놓인다. 이 배치가 정리 PDF 4.4절의
"위쪽 방향 +Y(팁 쪽) / -Y(밑동 쪽)" 기술과 일치한다.

Y축 둘레 회전은 y 좌표를 바꾸지 않으므로 **세 손가락의 밑동이 모두 y=0 평면에**
남는다. 덕분에 밑동 선택이 간단하다.

출력: NBLOCK/EBLOCK 하나에 손가락 3개. 손가락 구분용으로 CMBLOCK 도 함께 쓴다.
"""

import argparse
import json
import math
from pathlib import Path

import gmsh
import numpy as np

PROJECT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT / "01_geometry" / "source"
OUT_DIR = PROJECT / "02_mesh" / "msh"

ANGLES_DEG = (0.0, 120.0, 240.0)


def rotate_about_y(pts, center, deg):
    """center 를 지나는 Y축 둘레로 pts 를 deg 만큼 돌린다."""
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    out = pts.copy()
    dx = pts[:, 0] - center[0]
    dz = pts[:, 2] - center[2]
    out[:, 0] = center[0] + dx * c + dz * s
    out[:, 2] = center[2] - dx * s + dz * c
    return out


def mesh_single(step_path, size, shift_x):
    """핀레이 솔리드만 메쉬해 (절점좌표, 사면체연결, 볼정보) 를 돌려준다."""
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        gmsh.model.add(step_path.stem)
        gmsh.model.occ.importShapes(str(step_path))
        gmsh.model.occ.synchronize()

        solids = sorted(((gmsh.model.occ.getMass(3, t), t)
                         for _, t in gmsh.model.getEntities(3)), reverse=True)
        (ball_vol, ball_tag), (fin_vol, fin_tag) = solids
        x0, y0, z0, x1, y1, z1 = gmsh.model.getBoundingBox(3, ball_tag)
        ball = {
            "center": [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2],
            "r_contact": max(x1 - x0, y1 - y0, z1 - z0) / 2,
            "volume_mm3": ball_vol,
        }

        gmsh.model.occ.remove([(3, ball_tag)], recursive=True)
        gmsh.model.occ.synchronize()

        gmsh.option.setNumber("Mesh.MeshSizeMin", size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)   # SOLID285
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.Optimize", 1)
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
        gmsh.model.mesh.generate(3)

        ntags, ncoord, _ = gmsh.model.mesh.getNodes()
        ncoord = np.array(ncoord).reshape(-1, 3)
        order = np.argsort(ntags)
        ntags = np.array(ntags)[order]
        ncoord = ncoord[order]
        remap = {int(t): i + 1 for i, t in enumerate(ntags)}

        etypes, etags, enodes = gmsh.model.mesh.getElements(dim=3)
        tets = None
        for et, _, en in zip(etypes, etags, enodes):
            if et == 4:
                tets = np.array(en).reshape(-1, 4)
        tets = np.vectorize(remap.get)(tets)

        q = np.array(gmsh.model.mesh.getElementQualities(
            etags[list(etypes).index(4)]))

        ncoord[:, 0] += shift_x
        return ncoord, tets, ball, fin_vol, q
    finally:
        gmsh.finalize()


def write_inp(path, nodes, elems, base_sets):
    """NBLOCK/EBLOCK + 손가락별 밑동 컴포넌트를 쓴다."""
    with path.open("w", encoding="ascii", newline="\n") as f:
        f.write("/PREP7\n")
        f.write(f"NBLOCK,6,SOLID,{len(nodes)},{len(nodes)}\n")
        f.write("(3i9,6e21.13e3)\n")
        for i, (x, y, z) in enumerate(nodes, start=1):
            f.write(f"{i:9d}{0:9d}{0:9d}{x:21.13E}{y:21.13E}{z:21.13E}\n")
        f.write(f"N,R5.3,LOC,{-1:9d},\n")

        f.write(f"EBLOCK,19,SOLID,,{len(elems)}\n")
        f.write("(19i9)\n")
        for eid, conn in enumerate(elems, start=1):
            f.write(
                f"{1:9d}{1:9d}{1:9d}{1:9d}{0:9d}{0:9d}{0:9d}{0:9d}"
                f"{4:9d}{0:9d}{eid:9d}"
                + "".join(f"{int(n):9d}" for n in conn) + "\n"
            )
        f.write(f"{-1:9d}\n")

        # 손가락별 밑동 절점 컴포넌트 — 개별 반력(FSUM) 을 뽑을 때 쓴다
        for name, ids in base_sets.items():
            f.write(f"CMBLOCK,{name},NODE,{len(ids)}\n")
            f.write("(8i10)\n")
            for i in range(0, len(ids), 8):
                f.write("".join(f"{int(v):10d}" for v in ids[i:i + 8]) + "\n")
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", default="real15.step")
    ap.add_argument("--size", type=float, default=2.5)
    ap.add_argument("--shift-x", type=float, default=0.2896,
                    help="초기 간극 정규화 평행이동 [mm]")
    args = ap.parse_args()

    step_path = SOURCE_DIR / args.step
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    nodes1, tets1, ball, fin_vol, q = mesh_single(step_path, args.size, args.shift_x)
    n1, e1 = len(nodes1), len(tets1)
    print(f"단일 핀레이  절점 {n1:,}  요소 {e1:,}  품질 최소 {q.min():.4f}")
    print(f"볼 중심 {np.round(ball['center'], 4)}  접촉 반지름 {ball['r_contact']:.3f} mm")
    print(f"볼 체적 {ball['volume_mm3']:,.1f} mm^3 (잘린 형상 — 질량 계산용)")
    print()

    all_nodes, all_elems, base_sets = [], [], {}
    for k, ang in enumerate(ANGLES_DEG):
        nd = rotate_about_y(nodes1, ball["center"], ang)
        all_nodes.append(nd)
        all_elems.append(tets1 + k * n1)
        # 밑동: y ~ 0 인 절점 (Y축 회전이라 세 손가락 모두 y=0 유지)
        base_local = np.where(np.abs(nd[:, 1]) < 1e-6)[0] + 1 + k * n1
        base_sets[f"BASE{k}"] = base_local
        print(f"손가락 {k}  회전 {ang:6.1f}deg   절점 {k*n1+1:,}~{(k+1)*n1:,}"
              f"   밑동 절점 {len(base_local)}")

    nodes = np.vstack(all_nodes)
    elems = np.vstack(all_elems)
    print(f"\n합계  절점 {len(nodes):,}  요소 {len(elems):,}")

    limit = 128000
    print(f"Student 라이선스 한도 {limit:,} 대비 "
          f"절점 {len(nodes)/limit*100:.1f}% / 요소 {len(elems)/limit*100:.1f}%")
    if len(nodes) > limit or len(elems) > limit:
        print("!! 한도 초과 — 요소 크기를 키우거나 형상을 줄일 것")

    inp = OUT_DIR / f"{step_path.stem}_3finger_{args.size}mm.inp"
    write_inp(inp, nodes, elems, base_sets)

    meta = {
        "step": step_path.name,
        "mesh_size_mm": args.size,
        "shift_x_mm": args.shift_x,
        "angles_deg": list(ANGLES_DEG),
        "nodes_per_finger": n1,
        "elements_per_finger": e1,
        "nodes_total": int(len(nodes)),
        "elements_total": int(len(elems)),
        "finray_volume_mm3": round(fin_vol, 3),
        "ball": {
            "center": [round(c, 6) for c in ball["center"]],
            "r_contact_mm": round(ball["r_contact"], 6),
            "volume_mm3": round(ball["volume_mm3"], 3),
            "note": "질량은 volume_mm3 (잘린 형상) 를 쓸 것. "
                    "R=40 완전구로 계산하면 8.6% 과대평가된다.",
        },
        "base_components": {k: len(v) for k, v in base_sets.items()},
    }
    (OUT_DIR / f"{step_path.stem}_3finger_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n저장: {inp.name}")
    print(f"      {step_path.stem}_3finger_meta.json")


if __name__ == "__main__":
    main()
