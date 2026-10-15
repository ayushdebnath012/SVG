"""
3핑거 그리퍼 — 중력 하중으로 '아예 놓치는' 무게 찾기.

앞선 20_ 스크립트와 무엇이 다른가
  (1) 방향: -Y (중력 방향). 손가락이 볼을 아래에서 받치는 배치이므로
      이쪽이 실제 파지 자세다. 접촉 구역이 y=6~31mm 로 볼 적도(y=30) 아래에
      몰려 있는 것이 근거.
  (2) 하중 구동: 변위로 밀어넣으면 저항이 한없이 오르기만 해서 '못 잡는
      순간'이 나타나지 않는다. 중력을 실제 하중으로 걸고 키우면서 평형을
      못 찾는 지점을 찾는다 — 이것이 '아예 놓친다'의 정의다.
  (3) 볼을 횡방향으로도 풀어준다. 실제로는 볼이 손가락 사이로 옆으로 빠질 수
      있는데 앞선 해석은 그 모드를 구속하고 있었다.

중력 구현
  파일럿 절점에 MASS21 로 기준 질량 1 kg 을 두고 ACEL 을 g 의 배수로 램프한다.
  질량 1kg x (n x g) 의 관성력은 (n kg) 의 무게와 같으므로, 마지막으로 수렴한
  가속도 배수가 곧 kg 단위 상한이 된다.

단위계: mm, N, tonne, s  ->  g = 9806.65 mm/s^2, 질량 1 kg = 1e-3 tonne
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

C10, C01 = 0.385, 1.47
BALL_R = 40.0
CONTACT_BAND = 18.0
G_MMS2 = 9806.65            # mm/s^2
REF_MASS_TON = 1.0e-3       # 1 kg


def build(mapdl, mesh_inp, ball_center, mu, fkn):
    mapdl.clear()
    mapdl.prep7()

    mapdl.et(1, 285)                    # SOLID285  핀레이
    mapdl.et(2, 170)                    # TARGE170  볼(강체)
    mapdl.et(3, 174)                    # CONTA174  접촉
    mapdl.keyopt(3, 2, 0)
    mapdl.keyopt(3, 5, 0)
    mapdl.keyopt(3, 9, 0)
    mapdl.keyopt(3, 12, 0)

    mapdl.mp("DENS", 1, 1.2e-9)
    mapdl.tb("HYPE", 1, 1, 2, "MOON")
    mapdl.tbdata(1, C10, C01)
    mapdl.mp("MU", 1, mu)

    mapdl.r(1, BALL_R)                  # R1 = 타겟 구 반지름
    mapdl.rmodif(1, 3, fkn)             # R3 = FKN

    mapdl.input(str(mesh_inp))
    n_read = int(mapdl.get_value("NODE", 0, "COUNT"))
    if n_read == 0 or int(mapdl.get_value("ELEM", 0, "COUNT")) == 0:
        raise RuntimeError("메쉬 읽기 실패")
    print(f"   메쉬: 절점 {n_read:,}")

    cx, cy, cz = ball_center

    # 볼 = 해석적 구 강체 타겟 + 파일럿 절점.
    #
    # 절점이 둘 필요하다. 구 프리미티브의 정의 절점(n_c)은 '구속'만 가능하고
    # 하중을 받지 못한다 — 힘을 걸어도 아무 일이 일어나지 않는다 (실제로
    # 8 kg 까지 처짐이 정확히 0 으로 나왔다). 강체 타겟에 하중을 걸려면
    # TSHAP,PILO 로 만든 별도의 파일럿 절점이 있어야 하고, 그 절점이 타겟
    # 전체의 운동을 대표한다.
    #
    # MASS21 을 붙여 중력을 걸려고도 했으나 타겟 절점은 다른 요소와 공유할 수
    # 없어 거부된다. 강체 구에서는 중심 점하중이 자중과 정적으로 동등하므로
    # 파일럿에 힘을 준다.
    n_c = n_read + 1                    # 구 프리미티브 정의 절점
    pilot = n_read + 2                  # 파일럿 (하중·구속을 여기에)
    mapdl.n(n_c, cx, cy, cz)
    mapdl.n(pilot, cx, cy, cz)          # 같은 위치의 별개 절점

    mapdl.type(2); mapdl.real(1); mapdl.mat(1)
    mapdl.tshap("SPHE")
    mapdl.e(n_c)
    mapdl.tshap("PILO")
    mapdl.e(pilot)
    mapdl.tshap()

    # 접촉 요소는 볼 주변 띠에만 (요소 한도)
    mapdl.local(12, 2, cx, cy, cz)
    mapdl.allsel()
    mapdl.esel("S", "TYPE", "", 1)
    mapdl.csys(12)
    mapdl.nsel("S", "LOC", "X", 0, BALL_R + CONTACT_BAND)
    mapdl.csys(0)
    mapdl.type(3); mapdl.real(1); mapdl.mat(1)
    mapdl.esurf()
    mapdl.allsel()
    n_total = int(mapdl.get_value("ELEM", 0, "COUNT"))
    print(f"   총 요소 {n_total:,} / 한도 128,000 ({n_total/128000*100:.1f}%)")
    if n_total > 128000:
        raise RuntimeError(f"요소 한도 초과 ({n_total:,})")

    # Y축 원통좌표계 — 밑동 절점을 회전시켜 반경방향 조임
    mapdl.local(11, 1, cx, cy, cz, 0, -90, 0)
    mapdl.csys(0)
    mapdl.nsel("S", "LOC", "Y", -0.01, 0.01)
    mapdl.cm("BASE", "NODE")
    mapdl.csys(11)
    mapdl.nrotat("ALL")
    mapdl.csys(0)
    mapdl.allsel()
    return pilot


def switch_to_force_grip(mapdl, grip_force_N, n_base_per_finger=449):
    """밑동 구속을 '변위 고정'에서 '일정한 반경 힘'으로 바꾼다.

    왜 필요한가
      변위로 고정하면 볼이 아무리 무거워도 손가락을 벌릴 수 없다. 형상 구속이
      절대적이 되어 모델이 3 kg 을 넘겨도 볼을 놓치지 않는다.
      실제 그리퍼는 액추에이터가 유한한 힘으로 쥐므로, 볼 무게가 그 힘을 이기면
      손가락이 밀려 벌어지고 볼이 빠진다. 이쪽이 실제에 가깝다.

    밑동 절점은 이미 원통좌표계로 NROTAT 돼 있어 FX 가 곧 반경방향이다.
    조임은 반경 감소이므로 안쪽(-FX) 으로 건다.
    """
    mapdl.cmsel("S", "BASE")
    mapdl.ddele("ALL", "UX")            # 반경방향만 풀어준다
    per_node = -abs(grip_force_N) / n_base_per_finger
    mapdl.f("ALL", "FX", per_node)      # 안쪽으로
    mapdl.allsel()
    return per_node


def solve(mapdl, pilot, closings, gmax, nsub, lateral_free, tilt_deg=0.0,
          grip_force_N=None):
    """조임 -> 중력 램프. 하나의 /SOLU 세션에서 연속 하중 스텝.

    POST1 을 들렀다 돌아오면 해석이 새로 시작되어 결과가 덮어써지므로
    후처리는 전부 solve 완료 후에 한다.
    """
    mapdl.run("/SOLU")
    mapdl.antype("STATIC")
    mapdl.nlgeom("ON")
    mapdl.autots("ON")
    mapdl.lnsrch("ON")
    mapdl.cnvtol("F", "", 0.005, 2)
    mapdl.nropt("UNSYM")            # 마찰 -> 비대칭 접선강성
    mapdl.outres("ERASE")
    mapdl.outres("ALL", "LAST")

    # --- 1단계: 파지 (볼 완전 고정) ---
    mapdl.d(pilot, "ALL", 0)
    for i, c in enumerate(closings, start=1):
        mapdl.cmsel("S", "BASE")
        mapdl.d("ALL", "UX", -c)
        mapdl.d("ALL", "UY", 0)
        mapdl.d("ALL", "UZ", 0)
        mapdl.allsel()
        mapdl.nsubst(20, 400, 10)
        mapdl.time(i)
        mapdl.solve()
        print(f"  [파지 {i}/{len(closings)}] 조임 {c:.2f} mm 완료")

    # --- 1.5단계: 밑동을 힘 구동으로 전환 (선택) ---
    # 전환에도 하중 스텝이 하나 필요하다. 그만큼 중력 램프의 시작 TIME 이
    # 밀리므로, 후처리가 kg 을 제대로 환산하도록 램프 구간을 돌려준다.
    n_close = len(closings)
    t_ramp0 = n_close
    if grip_force_N:
        pn = switch_to_force_grip(mapdl, grip_force_N)
        mapdl.nsubst(20, 200, 10)
        mapdl.time(n_close + 1)
        mapdl.solve()
        t_ramp0 = n_close + 1
        print(f"  [전환] 밑동을 반경력 {grip_force_N:.3f} N/손가락 "
              f"({pn:.6f} N/절점) 로 전환 완료")

    # --- 2단계: 중력 램프 ---
    print(f"-- 2단계: 중력 램프 0 -> {gmax:.0f} g "
          f"(= {gmax:.0f} kg 상당) --")
    mapdl.outres("ERASE")
    mapdl.outres("ALL", "ALL")       # 곡선을 그려야 하므로 전 서브스텝

    # 볼을 놓아준다. 연직은 물론, 횡방향도 풀어 손가락 사이로 빠질 수 있게 한다.
    # 회전은 계속 구속한다 — 구의 회전은 형상을 바꾸지 않는 영모드라 풀면
    # 강성행렬이 특이해진다.
    mapdl.ddele(pilot, "UY")
    if lateral_free:
        mapdl.ddele(pilot, "UX")
        mapdl.ddele(pilot, "UZ")
    for lab in ("ROTX", "ROTY", "ROTZ"):
        mapdl.d(pilot, lab, 0)
    mapdl.allsel()

    # 무게를 -Y 로 램프. gmax kg 상당까지.
    #
    # tilt_deg 를 주면 하중을 손가락 사이 틈 방향으로 기울인다. 완전 대칭
    # 모델에서는 횡방향 합력이 정확히 0 이라 볼이 옆으로 빠지는 모드가
    # 아예 발생하지 못한다 (실제로 횡이동이 전 구간 0.0000 으로 나왔다).
    # 실제 그리퍼의 가공 공차·정렬 오차·편심을 이 기울임으로 대신한다.
    # 손가락이 0/120/240도 에 있으므로 틈은 60/180/300도. 180도 = -X 방향.
    W = gmax * 9.80665
    t = np.radians(tilt_deg)
    mapdl.f(pilot, "FY", -W * np.cos(t))
    if tilt_deg:
        mapdl.f(pilot, "FX", -W * np.sin(t))    # 180도 틈 쪽으로
    mapdl.nsubst(nsub, nsub * 20, nsub)
    mapdl.time(t_ramp0 + 1)

    # 마지막 하중 스텝은 발산할 수 있다. 발산 = 볼을 놓쳤다는 뜻이므로
    # 예외로 죽이지 않고 받아서 넘긴다.
    diverged = False
    try:
        mapdl.solve()
    except Exception as exc:
        diverged = True
        print(f"  [중력] 수렴 실패 — 볼을 놓쳤다는 신호다: "
              f"{type(exc).__name__}")
    mapdl.finish()
    return n_close, t_ramp0, diverged


def read_all(mapdl, pilot, n_close, closings, gmax, t_ramp0=None):
    """t_ramp0 = 중력 램프가 시작하는 TIME. 힘 전환 스텝이 있으면 밀린다."""
    if t_ramp0 is None:
        t_ramp0 = n_close
    mapdl.post1()
    nset = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))

    grip, ramp = [], []
    for s in range(1, nset + 1):
        mapdl.set(nset=s)
        lstp = int(mapdl.get_value("ACTIVE", 0, "SET", "LSTP"))
        tim = float(mapdl.get_value("ACTIVE", 0, "SET", "TIME"))

        if lstp <= n_close:
            per = []
            for k in range(3):
                mapdl.cmsel("S", f"BASE{k}")
                mapdl.fsum()
                fx = float(mapdl.get_value("FSUM", 0, "ITEM", "FX"))
                fz = float(mapdl.get_value("FSUM", 0, "ITEM", "FZ"))
                per.append(float(np.hypot(fx, fz)))
            mapdl.allsel()
            grip.append(dict(close_mm=closings[lstp - 1], f0=per[0], f1=per[1],
                             f2=per[2], total=sum(per)))
        elif tim > t_ramp0 + 1e-9:
            # 램프 구간 내 진행률 -> 걸린 중력 배수 -> kg 상당
            frac = tim - t_ramp0
            kg = frac * gmax
            uy = float(mapdl.get_value("NODE", pilot, "U", "Y"))
            ux = float(mapdl.get_value("NODE", pilot, "U", "X"))
            uz = float(mapdl.get_value("NODE", pilot, "U", "Z"))
            mapdl.allsel()
            mapdl.esel("S", "TYPE", "", 3)
            mapdl.etable("EP", "CONT", "PRES")
            mapdl.esort("ETAB", "EP", 0, 1)
            pmax = float(mapdl.get_value("SORT", "", "MAX"))
            mapdl.esel("R", "ETAB", "EP", 1e-12, 1e12)
            nclosed = int(mapdl.get_value("ELEM", 0, "COUNT"))
            # 손가락 최대 von Mises — 재료 한계에 근접하는지 본다
            mapdl.allsel()
            mapdl.esel("S", "TYPE", "", 1)
            mapdl.nsle("S")
            mapdl.nsort("S", "EQV")
            svm = float(mapdl.get_value("SORT", "", "MAX"))
            mapdl.allsel()
            ramp.append(dict(mass_kg=kg, weight_N=kg * 9.80665, svm_max_MPa=svm,
                             uy_mm=uy, ux_mm=ux, uz_mm=uz,
                             lateral_mm=float(np.hypot(ux, uz)),
                             n_closed=nclosed, pres_max_MPa=pmax))
    mapdl.finish()
    return grip, ramp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mu", type=float, default=0.6)
    ap.add_argument("--fkn", type=float, default=1.0)
    ap.add_argument("--size", type=float, default=1.5)
    ap.add_argument("--close", type=float, nargs="*",
                    default=[3.0, 4.0, 5.0, 5.7])
    ap.add_argument("--gmax", type=float, default=8.0,
                    help="중력을 몇 g 까지 램프할지 = 몇 kg 상당까지 볼지")
    ap.add_argument("--nsub", type=int, default=40)
    ap.add_argument("--nproc", type=int, default=4)
    ap.add_argument("--fix-lateral", action="store_true",
                    help="볼의 횡방향 이동을 구속한다 (기본은 풀어줌)")
    ap.add_argument("--grip-force", type=float, default=None,
                    help="밑동을 변위 고정 대신 이 반경력[N/손가락]으로 잡는다. "
                         "변위 고정은 볼이 손가락을 벌릴 수 없게 만들어 형상 "
                         "구속이 절대적이 된다. 실제 액추에이터는 유한한 힘으로 "
                         "쥐므로 이쪽이 실제에 가깝다. 조임 5.7mm 의 반력은 "
                         "손가락당 2.830 N.")
    ap.add_argument("--tilt-deg", type=float, default=0.0,
                    help="하중을 손가락 사이 틈 쪽으로 기울이는 각도. "
                         "완전 대칭 모델에서는 횡방향 합력이 0 이라 볼이 옆으로 "
                         "빠지는 모드가 생기지 않는다. 실제의 정렬 오차·편심을 "
                         "이것으로 대신한다.")
    args = ap.parse_args()

    mesh_inp = MSH_DIR / f"real15_3finger_{args.size}mm.inp"
    meta = json.loads((MSH_DIR / "real15_3finger_meta.json").read_text(
        encoding="utf-8"))
    ball = meta["ball"]

    print("3핑거 중력 하중 해석 — '아예 놓치는' 무게")
    print(f"  볼 중심 {ball['center']}  접촉 반지름 {ball['r_contact_mm']} mm")
    print(f"  mu={args.mu}  메쉬 {args.size}mm  조임 {args.close} mm")
    print(f"  중력 램프 0 -> {args.gmax:.0f} g  (= {args.gmax:.0f} kg 상당)")
    print(f"  볼 횡방향 {'구속' if args.fix_lateral else '자유'}")
    print()

    kill_stale()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mapdl = launch_mapdl(exec_file=ansys_exe(), run_location=run_dir("case_gravity"),
                         nproc=args.nproc, override=True, cleanup_on_exit=True)
    try:
        print("-- 모델 구성 --")
        pilot = build(mapdl, mesh_inp, ball["center"], args.mu, args.fkn)
        print("-- 1단계: 파지 --")
        n_close, t_ramp0, diverged = solve(
            mapdl, pilot, args.close, args.gmax, args.nsub,
            not args.fix_lateral, args.tilt_deg, args.grip_force)
        print("-- 후처리 --")
        grip, ramp = read_all(mapdl, pilot, n_close, args.close, args.gmax,
                              t_ramp0)

        # 하중이 실제로 걸렸는지 확인. 볼이 전혀 움직이지 않으면 하중이
        # 모델에 전달되지 않은 것이다 (강체 타겟에 파일럿이 없으면 이렇게 된다).
        # 원본 보고서가 "응력이 15자리까지 불변" 이었던 것과 같은 증상이며,
        # 검사 없이는 그럴듯한 표로 조용히 넘어간다.
        if ramp:
            moved = max(abs(r["uy_mm"]) for r in ramp)
            if moved < 1e-9:
                raise RuntimeError(
                    "볼이 전혀 움직이지 않았다 — 하중이 전달되지 않았다. "
                    "파일럿 절점 설정을 확인할 것.")
            print(f"   하중 전달 확인: 최대 처짐 {moved:.4f} mm")
    finally:
        try:
            mapdl.exit()
        except Exception:
            pass
        kill_stale()

    dg = pd.DataFrame(grip)
    dr = pd.DataFrame(ramp)
    tag = f"3finger_gravity_{args.size}mm_mu{args.mu}"
    dg.to_csv(OUT_DIR / f"{tag}_grip.csv", index=False, encoding="utf-8-sig")
    dr.to_csv(OUT_DIR / f"{tag}_ramp.csv", index=False, encoding="utf-8-sig")

    print()
    print("=" * 76)
    print("  파지력")
    print("=" * 76)
    for _, r in dg.iterrows():
        print(f"  조임 {r['close_mm']:.2f} mm  손가락당 {r['f0']:.3f} N  "
              f"합계 {r['total']:.3f} N")

    print()
    print("=" * 76)
    print("  중력 램프 — 볼이 얼마나 처지는가")
    print("=" * 76)
    print(f"  {'질량[kg]':>9} {'무게[N]':>9} {'연직처짐[mm]':>12} "
          f"{'횡이동[mm]':>11} {'닫힌접촉':>9} {'Pmax[MPa]':>10} {'SVM[MPa]':>9}")
    for _, r in dr.iterrows():
        print(f"  {r['mass_kg']:9.3f} {r['weight_N']:9.3f} "
              f"{r['uy_mm']:12.4f} {r['lateral_mm']:11.4f} "
              f"{int(r['n_closed']):9d} {r['pres_max_MPa']:10.4f} "
              f"{r['svm_max_MPa']:9.3f}")

    print()
    if len(dr):
        last = dr.iloc[-1]
        print(f"  마지막으로 수렴한 하중 = {last['mass_kg']:.3f} kg "
              f"({last['weight_N']:.2f} N)")
        print(f"    그때 볼 처짐 {last['uy_mm']:.3f} mm, "
              f"횡이동 {last['lateral_mm']:.3f} mm")
        if diverged:
            print(f"  → 이 하중을 넘기면서 평형을 찾지 못했다. "
                  f"'아예 놓치는' 무게 상한 ≈ {last['mass_kg']:.2f} kg")
        else:
            print(f"  → {args.gmax:.0f} kg 까지 전부 수렴했다. "
                  f"상한이 이보다 높으므로 --gmax 를 키워 다시 볼 것.")
    print(f"\n저장: {tag}_grip.csv / {tag}_ramp.csv")


if __name__ == "__main__":
    main()
