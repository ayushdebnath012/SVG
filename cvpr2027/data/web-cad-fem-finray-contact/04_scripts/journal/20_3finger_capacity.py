"""
3핑거 그리퍼 파지 용량 — 무게 상한치.

절차
  1단계 (파지)  세 손가락을 볼 중심축(Y) 쪽으로 반경방향 조임
  2단계 (인발)  볼을 아래(-Y)로 서서히 끌어내리며 반력 측정

반력이 상승하다 평탄해지는 지점이 마찰 한계다. 그 평탄값이 최대 지지 하중이고,
9.81 로 나누면 무게 상한(kg)이 된다.

왜 중력을 직접 걸지 않는가
  볼을 연직 구속한 채 중력을 걸면 하중이 전부 구속 반력으로 빠져 접촉에 전달되지
  않는다. 볼을 자유롭게 놓으면 접촉이 물기 전에 자유낙하로 발산한다 (원본 기록:
  변위 5e9 mm). 변위 구동 인발은 두 문제를 모두 피하면서 용량을 직접 준다.

좌표계
  볼은 y=0 / y=60 에서 잘린 R=40 구라 대칭축이 Y다. 그리퍼 축도 Y이고 손가락은
  Y축 둘레 120도 간격. Y축 원통좌표계를 만들어 밑동 절점을 NROTAT 하면 반경방향이
  곧 조임 방향이 되어, 세 손가락을 명령 하나로 조일 수 있다.
  (원통 절점좌표계에서 UX=반경, UY=원주, UZ=축방향=전역 Y)

신뢰 구간
  단일핑거 검증 결과 6.9mm 조임에서 메쉬 3종 모두 파탄한다 (힘 급등 + 접촉면적
  감소 + 접촉압력 82배). 5.7mm 이하만 유효하므로 그 안에서만 조인다.
"""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd
from ansys.mapdl.core import launch_mapdl

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROJECT, ansys_exe, run_dir, kill_stale  # noqa: E402

MSH_DIR = PROJECT / "02_mesh" / "msh"
OUT_DIR = PROJECT / "05_results" / "raw"
RUN_LOC = run_dir("case_3finger")

C10, C01 = 0.385, 1.47      # MPa — NinjaFlex Mooney-Rivlin
BALL_R = 40.0               # mm — 접촉부 실측 반지름
G = 9.80665                 # m/s^2

# 신뢰 구간 상한. 단일핑거에서 6.9mm 는 메쉬와 무관하게 파탄점이었다.
CLOSE_LIMIT = 5.7

# 접촉 요소를 만들 띠의 두께 [mm]. 볼 표면(R=40) 에서 이만큼 바깥까지.
# 18mm 면 3핑거 접촉요소 19,953 개로 총 115,261 (한도의 90%).
# 조임 5.7mm 동안 접촉점이 이동하는 범위를 덮을 만큼 넉넉해야 한다.
CONTACT_BAND = 18.0


