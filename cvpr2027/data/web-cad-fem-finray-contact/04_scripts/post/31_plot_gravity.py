"""
중력 하중 해석 종합 그림.

패널
  (1) 조임량 - 파지력
  (2) 중력 하중 - 볼 처짐 (조임량별), 실측 1 kg 표시
  (3) 인발 방향 비교 (+Y 마찰 지배 vs -Y 형상 구속)
  (4) 접촉압력 - 수치 건전성 판정
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROJECT, matplotlib_korean  # noqa: E402

RAW = PROJECT / "05_results" / "raw"
IMG = PROJECT / "06_image" / "plot"
G = 9.80665
MU = 0.6
SHEAR_MOD = 3.71          # MPa — NinjaFlex 전단계수
MEASURED_KG = 1.0         # 실측 파지 상한
BREAK_RATIO = 1.5

matplotlib_korean(plt, matplotlib)
plt.rcParams.update({"font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3, "figure.dpi": 130})


def load(name):
    p = RAW / name
    return pd.read_csv(p) if p.exists() else None


def first_break(df, col="pres_max_MPa"):
    """신뢰 구간의 끝을 찾는다.

    두 기준 중 먼저 걸리는 쪽:
      (a) 접촉압력이 직전 대비 1.5배 이상 급등 — 요소 뒤집힘의 전형적 징후
      (b) 접촉압력이 재료 전단계수를 넘음 — 이 지점부터는 물리적으로 의심스럽다
    (a) 만 쓰면 압력이 완만하게 오르는 경우를 놓친다 (실제로 놓쳤다).
    """
    p = df[col].to_numpy()
    for i in range(1, len(p)):
        if p[i] > BREAK_RATIO * p[i - 1] or p[i] > SHEAR_MOD:
            return i
    return None


grip = load("3finger_15deg_1.5mm_mu0.6_tip_grip.csv")
tip = load("3finger_15deg_1.5mm_mu0.6_tip_pull.csv")
base = load("3finger_15deg_1.5mm_mu0.6_base_pull.csv")
g57 = load("3finger_gravity_close5.7_tilt10_ramp.csv")
g30 = load("3finger_gravity_close3.0_tilt10_ramp.csv")

fig, ax = plt.subplots(2, 2, figsize=(11.5, 8.0))

# ---------------------------------------------- (1) 조임 - 파지력
a = ax[0, 0]
a.plot(grip["close_mm"], grip["total"], "o-", color="#1f77b4", label="총 파지력")
a.plot(grip["close_mm"], grip["f0"], "s--", color="#7fb3d5", ms=4, label="손가락당")
for x, y in zip(grip["close_mm"], grip["total"]):
    a.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
               xytext=(0, 6), ha="center", fontsize=7)
a.set_xlabel("조임량 [mm]"); a.set_ylabel("반경방향 파지력 [N]")
a.set_title("(1) 조임량이 파지력을 지배한다")
a.legend(fontsize=8)

# ---------------------------------------------- (2) 중력 - 처짐
a = ax[0, 1]
for df, lab, c in ((g57, "조임 5.7 mm", "#d62728"),
                   (g30, "조임 3.0 mm", "#ff7f0e")):
    if df is None:
        continue
    b = first_break(df)
    a.plot(df["mass_kg"], -df["uy_mm"], "-", color=c, lw=1, alpha=0.35)
    v = df.iloc[:b] if b else df
    a.plot(v["mass_kg"], -v["uy_mm"], "o-", color=c, ms=2.5, label=lab)
    if b is not None:
        a.plot(df["mass_kg"].iloc[b], -df["uy_mm"].iloc[b], "x", color=c, ms=9)
a.axvline(MEASURED_KG, color="#2ca02c", ls="--", lw=1.6)
a.text(MEASURED_KG, a.get_ylim()[1] * 0.92, " 실측 1 kg", color="#2ca02c",
       fontsize=8.5, va="top")
a.set_xlabel("볼 질량 [kg]"); a.set_ylabel("볼이 내려앉은 거리 [mm]")
a.set_title("(2) 중력 하중에 따른 볼 처짐  (x = 수치 파탄 개시)")
a.legend(fontsize=8, loc="lower right")

# ---------------------------------------------- (3) 방향 비교
a = ax[1, 0]
a.plot(abs(tip["uy_mm"]), tip["fy_N"], "-", color="#d62728", lw=2,
       label="+Y 팁 쪽 — 마찰 지배")
bb = first_break(base)
a.plot(abs(base["uy_mm"]), base["fy_N"], "-", color="#cccccc", lw=1)
bv = base.iloc[:bb] if bb else base
a.plot(abs(bv["uy_mm"]), bv["fy_N"], "-", color="#8c564b", lw=2,
       label="-Y 밑동 쪽 — 형상 구속")
a.axhline(MU * grip["total"].iloc[-1], color="#2ca02c", ls=":", lw=1.5,
          label=f"쿨롱 근사 {MU*grip['total'].iloc[-1]:.2f} N")
a.axhline(MEASURED_KG * G, color="#1f77b4", ls="--", lw=1.4,
          label=f"실측 1 kg = {MEASURED_KG*G:.2f} N")
a.set_yscale("log")
a.set_xlabel("볼이 이동한 거리 [mm]"); a.set_ylabel("저항 반력 [N]")
a.set_title("(3) 인발 방향이 30배를 가른다")
a.legend(fontsize=7.5, loc="upper left")

# ---------------------------------------------- (4) 접촉압력
a = ax[1, 1]
for df, lab, c in ((g57, "조임 5.7 mm", "#d62728"),
                   (g30, "조임 3.0 mm", "#ff7f0e")):
    if df is None:
        continue
    a.semilogy(df["mass_kg"], df["pres_max_MPa"], "o-", ms=2.5, color=c, label=lab)
a.axhline(SHEAR_MOD, color="#9467bd", ls=":", lw=1.6,
          label=f"재료 전단계수 {SHEAR_MOD} MPa")
a.axvline(MEASURED_KG, color="#2ca02c", ls="--", lw=1.4)
a.set_xlabel("볼 질량 [kg]"); a.set_ylabel("최대 접촉압력 [MPa]")
a.set_title("(4) 접촉압력 — 어디까지 믿을 수 있나")
a.legend(fontsize=8)

fig.suptitle("Fin Ray 15deg 3핑거 — 중력 하중 해석 "
             f"(mu={MU}, 메쉬 1.5mm, 하중 10도 기울임)", fontsize=11)
fig.tight_layout()
IMG.mkdir(parents=True, exist_ok=True)
out = IMG / "3finger_gravity.png"
fig.savefig(out, bbox_inches="tight")

# ------------------------------------------------------------ 요약
print("=" * 72)
print("  중력 하중 해석 요약")
print("=" * 72)
for df, lab in ((g57, "조임 5.7 mm"), (g30, "조임 3.0 mm")):
    if df is None:
        print(f"  {lab}: (데이터 없음 — 아직 계산 중)")
        continue
    b = first_break(df)
    v = df.iloc[:b] if b else df
    at1 = df.iloc[(df["mass_kg"] - MEASURED_KG).abs().idxmin()]
    print(f"  {lab}")
    print(f"    실측 1 kg 지점   처짐 {-at1['uy_mm']:.3f} mm, "
          f"압력 {at1['pres_max_MPa']:.3f} MPa")
    if b is not None:
        print(f"    수치 파탄 개시   {df['mass_kg'].iloc[b]:.2f} kg "
              f"(압력 {df['pres_max_MPa'].iloc[b-1]:.2f} -> "
              f"{df['pres_max_MPa'].iloc[b]:.2f} MPa)")
    print(f"    신뢰 구간 내 최대 {v['mass_kg'].max():.2f} kg 까지 볼을 놓치지 않음")
print()
print(f"  저장: {out.relative_to(PROJECT)}")
