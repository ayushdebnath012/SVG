"""
단일핑거 접촉 해석 — 재구축본 검증.

케이스 A (딱딱한 볼 + 변형하는 핀레이) 를 재현해 PDF 기록과 대조한다.
이 단계가 맞아야 3핑거로 넘어갈 수 있다.

검증 목표 (단일핑거 PDF 6절, 15deg):
    거리[mm]   면적[mm2]   힘[N]
     1.05        9.5       0.09
     2.10       15.4       0.43
     3.30       36.9       0.90
     4.50       56.8       1.44
     5.70       80.3       2.36
     6.90      105.2       4.35

접촉힘이 1차 기준이다. PDF 스스로 접촉힘은 신뢰도 "높음"(압력 과대평가와 면적
과소평가가 상쇄), 접촉 면적은 "낮음"(메쉬 해상도에 좌우)으로 적어두었다.

모델 구성
- 핀레이: SOLID285 (mixed u-P), Mooney-Rivlin c10=0.385 c01=1.47 MPa
- 볼:     TARGE170 해석적 구 프리미티브 (TSHAP,SPHE) R=40, 고정
          접촉부가 정확히 구면이라 메쉬 이산화 오차가 없다
- 접촉:   CONTA174, 마찰 없음 (PDF 단일핑거 해석 전체가 무마찰)
- 하중:   밑동(y=0)을 +X 로 밀어넣음, UY=UZ=0
- 간극:   0.735 mm (메쉬 생성 시 +0.2896 mm 평행이동으로 정규화 완료)
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from ansys.mapdl.core import launch_mapdl

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROJECT, ansys_exe, run_dir  # noqa: E402

MSH_DIR = PROJECT / "02_mesh" / "msh"
OUT_DIR = PROJECT / "05_results" / "raw"
RUN_LOC = run_dir("case_single")

# 재료 — NinjaFlex TPU, Reppel & Weinberg (2018) Mooney-Rivlin 피팅
C10, C01 = 0.385, 1.47          # MPa
BALL_R = 40.0                    # mm — 접촉부 실측 반지름

# PDF 기록 (15deg)
REFERENCE = pd.DataFrame({
    "dist_mm":  [1.05, 2.10, 3.30, 4.50, 5.70, 6.90],
    "pdf_area": [9.5, 15.4, 36.9, 56.8, 80.3, 105.2],
    "pdf_force": [0.09, 0.43, 0.90, 1.44, 2.36, 4.35],
})


def prepare_run_dir(path):
    """작업 폴더를 깨끗한 상태로 만든다.

    해석이 중간에 죽으면 file.lock 이 남아 다음 기동이 막힌다. 학생용 라이선스는
    동시 세션도 제한돼서, 죽은 MAPDL 프로세스가 떠 있으면 새 세션이 SOLUTION 을
    못 받는다. 두 가지를 함께 정리한다.
    """
    import subprocess
    import time

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    lock = p / "file.lock"
    if lock.exists():
        subprocess.run(["taskkill", "/F", "/IM", "ANSYS.exe"],
                       capture_output=True, check=False)
        subprocess.run(["taskkill", "/F", "/IM", "ANSYS261.exe"],
                       capture_output=True, check=False)
        time.sleep(2)
        try:
            lock.unlink()
            print(f"   남아 있던 file.lock 제거")
        except OSError as exc:
            raise RuntimeError(f"file.lock 을 지울 수 없다: {exc}") from exc


def build(mapdl, mesh_inp, ball_center, mu, fkn, order):
    """메쉬를 읽고 재료·접촉쌍·경계조건을 정의한다."""
    mapdl.clear()
    mapdl.prep7()

    # --- 요소 타입 ---
    # EBLOCK 의 각 줄은 TYPE/MAT/REAL 을 번호로 참조한다. 메쉬를 읽기 전에
    # 정의돼 있지 않으면 요소가 조용히 전부 버려진다 (절점만 들어옴).
    if order == 1:
        mapdl.et(1, 285)                   # SOLID285  4절점 mixed u-P
    else:
        mapdl.et(1, 187)                   # SOLID187  10절점 2차 사면체
        mapdl.keyopt(1, 6, 1)              # mixed u-P — 완전 비압축 초탄성에 필수
    mapdl.et(2, 170)                       # TARGE170  볼(강체)
    mapdl.et(3, 174)                       # CONTA174  접촉면

    # CONTA174 옵션
    mapdl.keyopt(3, 2, 0)                  # 증강 라그랑주
    mapdl.keyopt(3, 5, 0)                  # 초기 간극 자동조정 안 함 — 0.735 유지
    mapdl.keyopt(3, 9, 0)                  # 초기 관통/간극 그대로 반영
    mapdl.keyopt(3, 12, 0)                 # 표준 단면 접촉

    # --- 재료 ---
    mapdl.mp("DENS", 1, 1.2e-9)            # ton/mm^3 (TPU ~1200 kg/m^3), 정적이라 영향 없음
    mapdl.tb("HYPE", 1, 1, 2, "MOON")
    mapdl.tbdata(1, C10, C01)              # d=0 → 비압축, mixed u-P 가 처리

    # --- 메쉬 ---
    mapdl.input(str(mesh_inp))
    # NBLOCK/EBLOCK 은 형식이 조금만 어긋나도 조용히 빈 채로 넘어간다.
    # 여기서 바로 확인하지 않으면 한참 뒤 엉뚱한 곳에서 터진다.
    n_read = int(mapdl.get_value("NODE", 0, "COUNT"))
    e_read = int(mapdl.get_value("ELEM", 0, "COUNT"))
    if n_read == 0 or e_read == 0:
        raise RuntimeError(
            f"메쉬 읽기 실패 — 절점 {n_read}, 요소 {e_read}. "
            f"NBLOCK/EBLOCK 형식을 확인할 것: {mesh_inp}")
    print(f"   메쉬 읽음: 절점 {n_read:,}  요소 {e_read:,}")

    # --- 접촉 실상수 ---
    #   R1 = 타겟 프리미티브 반지름, R3 = FKN(법선강성계수)
    mapdl.r(1, BALL_R)
    mapdl.rmodif(1, 3, fkn)
    mapdl.mp("MU", 1, mu)

    # --- 볼: 해석적 구 강체 타겟 ---
    nmax = int(mapdl.get_value("NODE", 0, "NUM", "MAX"))
    pilot = nmax + 1
    mapdl.n(pilot, *ball_center)
    mapdl.type(2)
    mapdl.real(1)
    mapdl.mat(1)
    mapdl.tshap("SPHE")
    mapdl.e(pilot)                         # 구 프리미티브: 중심 절점 1개 + R1
    mapdl.tshap()                          # 프리미티브 모드 해제

    # --- 핀레이 표면에 접촉 요소 ---
    mapdl.allsel()
    mapdl.esel("S", "TYPE", "", 1)
    mapdl.nsle("S")
    mapdl.type(3)
    mapdl.real(1)
    mapdl.mat(1)
    mapdl.esurf()                          # 자유면(외피)에만 생성된다
    mapdl.allsel()

    n_cont = int(mapdl.get_value("ELEM", 0, "COUNT")) if False else None

    # --- 경계조건 ---
    # 볼은 고정 (케이스 A)
    mapdl.d(pilot, "ALL", 0)
    # 밑동 y=0 평면
    mapdl.nsel("S", "LOC", "Y", -0.01, 0.01)
    mapdl.cm("BASE", "NODE")
    n_base = int(mapdl.get_value("NODE", 0, "COUNT"))
    mapdl.allsel()

    return pilot, n_base


def solve_steps(mapdl, distances, nsubst=(20, 200, 10)):
    """각 거리까지 순차적으로 밀어넣는다. 거리마다 하나의 하중 스텝."""
    mapdl.run("/SOLU")
    mapdl.antype("STATIC")
    mapdl.nlgeom("ON")
    mapdl.autots("ON")
    mapdl.lnsrch("ON")
    # 각 하중 스텝의 마지막 서브스텝만 저장한다. 후처리에서 SET(i,"LAST") 로
    # 읽으므로 이걸로 충분하고, .rst 가 2차 요소에서 GB 급으로 커지는 걸 막는다.
    mapdl.outres("ERASE")
    mapdl.outres("ALL", "LAST")
    mapdl.cnvtol("F", "", 0.005, 2)         # 힘 수렴 0.5%

    for i, dist in enumerate(distances, start=1):
        mapdl.cmsel("S", "BASE")
        mapdl.d("ALL", "UX", dist)
        mapdl.d("ALL", "UY", 0)
        mapdl.d("ALL", "UZ", 0)
        mapdl.allsel()
        mapdl.nsubst(*nsubst)
        mapdl.time(i)
        out = mapdl.solve()
        print(f"  [스텝 {i}] 거리 {dist:.2f} mm 완료")
    mapdl.finish()


def post(mapdl, n_steps):
    """스텝마다 밑동 반력(=접촉힘)과 접촉 면적을 뽑는다."""
    mapdl.post1()
    rows = []
    for i in range(1, n_steps + 1):
        mapdl.set(i, "LAST")

        # 접촉힘 — 밑동 반력. 유일한 하중 경로라 접촉힘과 같다.
        # PDF: "밑동 반력(FSUM)으로 측정한 값은 램프 방식과 무관해 신뢰할 수 있다"
        mapdl.cmsel("S", "BASE")
        mapdl.fsum()
        fx = float(mapdl.get_value("FSUM", 0, "ITEM", "FX"))
        fy = float(mapdl.get_value("FSUM", 0, "ITEM", "FY"))
        fz = float(mapdl.get_value("FSUM", 0, "ITEM", "FZ"))

        # 최대 von Mises — 핀레이 solid 절점만
        mapdl.allsel()
        mapdl.esel("S", "TYPE", "", 1)
        mapdl.nsle("S")
        mapdl.nsort("S", "EQV")
        svm = float(mapdl.get_value("SORT", "", "MAX"))

        # 접촉 압력과 면적 — 압력>0 인 요소의 면적 합
        #
        # *GET,,ETAB,... 로 최댓값을 읽으면 엉뚱한 값(직전 NSORT 결과)이 돌아온다.
        # ETABLE 후 ESORT 를 거쳐 SORT 에서 읽는 것이 확실한 방법이다.
        mapdl.allsel()
        mapdl.esel("S", "TYPE", "", 3)
        mapdl.etable("EPRES", "CONT", "PRES")
        mapdl.etable("EAREA", "VOLU")
        mapdl.etable("EPENE", "CONT", "PENE")
        mapdl.esort("ETAB", "EPRES", 0, 1)      # 절대값 내림차순
        pmax = float(mapdl.get_value("SORT", "", "MAX"))
        mapdl.esort("ETAB", "EPENE", 0, 1)
        pene = float(mapdl.get_value("SORT", "", "MAX"))
        try:
            mapdl.esel("R", "ETAB", "EPRES", 1e-12, 1e12)
            n_closed = int(mapdl.get_value("ELEM", 0, "COUNT"))
            mapdl.ssum()
            area = float(mapdl.get_value("SSUM", 0, "ITEM", "EAREA"))
        except Exception:
            area, n_closed = float("nan"), -1
        mapdl.allsel()

        rows.append({
            "step": i, "fx_N": fx, "fy_N": fy, "fz_N": fz,
            "force_N": abs(fx), "area_mm2": area, "n_closed": n_closed,
            "pene_max_mm": pene, "pres_max_MPa": pmax, "svm_max_MPa": svm,
        })
        print(f"  [스텝 {i}] FX={fx:8.3f} N  면적={area:7.2f} mm2 "
              f"(요소 {n_closed:3d}개)  관통={pene:.5f} mm  "
              f"Pmax={pmax:.4f} MPa  SVM={svm:.3f} MPa")
    mapdl.finish()
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mu", type=float, default=0.0,
                    help="마찰계수 (PDF 단일핑거는 무마찰 0)")
    ap.add_argument("--fkn", type=float, default=1.0, help="법선접촉강성계수")
    ap.add_argument("--dist", type=float, nargs="*", default=None,
                    help="밀어넣을 거리 목록 [mm]")
    ap.add_argument("--nproc", type=int, default=4)
    ap.add_argument("--order", type=int, default=2, choices=(1, 2),
                    help="요소 차수. 1=SOLID285, 2=SOLID187(기본). "
                         "1차는 6.9mm 에서 요소 뒤집힘으로 파탄한다.")
    ap.add_argument("--size", type=float, default=2.5)
    args = ap.parse_args()

    tag = f"real15_finray_{args.size}mm_o{args.order}"
    mesh_inp = MSH_DIR / f"{tag}.inp"
    meta = json.loads((MSH_DIR / f"{tag}_meta.json").read_text(encoding="utf-8"))
    ball_center = meta["ball"]["center"]
    distances = args.dist if args.dist else list(REFERENCE["dist_mm"])

    print(f"볼 중심 {ball_center}  R={BALL_R}")
    print(f"메쉬 {meta['finray']['nodes']:,}절점 / {meta['finray']['elements']:,}요소"
          f"  {meta['mapdl_element']}  (간극 정규화 {meta['shift_x_mm']:+.4f} mm)")
    print(f"거리 {distances}")
    print(f"mu={args.mu}  FKN={args.fkn}")
    print()

    prepare_run_dir(RUN_LOC)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # license_type 을 지정하면 SOLUTION capability 가 빠진 제품으로 잡혀
    # "The capability SOLUTION was either not ordered..." 로 죽는다. 기본값을 쓸 것.
    mapdl = launch_mapdl(exec_file=ansys_exe(), run_location=RUN_LOC,
                         nproc=args.nproc, override=True, cleanup_on_exit=True)
    try:
        print("-- 모델 구성 --")
        pilot, n_base = build(mapdl, mesh_inp, ball_center,
                              args.mu, args.fkn, args.order)
        n_all = int(mapdl.get_value("NODE", 0, "COUNT"))
        mapdl.esel("S", "TYPE", "", 3)
        n_cont = int(mapdl.get_value("ELEM", 0, "COUNT"))
        mapdl.allsel()
        print(f"   절점 {n_all:,}  접촉요소 {n_cont:,}  밑동 절점 {n_base}")

        print("-- 해석 --")
        solve_steps(mapdl, distances)

        print("-- 후처리 --")
        df = post(mapdl, len(distances))
        df.insert(1, "dist_mm", distances)
    finally:
        try:
            mapdl.exit()
        except Exception:
            pass

    # PDF 대조
    merged = df.merge(REFERENCE, on="dist_mm", how="left")
    merged["force_err_%"] = (merged["force_N"] - merged["pdf_force"]) / merged["pdf_force"] * 100
    merged["area_err_%"] = (merged["area_mm2"] - merged["pdf_area"]) / merged["pdf_area"] * 100

    out = OUT_DIR / f"single_finger_15deg_o{args.order}_mu{args.mu}_fkn{args.fkn}.csv"
    merged.to_csv(out, index=False, encoding="utf-8-sig")

    print()
    print("=" * 78)
    print("  PDF 기록 대조 (15deg 단일핑거)")
    print("=" * 78)
    print(f"{'거리':>6} {'힘[N]':>9} {'PDF':>7} {'오차':>9} "
          f"{'면적[mm2]':>10} {'PDF':>8} {'오차':>9}")
    for _, r in merged.iterrows():
        print(f"{r['dist_mm']:6.2f} {r['force_N']:9.3f} {r['pdf_force']:7.2f} "
              f"{r['force_err_%']:8.1f}% {r['area_mm2']:10.2f} {r['pdf_area']:8.1f} "
              f"{r['area_err_%']:8.1f}%")
    print()
    print(f"저장: {out.name}")


if __name__ == "__main__":
    main()