def build(mapdl, mesh_inp, ball_center, mu, fkn):
    mapdl.clear()
    mapdl.prep7()

    # 요소 타입은 EBLOCK 을 읽기 전에 정의돼야 한다. 아니면 요소가 조용히 버려진다.
    mapdl.et(1, 285)                    # SOLID285  핀레이
    mapdl.et(2, 170)                    # TARGE170  볼(강체)
    mapdl.et(3, 174)                    # CONTA174  접촉
    mapdl.keyopt(3, 2, 0)               # 증강 라그랑주
    mapdl.keyopt(3, 5, 0)               # 초기 간극 자동조정 안 함
    mapdl.keyopt(3, 9, 0)               # 초기 간극 그대로 반영
    mapdl.keyopt(3, 12, 0)              # 표준 단면 접촉 (미끄러짐 허용)

    mapdl.mp("DENS", 1, 1.2e-9)
    mapdl.tb("HYPE", 1, 1, 2, "MOON")
    mapdl.tbdata(1, C10, C01)
    mapdl.mp("MU", 1, mu)

    mapdl.r(1, BALL_R)                  # R1 = 타겟 구 반지름
    mapdl.rmodif(1, 3, fkn)             # R3 = FKN

    mapdl.input(str(mesh_inp))
    n_read = int(mapdl.get_value("NODE", 0, "COUNT"))
    e_read = int(mapdl.get_value("ELEM", 0, "COUNT"))
    if n_read == 0 or e_read == 0:
        raise RuntimeError(f"메쉬 읽기 실패 — 절점 {n_read}, 요소 {e_read}")
    print(f"   메쉬: 절점 {n_read:,}  요소 {e_read:,}")

    cx, cy, cz = ball_center

    # 볼 = 해석적 구 강체 타겟 + 파일럿 절점
    pilot = n_read + 1
    mapdl.n(pilot, cx, cy, cz)
    mapdl.type(2); mapdl.real(1); mapdl.mat(1)
    mapdl.tshap("SPHE")
    mapdl.e(pilot)
    mapdl.tshap()

    # 접촉 요소는 볼 주변 띠에만 만든다.
    #
    # 손가락 외피 전체에 만들면 3핑거 기준 접촉요소가 40,176개가 되어
    # 솔리드 95,307 과 합쳐 Student 한도 128,000 을 넘는다. 닿지도 않는
    # 뒷면까지 만드는 셈이라 낭비이기도 하다.
    #
    # 중요: 솔리드 요소는 '전부' 선택한 채 절점만 띠로 제한한다. ESURF 는
    # 선택된 요소의 자유면 중 절점이 모두 선택된 면에만 요소를 만든다.
    # 요소까지 띠로 줄이면 띠 경계의 내부면이 자유면으로 보여 가짜 접촉면이
    # 생긴다.
    mapdl.local(12, 2, cx, cy, cz)      # 볼 중심 구면좌표계 (LOC,X = 반경)
    mapdl.allsel()
    mapdl.esel("S", "TYPE", "", 1)      # 솔리드 전부
    mapdl.csys(12)
    mapdl.nsel("S", "LOC", "X", 0, BALL_R + CONTACT_BAND)
    mapdl.csys(0)
    mapdl.type(3); mapdl.real(1); mapdl.mat(1)
    mapdl.esurf()
    mapdl.allsel()
    mapdl.esel("S", "TYPE", "", 3)
    n_cont = int(mapdl.get_value("ELEM", 0, "COUNT"))
    mapdl.allsel()
    n_total = int(mapdl.get_value("ELEM", 0, "COUNT"))
    print(f"   총 요소 {n_total:,} / 한도 128,000 ({n_total/128000*100:.1f}%)")
    if n_total > 128000:
        raise RuntimeError(f"요소 한도 초과 ({n_total:,}). CONTACT_BAND 를 줄일 것.")

    # Y축 원통좌표계 — THYZ=-90 이 국부 Z 를 전역 Y 에 맞춘다.
    # 원통계(KCS=1)의 축은 국부 Z 이므로 이것이 그리퍼 축이 된다.
    mapdl.local(11, 1, cx, cy, cz, 0, -90, 0)

    # 밑동 절점 선택은 전역 좌표 기준
    mapdl.csys(0)
    mapdl.nsel("S", "LOC", "Y", -0.01, 0.01)
    mapdl.cm("BASE", "NODE")
    n_base = int(mapdl.get_value("NODE", 0, "COUNT"))

    # NROTAT 은 '활성' 좌표계로 절점좌표계를 돌린다. 전역인 채로 부르면
    # 아무 효과가 없으므로 반드시 원통계로 바꾼 뒤 호출한다.
    mapdl.csys(11)
    mapdl.nrotat("ALL")
    mapdl.csys(0)
    mapdl.allsel()

    print(f"   접촉요소 {n_cont:,}  밑동 절점 {n_base}  파일럿 절점 {pilot}")
    return pilot, n_base, n_cont


