"""
real15.step 에서 핀레이 솔리드만 뽑아 2.5mm 1차 사면체로 메쉬하고,
MAPDL 이 읽을 수 있는 NBLOCK/EBLOCK 입력 파일로 내보낸다.

STEP 안에는 솔리드가 2개 들어 있다 — 큰 쪽(체적 245,042 mm^3, 3면)이 볼,
작은 쪽이 핀레이다. 볼은 강체 타겟으로 따로 만들 것이므로 여기서는
핀레이만 메쉬하고, 볼은 형상 정보(중심/반지름)만 뽑아 JSON 으로 남긴다.

검증 기준 (PDF 기록):
    15deg  3,044 절점 / 9,846 요소
    25deg  2,939 절점 / 9,102 요소

사용법:
    python 02_mesh_finray.py [--step real15.step] [--size 2.5]
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

# PDF 기록 — 재구축본 대조용
REFERENCE = {
    "real15": {"nodes": 3044, "elements": 9846},
    "real25": {"nodes": 2939, "elements": 9102},
}


def split_solids(step_path: Path):
    """STEP 의 솔리드를 (볼 tag, 핀레이 tag) 로 가른다. 체적이 큰 쪽이 볼."""
    solids = gmsh.model.getEntities(3)
    if len(solids) != 2:
        raise RuntimeError(f"솔리드가 2개가 아니다: {len(solids)}개")
    by_volume = sorted(
        ((gmsh.model.occ.getMass(3, tag), tag) for _, tag in solids),
        reverse=True,
    )
    (ball_vol, ball_tag), (fin_vol, fin_tag) = by_volume
    return (ball_tag, ball_vol), (fin_tag, fin_vol)


def ball_info(tag: int, volume: float) -> dict:
    """볼의 중심과 반지름을 뽑는다. 반지름은 bbox 기준(외접) — 체적 기준이 아니다.

    실제 CAD 볼은 완전구가 아니라서(체적이 R=40 구의 91.4%) 두 반지름이 다르다.
    접촉 계산에는 bbox 반지름을, 질량 계산에는 실제 체적을 써야 한다.
    """
    x0, y0, z0, x1, y1, z1 = gmsh.model.getBoundingBox(3, tag)
    center = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    r_bbox = max(x1 - x0, y1 - y0, z1 - z0) / 2
    r_vol = (volume * 3.0 / (4.0 * math.pi)) ** (1.0 / 3.0)
    return {
        "center": [round(c, 6) for c in center],
        "r_bbox": round(r_bbox, 6),
        "r_equiv_volume": round(r_vol, 6),
        "volume_mm3": round(volume, 3),
        "volume_perfect_sphere_mm3": round(4 / 3 * math.pi * r_bbox**3, 3),
        "note": "실제 CAD 볼은 완전구가 아님. 질량은 volume_mm3 를 쓸 것.",
    }


# gmsh 10절점 사면체 → ANSYS SOLID187 절점 순서
#   gmsh 모서리절점: 4=(0,1) 5=(1,2) 6=(0,2) 7=(0,3) 8=(2,3) 9=(1,3)
#   ANSYS:  M=(I,J) N=(J,K) O=(K,I) P=(I,L) Q=(J,L) R=(K,L)
#   → 마지막 두 개(Q,R)의 순서가 gmsh 와 반대다
GMSH_TET10_TO_ANSYS = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]


def write_mapdl_block(path: Path, nodes: np.ndarray, elems: np.ndarray) -> None:
    """NBLOCK/EBLOCK 형식 APDL 입력 파일로 쓴다.

    N/EN 명령을 한 줄씩 보내는 것보다 훨씬 빠르고, /INPUT 한 번으로 읽힌다.
    EBLOCK 의 SOLID 형식은 앞에 11개 정수 필드가 붙는다:
      MAT, TYPE, REAL, SECT, CSYS, DEATH, SOLIDMODEL, SHAPE, NNODES, EXCL, ELEMID

    4절점(1차)과 10절점(2차) 사면체를 모두 지원한다. 10절점이면 한 줄에 19개
    제한을 넘으므로(11+10=21) 절점 8개까지만 첫 줄에 쓰고 나머지는 다음 줄로 넘긴다.
    """
    nn = elems.shape[1]
    if nn == 10:
        elems = elems[:, GMSH_TET10_TO_ANSYS]

    with path.open("w", encoding="ascii", newline="\n") as f:
        f.write("/PREP7\n")

        # --- 절점 ---
        f.write(f"NBLOCK,6,SOLID,{len(nodes)},{len(nodes)}\n")
        f.write("(3i9,6e21.13e3)\n")
        for i, (x, y, z) in enumerate(nodes, start=1):
            f.write(f"{i:9d}{0:9d}{0:9d}"
                    f"{x:21.13E}{y:21.13E}{z:21.13E}\n")
        f.write(f"N,R5.3,LOC,{-1:9d},\n")

        # --- 요소 ---
        # EBLOCK, NUM_NODES, Solkey, --, NUM_ELEM
        # 3번째 필드는 미사용이므로 반드시 비워야 한다. 값을 넣으면 블록 읽기
        # 모드로 들어가지 않고 데이터 줄이 전부 명령으로 해석된다.
        f.write(f"EBLOCK,19,SOLID,,{len(elems)}\n")
        f.write("(19i9)\n")
        for eid, conn in enumerate(elems, start=1):
            head = (f"{1:9d}{1:9d}{1:9d}{1:9d}{0:9d}{0:9d}{0:9d}{0:9d}"
                    f"{nn:9d}{0:9d}{eid:9d}")
            first = conn[:8] if nn > 8 else conn
            f.write(head + "".join(f"{int(n):9d}" for n in first) + "\n")
            if nn > 8:
                f.write("".join(f"{int(n):9d}" for n in conn[8:]) + "\n")
        f.write(f"{-1:9d}\n")
        f.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", default="real15.step")
    ap.add_argument("--size", type=float, default=2.5,
                    help="목표 요소 크기 [mm] (기본 2.5 — PDF 와 동일)")
    ap.add_argument("--order", type=int, default=1, choices=(1, 2),
                    help="요소 차수. 1=SOLID285(4절점), 2=SOLID187(10절점). "
                         "얇은 리브의 큰 휨에서는 2차가 요소 뒤집힘에 훨씬 강하다.")
    ap.add_argument("--shift-x", type=float, default=0.0,
                    help="핀레이를 +X 로 평행이동 [mm]. 초기 간극 정규화용. "
                         "real15 는 CAD 간극 1.0246mm 이므로 0.2896 을 주면 "
                         "PDF 기준인 0.735mm 가 된다.")
    args = ap.parse_args()

    step_path = SOURCE_DIR / args.step
    if not step_path.exists():
        print(f"STEP 파일이 없다: {step_path}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = step_path.stem

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        gmsh.model.add(stem)
        gmsh.model.occ.importShapes(str(step_path))
        gmsh.model.occ.synchronize()

        (ball_tag, ball_vol), (fin_tag, fin_vol) = split_solids(step_path)
        print(f"볼      solid {ball_tag}  체적 {ball_vol:12,.1f} mm^3")
        print(f"핀레이  solid {fin_tag}  체적 {fin_vol:12,.1f} mm^3")

        ball = ball_info(ball_tag, ball_vol)
        print(f"볼 중심 {ball['center']}  bbox 반지름 {ball['r_bbox']:.3f} mm")

        # 볼을 지우고 핀레이만 남긴다
        gmsh.model.occ.remove([(3, ball_tag)], recursive=True)
        gmsh.model.occ.synchronize()

        # --- 메쉬 ---
        gmsh.option.setNumber("Mesh.MeshSizeMin", args.size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", args.size)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.ElementOrder", args.order)
        gmsh.option.setNumber("Mesh.HighOrderOptimize", 1 if args.order == 2 else 0)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)       # Delaunay
        gmsh.option.setNumber("Mesh.Optimize", 1)
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
        gmsh.model.mesh.generate(3)

        # --- 절점 ---
        ntags, ncoord, _ = gmsh.model.mesh.getNodes()
        ncoord = np.array(ncoord).reshape(-1, 3)
        order = np.argsort(ntags)
        ntags = np.array(ntags)[order]
        ncoord = ncoord[order]
        remap = {int(t): i + 1 for i, t in enumerate(ntags)}   # 1부터 재번호

        # --- 요소 (gmsh type 4 = tet4, 11 = tet10) ---
        want_type, nn = (4, 4) if args.order == 1 else (11, 10)
        etypes, etags, enodes = gmsh.model.mesh.getElements(dim=3)
        tets = qual_tags = None
        for et, tg, en in zip(etypes, etags, enodes):
            if et == want_type:
                tets = np.array(en).reshape(-1, nn)
                qual_tags = tg
        if tets is None:
            raise RuntimeError(f"{nn}절점 사면체가 생성되지 않았다")
        tets = np.vectorize(remap.get)(tets)

        # 초기 간극 정규화 — 핀레이를 볼 쪽(+X)으로 당긴다.
        # numpy 배열만 옮기면 .inp 에는 반영되지만 gmsh 가 쓰는 .msh 에는 반영되지
        # 않아 두 파일의 좌표가 어긋난다. gmsh 내부 메쉬도 같이 옮긴다.
        if args.shift_x:
            ncoord[:, 0] += args.shift_x
            gmsh.model.mesh.affineTransform(
                [1, 0, 0, args.shift_x,
                 0, 1, 0, 0,
                 0, 0, 1, 0])
            print(f"핀레이를 +X 로 {args.shift_x:+.4f} mm 평행이동 (간극 정규화)")

        print()
        print(f"절점 {len(ntags):,}  요소 {len(tets):,}")
        ref = REFERENCE.get(stem)
        if ref:
            dn = (len(ntags) - ref["nodes"]) / ref["nodes"] * 100
            de = (len(tets) - ref["elements"]) / ref["elements"] * 100
            print(f"PDF 기록 {ref['nodes']:,} / {ref['elements']:,}"
                  f"  → 절점 {dn:+.1f}%, 요소 {de:+.1f}%")
            if abs(dn) < 10 and abs(de) < 10:
                print("판정: 기록과 같은 수준. 재구축 메쉬로 사용 가능.")
            else:
                print("판정: 차이가 크다. 요소 크기나 알고리즘 설정을 재확인할 것.")

        # --- 요소 품질 ---
        q = np.array(gmsh.model.mesh.getElementQualities(qual_tags))
        print(f"요소 품질(gamma)  최소 {q.min():.4f}  평균 {q.mean():.4f}"
              f"  0.1 미만 {int((q < 0.1).sum())}개")

        # --- 내보내기 ---
        tag = f"{stem}_finray_{args.size}mm_o{args.order}"
        inp = OUT_DIR / f"{tag}.inp"
        write_mapdl_block(inp, ncoord, tets)
        gmsh.write(str(OUT_DIR / f"{tag}.msh"))

        meta = {
            "step": step_path.name,
            "mesh_size_mm": args.size,
            "element_order": args.order,
            "mapdl_element": "SOLID285" if args.order == 1 else "SOLID187",
            "shift_x_mm": args.shift_x,
            "finray": {
                "volume_mm3": round(fin_vol, 3),
                "nodes": int(len(ntags)),
                "elements": int(len(tets)),
                "quality_min": float(q.min()),
                "quality_mean": float(q.mean()),
            },
            "ball": ball,
            "reference_pdf": ref,
        }
        (OUT_DIR / f"{tag}_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        print()
        print(f"저장: {inp.name}")
        print(f"      {tag}_meta.json")
        return 0
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    raise SystemExit(main())
