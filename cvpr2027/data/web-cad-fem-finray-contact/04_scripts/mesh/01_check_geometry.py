"""
STEP 형상 건전성 검사.

finray_basic.step 이 자기교차 와이어와 Unorientable shape 로 메쉬 생성에 실패한
전례가 있어, 메쉬를 만들기 전에 형상부터 검사한다.

검사 항목: 솔리드/면/에지 개수, 바운딩 박스, 체적, 퇴화 면(면적 0에 가까운 면),
짧은 에지. PDF 기록과 대조할 수 있도록 치수와 체적을 함께 출력한다.

사용법:
    python 01_check_geometry.py [step_file ...]
인자를 주지 않으면 01_geometry/source 의 STEP 3종을 모두 검사한다.
"""

import sys
from pathlib import Path

import gmsh

# PDF 기록값 — 재구축본이 원본과 같은 형상인지 대조용
REFERENCE = {
    "real15": {"bbox": (44.1, 74.0, 31.5), "volume": 15364.0},
    "real25": {"bbox": (44.1, 69.0, 31.5), "volume": 11250.0},
}

DEGENERATE_AREA = 1e-3   # mm^2 미만이면 퇴화 면으로 본다
SHORT_EDGE = 1e-2        # mm 미만이면 짧은 에지로 본다

PROJECT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT / "01_geometry" / "source"


def check(path: Path) -> bool:
    """STEP 파일 하나를 검사하고 메쉬 생성이 가능해 보이면 True."""
    print("=" * 68)
    print(f"  {path.name}")
    print("=" * 68)

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        gmsh.model.add(path.stem)
        try:
            gmsh.model.occ.importShapes(str(path))
            gmsh.model.occ.synchronize()
        except Exception as exc:
            print(f"  [실패] STEP 임포트 자체가 안 됨: {exc}")
            return False

        solids = gmsh.model.getEntities(3)
        faces = gmsh.model.getEntities(2)
        edges = gmsh.model.getEntities(1)
        print(f"  솔리드 {len(solids)} / 면 {len(faces)} / 에지 {len(edges)}")

        if not solids:
            print("  [실패] 솔리드가 없다. 껍질(shell)만 있는 STEP 일 가능성.")
            return False

        # 바운딩 박스와 체적
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
        dims = (xmax - xmin, ymax - ymin, zmax - zmin)
        volume = sum(gmsh.model.occ.getMass(3, tag) for _, tag in solids)
        print(f"  치수  {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
        print(f"  체적  {volume:,.0f} mm^3")

        ref = REFERENCE.get(path.stem)
        if ref:
            ok_dim = all(abs(a - b) < 1.0 for a, b in zip(dims, ref["bbox"]))
            ok_vol = abs(volume - ref["volume"]) / ref["volume"] < 0.05
            print(f"  PDF 기록 대조 — 치수 {'일치' if ok_dim else '불일치'}, "
                  f"체적 {'일치' if ok_vol else '불일치'} "
                  f"(기록: {ref['bbox'][0]}x{ref['bbox'][1]}x{ref['bbox'][2]}, "
                  f"{ref['volume']:,.0f} mm^3)")

        # 퇴화 면 / 짧은 에지 — basic 형상이 걸렸던 항목
        tiny_faces = [tag for _, tag in faces
                      if gmsh.model.occ.getMass(2, tag) < DEGENERATE_AREA]
        short_edges = [tag for _, tag in edges
                       if gmsh.model.occ.getMass(1, tag) < SHORT_EDGE]
        print(f"  퇴화 면(<{DEGENERATE_AREA} mm^2)  {len(tiny_faces)}")
        print(f"  짧은 에지(<{SHORT_EDGE} mm)      {len(short_edges)}")

        if tiny_faces or short_edges:
            print("  [주의] 퇴화 형상이 있다. 메쉬가 나와도 요소 품질을 확인할 것.")

        return True
    finally:
        gmsh.finalize()


def main() -> int:
    if len(sys.argv) > 1:
        targets = [Path(a) for a in sys.argv[1:]]
    else:
        targets = sorted(SOURCE_DIR.glob("*.step"))

    if not targets:
        print(f"검사할 STEP 파일이 없다: {SOURCE_DIR}")
        return 1

    results = {}
    for path in targets:
        if not path.exists():
            print(f"[건너뜀] 파일 없음: {path}")
            continue
        try:
            results[path.name] = check(path)
        except Exception as exc:
            print(f"  [실패] 검사 중 예외: {exc}")
            results[path.name] = False
        print()

    print("=" * 68)
    print("  요약")
    print("=" * 68)
    for name, ok in results.items():
        print(f"  {'사용 가능' if ok else '사용 불가':<10} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