def solve_all(mapdl, pilot, closings, pull_mm, nsub):
    """파지 → 인발을 '하나의' /SOLU 세션에서 연속 하중 스텝으로 푼다.

    중간에 FINISH 로 나가 POST1 을 들렀다가 /SOLU 로 돌아오면 MAPDL 이 해석을
    새로 시작한다 (ANTYPE 을 다시 선언하지 않아도 그렇다). 그러면:
      - 결과 파일이 덮어써져 앞 하중스텝이 사라지고
      - 조임 변위가 0 부터 다시 램프되어, 조이면서 동시에 당기는 이력이 된다
        (마찰은 이력 의존이므로 실제 순서와 다른 답이 나온다)
    실제로 이 실수로 두 번 다시 돌렸다. 후처리는 전부 solve 가 끝난 뒤에 한다.
    """
    mapdl.run("/SOLU")
    mapdl.antype("STATIC")
    mapdl.nlgeom("ON")
    mapdl.autots("ON")
    mapdl.lnsrch("ON")
    mapdl.cnvtol("F", "", 0.005, 2)

    # 마찰 접촉은 접선강성 행렬을 비대칭으로 만든다. mu=0.6 처럼 큰 마찰에서
    # 대칭 솔버로는 미끄러짐 구간이 사실상 수렴하지 않는다.
    # (MAPDL 도 경고를 낸다: "Maximum friction coefficient 0.6 is defined...
    #  Switch to the unsymmetric solver (NROP,UNSYM)")
    # 실제로 대칭 솔버로는 인발 67% 지점에서 2시간 동안 서브스텝 하나를
    # 넘기지 못했다.
    mapdl.nropt("UNSYM")

    # --- 1단계: 파지 ---
    mapdl.outres("ERASE")
    mapdl.outres("ALL", "LAST")
    mapdl.d(pilot, "ALL", 0)            # 파지 중에는 볼 고정

    for i, c in enumerate(closings, start=1):
        mapdl.cmsel("S", "BASE")
        mapdl.d("ALL", "UX", -c)        # 반경 감소 = 조임
        mapdl.d("ALL", "UY", 0)         # 원주방향 고정
        mapdl.d("ALL", "UZ", 0)         # 축방향(전역 Y) 고정
        mapdl.allsel()
        mapdl.nsubst(20, 400, 10)
        mapdl.time(i)
        mapdl.solve()
        print(f"  [파지 {i}/{len(closings)}] 조임 {c:.2f} mm 완료")

    # --- 2단계: 인발 (같은 /SOLU 세션에서 이어서) ---
    n_close = len(closings)
    print("-- 2단계: 인발 --")
    mapdl.outres("ERASE")
    mapdl.outres("ALL", "ALL")          # 곡선을 그려야 하므로 전 서브스텝 저장
    mapdl.allsel()
    mapdl.d(pilot, "UY", pull_mm)       # 부호는 호출부에서 정한다
    mapdl.nsubst(nsub, nsub * 8, nsub)
    mapdl.time(n_close + 1)
    mapdl.solve()
    mapdl.finish()
    print(f"  [인발] {pull_mm:.2f} mm 완료")
    return n_close


