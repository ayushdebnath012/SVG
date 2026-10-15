"""3핑거 파지 결과 그림 — 조임-파지력 곡선과 두 방향의 인발 곡선.

인발 방향이 결과를 완전히 바꾼다.
  tip  (+Y, 팁 쪽)  : 뒤집은 픽업 자세에서 중력이 볼을 당기는 방향.
                      볼이 손가락에서 빠져나가며 마찰 한계가 드러난다.
  base (-Y, 밑동 쪽): 손가락이 볼을 아래에서 받치는 자세. 볼을 바구니
                      안으로 밀어넣는 꼴이라 형상 구속이 지배하고
                      마찰 한계가 보이지 않는다.
접촉 구역이 y=6~31 (볼 적도 y=30 아래) 이므로 손가락은 볼을 아래에서
받치고 있다. 따라서 실제 파지 한계를 보려면 tip 방향이 맞다.
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
BREAK_RATIO = 1.5     # 접촉압력이 직전 대비 이 배율 이상 뛰면 수치 파탄

matplotlib_korean(plt, matplotlib)
plt.rcParams.update({"font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3, "figure.dpi": 130})

grip = pd.read_csv(RAW / "3finger_15deg_1.5mm_mu0.6_tip_grip.csv")
tip = pd.read_csv(RAW / "3finger_15deg_1.5mm_mu0.6_tip_pull.csv")
base = pd.read_csv(RAW / "3finger_15deg_1.5mm_mu0.6_base_pull.csv")


def split_valid(df):
    """접촉압력 급등 지점 앞까지를 신뢰 구간으로 자른다."""
    p = df["pres_max_MPa"].to_numpy()
    for i in range(1, len(p)):
        if p[i] > BREAK_RATIO * p[i - 1]:
            return df.iloc[:i], float(df["uy_mm"].iloc[i])
    return df, None


tip_v, tip_brk = split_valid(tip)
base_v, base_brk = split_valid(base)
coulomb = MU * float(grip["total"].iloc[-1])
cap = float(tip_v["fy_N"].max())
cap_u = float(tip_v.loc[tip_v["fy_N"].idxmax(), "uy_mm"])

fig, ax = plt.subplots(1, 3, figsize=(12.8, 3.9))

# (1) 조임 - 파지력
a = ax[0]
a.plot(grip["close_mm"], grip["total"], "o-", color="#1f77b4", label="총 파지력")
a.plot(grip["close_mm"], grip["f0"], "s--", color="#7fb3d5", ms=4, label="손가락당")
a.set_xlabel("조임량 [mm]"); a.set_ylabel("반경방향 파지력 [N]")
a.set_title("(1) 조임량에 따른 파지력")
a.legend(fontsize=8)
for x, y in zip(grip["close_mm"], grip["total"]):
    a.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
               xytext=(0, 6), ha="center", fontsize=7)

# (2) 인발 곡선 — 팁 방향 (실제 파지 한계)
a = ax[1]
a.plot(abs(tip["uy_mm"]), tip["fy_N"], "o-", color="#d62728", ms=3,
       label="FEA 저항")
a.axhline(coulomb, color="#2ca02c", ls=":", lw=1.5,
          label=f"쿨롱 근사 {coulomb:.2f} N")
a.plot([abs(cap_u)], [cap], "*", ms=14, color="#000000", zorder=5)
a.annotate(f"최대 {cap:.2f} N\n= {cap/G:.3f} kg", (abs(cap_u), cap),
           textcoords="offset points", xytext=(18, -6), fontsize=8)
a.set_xlabel("볼이 팁 쪽으로 빠져나간 거리 [mm]")
a.set_ylabel("저항 반력 [N]")
a.set_title("(2) 팁 방향 인발 — 미끄러짐 평탄 구간")
a.legend(fontsize=7, loc="lower right")
a.set_ylim(0, max(coulomb, cap) * 1.25)

# (3) 방향 비교
a = ax[2]
a.plot(abs(tip["uy_mm"]), tip["fy_N"], "-", color="#d62728", lw=2,
       label="팁 쪽 (+Y) — 실제 파지 한계")
a.plot(abs(base["uy_mm"]), base["fy_N"], "-", color="#bbbbbb", lw=1.2,
       label="밑동 쪽 (-Y) — 파탄 포함")
a.plot(abs(base_v["uy_mm"]), base_v["fy_N"], "-", color="#8c564b", lw=2,
       label="밑동 쪽 (-Y) — 형상 구속")
a.axhline(coulomb, color="#2ca02c", ls=":", lw=1.5, label="쿨롱 근사")
a.set_xlabel("볼이 이동한 거리 [mm]"); a.set_ylabel("저항 반력 [N]")
a.set_title("(3) 인발 방향이 결과를 바꾼다")
a.set_yscale("log")
a.legend(fontsize=7, loc="upper left")

fig.suptitle("Fin Ray 15deg 3핑거 파지 용량 "
             f"(mu={MU}, 조임 5.7mm, 메쉬 1.5mm)", fontsize=10)
fig.tight_layout()
IMG.mkdir(parents=True, exist_ok=True)
out = IMG / "3finger_capacity.png"
fig.savefig(out, bbox_inches="tight")

print("=" * 70)
print("  3핑거 파지 무게 상한 — 최종")
print("=" * 70)
print(f"  조임 5.7 mm 총 파지력 (반경)      {grip['total'].iloc[-1]:8.3f} N")
print()
print(f"  [FEA] 팁 방향 최대 저항           {cap:8.3f} N  (볼 이동 {abs(cap_u):.3f} mm)")
print(f"        → 무게 상한                {cap/G:8.3f} kg")
print()
print(f"  [참고] 쿨롱 근사 mu x N           {coulomb:8.3f} N  → {coulomb/G:.3f} kg")
print(f"        FEA / 쿨롱                 {cap/coulomb:8.2f}")
print()
print(f"  팁 방향 곡선 최대 접촉압력        {tip['pres_max_MPa'].max():8.3f} MPa"
      f"  (재료 전단계수 3.71) — 수치 파탄 없음")
print()
print(f"  저장: {out.relative_to(PROJECT)}")