def read_grip(mapdl, n_steps):
    """파지 단계의 손가락별 반경방향 파지력.

    FSUM 은 절점좌표계가 아니라 '전역' 좌표계로 합산한다. 손가락이 120도씩
    돌아가 있으므로 전역 FX 만 읽으면 손가락마다 다른 값이 나온다 (대칭인데도).
    그리퍼 축이 Y 이므로 반경 성분 = sqrt(FX^2 + FZ^2) 로 구해야 한다.
    원본 PDF 4.2절도 FX/FY/FZ 를 모두 적고 반경 성분을 따로 계산했다.
    """
    enter_post1(mapdl)
    rows = []
    for i in range(1, n_steps + 1):
        mapdl.set(i, "LAST")
        per_finger, axial = [], []
        for k in range(3):
            mapdl.cmsel("S", f"BASE{k}")
            mapdl.fsum()
            fx = float(mapdl.get_value("FSUM", 0, "ITEM", "FX"))
            fy = float(mapdl.get_value("FSUM", 0, "ITEM", "FY"))
            fz = float(mapdl.get_value("FSUM", 0, "ITEM", "FZ"))
            per_finger.append(float(np.hypot(fx, fz)))   # 반경 성분
            axial.append(fy)                             # 축방향(전역 Y)
        mapdl.allsel()
        mapdl.esel("S", "TYPE", "", 3)
        mapdl.etable("EPRES", "CONT", "PRES")
        mapdl.etable("EPENE", "CONT", "PENE")
        mapdl.esort("ETAB", "EPENE", 0, 1)
        pene = float(mapdl.get_value("SORT", "", "MAX"))
        mapdl.allsel()
        spread = (max(per_finger) - min(per_finger)) / max(per_finger) * 100
        rows.append(dict(step=i, f0=per_finger[0], f1=per_finger[1],
                         f2=per_finger[2], total=sum(per_finger),
                         axial_mean=float(np.mean(axial)),
                         asym_pct=spread, pene=pene))
    mapdl.finish()
    return rows


def read_pull(mapdl, lstep):
    """인발 단계의 (볼 변위, 반력) 곡선."""
    enter_post1(mapdl)
    mapdl.set("FIRST")
    n = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
    rows = []
    for s in range(1, n + 1):
        # SET 의 첫 인자는 데이터셋 번호가 아니라 '하중 스텝' 번호다.
        # 결과 세트를 순번으로 훑으려면 nset= 을 써야 한다.
        mapdl.set(nset=s)
        # *GET 의 필드명은 LSTEP 이 아니라 LSTP 다
        ls = float(mapdl.get_value("ACTIVE", 0, "SET", "LSTP"))
        if int(ls) != lstep:
            continue
        uy = float(mapdl.get_value("NODE", PILOT[0], "U", "Y"))
        # FSUM 은 구속 절점의 반력을 잡지 못한다 (전 구간 0 이 나온다).
        # 반력은 *GET,,NODE,n,RF,FY 로 읽어야 한다.
        fy = float(mapdl.get_value("NODE", PILOT[0], "RF", "FY"))

        # 접촉 상태도 같이 본다. 접촉압력이 갑자기 튀면 그 지점부터는
        # 수치 파탄이라 곡선을 믿을 수 없다.
        mapdl.allsel()
        mapdl.esel("S", "TYPE", "", 3)
        mapdl.etable("EP", "CONT", "PRES")
        mapdl.etable("EN", "CONT", "PENE")
        mapdl.esort("ETAB", "EP", 0, 1)
        pmax = float(mapdl.get_value("SORT", "", "MAX"))
        mapdl.esort("ETAB", "EN", 0, 1)
        pene = float(mapdl.get_value("SORT", "", "MAX"))
        mapdl.esel("R", "ETAB", "EP", 1e-12, 1e12)
        nclosed = int(mapdl.get_value("ELEM", 0, "COUNT"))
        mapdl.allsel()
        rows.append(dict(uy_mm=uy, fy_N=abs(fy), n_closed=nclosed,
                         pres_max_MPa=pmax, pene_max_mm=pene))
    mapdl.finish()
    return rows


PILOT = [0]          # read_pull 에서 참조
POST_ONLY = [False]  # True 면 POST1 진입 시마다 기존 file.rst 를 다시 지정


def enter_post1(mapdl):
    mapdl.post1()
    if POST_ONLY[0]:
        # 잡네임이 post 라서 기본 결과파일이 post.rst 가 된다. 기존 결과를 가리킨다.
        mapdl.file("file", "rst")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mu", type=float, default=0.6)
    ap.add_argument("--fkn", type=float, default=1.0)
    ap.add_argument("--size", type=float, default=1.5)
    ap.add_argument("--close", type=float, nargs="*",
                    default=[3.0, 4.0, 5.0, 5.7],
                    help="조임량 목록 [mm]. 5.7 초과는 신뢰 구간 밖.")
    ap.add_argument("--pull", type=float, default=2.0,
                    help="볼을 끌어낼 거리 [mm] (부호 없는 크기)")
    ap.add_argument("--pull-dir", choices=("tip", "base"), default="tip",
                    help="볼을 빼내는 방향. "
                         "tip=+Y(팁 쪽) — 뒤집은 픽업 자세에서 중력이 볼을 "
                         "당기는 방향. 실제 파지 한계를 보려면 이쪽이다. "
                         "base=-Y(밑동 쪽) — 손가락이 볼을 아래에서 받치는 "
                         "자세라 형상 구속이 지배해 마찰 한계가 안 보인다.")
    ap.add_argument("--nsub", type=int, default=40)
    ap.add_argument("--nproc", type=int, default=4)
    ap.add_argument("--post-only", action="store_true",
                    help="다시 풀지 않고 기존 file.rst 만 후처리한다. "
                         "모델은 PREP7 로 재구성하되 SOLVE 는 건너뛴다 "
                         "(메쉬가 같으면 절점 번호가 일치하므로 결과와 맞는다).")
    args = ap.parse_args()

    over = [c for c in args.close if c > CLOSE_LIMIT]
    if over:
        print(f"!! 경고: {over} 는 신뢰 구간({CLOSE_LIMIT}mm) 밖이다. "
              f"6.9mm 부근에서 메쉬와 무관하게 수치 파탄이 확인됐다.")

    mesh_inp = MSH_DIR / f"real15_3finger_{args.size}mm.inp"
    meta = json.loads((MSH_DIR / "real15_3finger_meta.json").read_text(encoding="utf-8"))
    ball = meta["ball"]

    print(f"3핑거 파지 용량 해석")
    print(f"  볼 중심 {ball['center']}  접촉 반지름 {ball['r_contact_mm']} mm")
    print(f"  볼 체적 {ball['volume_mm3']:,.1f} mm^3 (잘린 형상)")
    print(f"  mu={args.mu}  FKN={args.fkn}  메쉬 {args.size}mm")
    print(f"  조임 {args.close} mm   인발 {args.pull} mm")
    print()

    POST_ONLY[0] = args.post_only
    kill_stale()
    Path(RUN_LOC).mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 후처리 전용일 때는 잡네임을 바꿔 기존 file.* 를 건드리지 않는다
    mapdl = launch_mapdl(exec_file=ansys_exe(), run_location=RUN_LOC,
                         nproc=args.nproc, override=True, cleanup_on_exit=True,
                         jobname="post" if args.post_only else "file")
    try:
        print("-- 모델 구성 --")
        pilot, n_base, n_cont = build(mapdl, mesh_inp, ball["center"],
                                      args.mu, args.fkn)
        PILOT[0] = pilot

        n_steps = len(args.close)
        if args.post_only:
            print("-- 후처리 전용: 기존 file.rst 사용 --")
            mapdl.post1()
            mapdl.file("file", "rst")
            nset = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
            mapdl.set("LAST")
            tmax = float(mapdl.get_value("ACTIVE", 0, "SET", "TIME"))
            lmax = int(mapdl.get_value("ACTIVE", 0, "SET", "LSTP"))
            mapdl.finish()
            print(f"   결과 세트 {nset}개, 마지막 하중스텝 {lmax}, TIME {tmax:.4f}")
            if lmax <= n_steps:
                print(f"   !! 인발 단계(하중스텝 {n_steps+1})가 결과 파일에 없다. "
                      f"파지 단계만 후처리한다.")
        else:
            print("-- 1단계: 파지 --")
            signed_pull = args.pull if args.pull_dir == "tip" else -args.pull
            n_steps = solve_all(mapdl, pilot, args.close, signed_pull, args.nsub)

        print("-- 파지력 --")
        grip = read_grip(mapdl, n_steps)
        pd.DataFrame(grip).assign(close_mm=args.close).to_csv(
            OUT_DIR / "_partial_grip.csv", index=False, encoding="utf-8-sig")
        for g, c in zip(grip, args.close):
            print(f"  조임 {c:.2f} mm  반경력 {g['f0']:.3f}/{g['f1']:.3f}/"
                  f"{g['f2']:.3f} N  합계 {g['total']:.3f} N  "
                  f"비대칭 {g['asym_pct']:.2f}%  관통 {g['pene']:.5f} mm")
        worst = max(g["asym_pct"] for g in grip)
        if worst > 5:
            print(f"  !! 손가락 간 비대칭 {worst:.1f}% — 배치나 경계조건 확인 필요")
        else:
            print(f"  대칭성 양호 (최대 편차 {worst:.2f}%)")

        try:
            pull = read_pull(mapdl, n_steps + 1)
            pd.DataFrame(pull).to_csv(OUT_DIR / "_partial_pull.csv",
                                      index=False, encoding="utf-8-sig")
        except Exception as exc:
            print(f"  !! 인발 후처리 실패: {type(exc).__name__}: {str(exc)[:200]}")
            print(f"     결과는 {RUN_LOC}\\file.rst 에 남아 있다.")
            pull = []
    finally:
        try:
            mapdl.exit()
        except Exception:
            pass
        kill_stale()

    df_grip = pd.DataFrame(grip)
    df_grip.insert(1, "close_mm", args.close)
    df_pull = pd.DataFrame(pull)

    tagname = f"3finger_15deg_{args.size}mm_mu{args.mu}_{args.pull_dir}"
    df_grip.to_csv(OUT_DIR / f"{tagname}_grip.csv", index=False, encoding="utf-8-sig")
    df_pull.to_csv(OUT_DIR / f"{tagname}_pull.csv", index=False, encoding="utf-8-sig")

    print()
    print("=" * 74)
    print("  인발 곡선")
    print("=" * 74)
    print(f"  {'볼변위[mm]':>11} {'반력[N]':>9} {'환산[kg]':>9} "
          f"{'닫힌접촉':>9} {'Pmax[MPa]':>10}")
    for _, r in df_pull.iterrows():
        print(f"  {r['uy_mm']:11.4f} {r['fy_N']:9.3f} {r['fy_N']/G:9.4f} "
              f"{int(r['n_closed']):9d} {r['pres_max_MPa']:10.4f}")

    if len(df_pull):
        # 접촉압력이 직전 대비 2배 이상 뛰면 그 지점부터 수치 파탄으로 본다.
        # (단일핑거 검증에서 파탄은 항상 압력 급등 + 접촉면적 감소로 나타났다)
        p = df_pull["pres_max_MPa"].to_numpy()
        bad = None
        for i in range(1, len(p)):
            if p[i] > 2.0 * p[i - 1]:
                bad = i
                break
        valid = df_pull.iloc[:bad] if bad else df_pull
        print()
        if bad:
            print(f"  !! 접촉압력이 {p[bad-1]:.2f} -> {p[bad]:.2f} MPa 로 급등 "
                  f"(볼 변위 {df_pull['uy_mm'].iloc[bad]:.3f} mm). "
                  f"이 지점부터 수치 파탄으로 판단해 제외한다.")
        cap = float(valid["fy_N"].max())
        cap_u = float(valid["uy_mm"].iloc[valid["fy_N"].idxmax()])
        print(f"  신뢰 구간 내 최대 반력 = {cap:.3f} N "
              f"(볼 변위 {cap_u:.3f} mm)  →  {cap / G:.3f} kg")
        print()
        print(f"  쿨롱 근사 (마찰만) = mu x 총파지력 = {args.mu} x "
              f"{grip[-1]['total']:.3f} = {args.mu * grip[-1]['total']:.3f} N "
              f"→ {args.mu * grip[-1]['total'] / G:.3f} kg")
        print()
        print(f"  조건: 조임 {args.close[-1]} mm, mu={args.mu}, "
              f"메쉬 {args.size}mm (1.0mm 대비 약 10% 불확실)")

    print(f"\n저장: {tagname}_grip.csv / {tagname}_pull.csv")


if __name__ == "__main__":
    main()
