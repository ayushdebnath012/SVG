"""
3핑거 파지 → 인발 과정 애니메이션 (GIF).

2단계 구성
  1) MAPDL 로 결과 파일에서 절점 변위를 뽑아 .npz 로 저장
  2) 저장한 변위와 .inp 메쉬로 pyvista 렌더링 → GIF

왜 이렇게 하는가
  ansys-mapdl-reader(0.56) 로 이 결과 파일을 직접 읽으면 변위가 1e307 급
  쓰레기 값과 NaN 으로 나온다 — 구버전 리더가 MAPDL 2026 R1 형식을 제대로
  파싱하지 못한다. MAPDL 자체 리더를 쓰고, 메쉬는 우리가 만든 .inp 를 직접
  파싱해 중간에 못 믿을 단계를 없앤다.

  1) 은 라이선스가 필요하고 느리므로 결과를 캐시한다. 2) 만 반복하면 된다.

사용법
    python 40_animate.py                 # 캐시 있으면 렌더만
    python 40_animate.py --extract       # 변위 다시 추출
"""

import argparse
import os
import subprocess
import time
from pathlib import Path

import numpy as np
import pyvista as pv
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (PROJECT, ansys_exe, run_dir, kill_stale,  # noqa: E402
                    korean_font)

MESH_INP = PROJECT / "02_mesh" / "msh" / "real15_3finger_1.5mm.inp"
OUT_DIR = PROJECT / "06_image" / "figures"
CACHE = PROJECT / "05_results" / "processed" / "3finger_disp.npz"
RUN_LOC = run_dir("case_3finger")

BALL_C = np.array([40.0, 30.0, -9.0])
BALL_R = 40.0
BALL_YMIN, BALL_YMAX = 0.0, 60.0
N_CLOSE = 4
CLOSINGS = [3.0, 4.0, 5.0, 5.7]


# ---------------------------------------------------------------- 메쉬 파싱

def parse_inp(path):
    """우리가 쓴 NBLOCK/EBLOCK 을 되읽는다. 절점 번호는 1..N 연속이다."""
    nodes, tets = [], []
    mode = None
    with path.open(encoding="ascii") as f:
        for line in f:
            s = line.rstrip("\n")
            if s.startswith("NBLOCK"):
                mode = "n_fmt"; continue
            if s.startswith("EBLOCK"):
                mode = "e_fmt"; continue
            if s.startswith("CMBLOCK"):
                mode = None; continue
            if mode == "n_fmt":
                mode = "n"; continue
            if mode == "e_fmt":
                mode = "e"; continue
            if mode == "n":
                if s.startswith("N,R5.3"):
                    mode = None; continue
                nodes.append([float(s[27:48]), float(s[48:69]), float(s[69:90])])
            elif mode == "e":
                if s.strip() == "-1":
                    mode = None; continue
                v = [int(s[i:i + 9]) for i in range(0, len(s.rstrip()), 9)]
                tets.append(v[11:15])
    return np.array(nodes), np.array(tets, dtype=np.int64) - 1


def build_grid(nodes, tets):
    cells = np.hstack([np.full((len(tets), 1), 4), tets]).ravel()
    ctypes = np.full(len(tets), pv.CellType.TETRA, dtype=np.uint8)
    return pv.UnstructuredGrid(cells, ctypes, nodes)


def make_ball():
    s = pv.Sphere(radius=BALL_R, center=BALL_C, theta_resolution=64,
                  phi_resolution=64)
    s = s.clip(normal="y", origin=(0, BALL_YMIN, 0), invert=False)
    s = s.clip(normal="y", origin=(0, BALL_YMAX, 0), invert=True)
    return s


# ------------------------------------------------------------- 변위 추출

def extract():
    """MAPDL 로 세트별 절점 변위를 뽑아 캐시한다."""
    from ansys.mapdl.core import launch_mapdl

    kill_stale()
    mapdl = launch_mapdl(exec_file=ansys_exe(), run_location=RUN_LOC, nproc=2,
                         override=True, cleanup_on_exit=True, jobname="anim")
    try:
        mapdl.post1()
        mapdl.file("file", "rst")
        nsets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
        print(f"결과 세트 {nsets}개에서 변위 추출")
        disps, times, lsteps = [], [], []
        for s in range(1, nsets + 1):
            mapdl.set(nset=s)
            mapdl.allsel()
            d = mapdl.post_processing.nodal_displacement("all")
            disps.append(np.asarray(d, dtype=np.float64))
            times.append(float(mapdl.get_value("ACTIVE", 0, "SET", "TIME")))
            lsteps.append(int(mapdl.get_value("ACTIVE", 0, "SET", "LSTP")))
            if s % 10 == 0 or s == nsets:
                print(f"  {s}/{nsets}")
        nnum = np.asarray(mapdl.mesh.nnum, dtype=np.int64)
    finally:
        try:
            mapdl.exit()
        except Exception:
            pass
        kill_stale()

    arr = np.stack(disps)          # (nsets, nnode, 3)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, disp=arr, nnum=nnum,
                        time=np.array(times), lstep=np.array(lsteps))
    print(f"캐시 저장: {CACHE.name}  shape={arr.shape}")
    return arr, nnum


# ------------------------------------------------------------------ 렌더

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true", help="변위 재추출")
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--size", type=int, nargs=2, default=[960, 720])
    args = ap.parse_args()

    if args.extract or not CACHE.exists():
        disp, nnum = extract()
        z = np.load(CACHE)
    else:
        z = np.load(CACHE)
        disp, nnum = z["disp"], z["nnum"]
        print(f"캐시 사용: {CACHE.name}  shape={disp.shape}")

    # 값 검증 — 리더 문제로 쓰레기가 들어오면 여기서 걸린다
    if not np.isfinite(disp).all():
        raise RuntimeError("변위에 NaN/Inf 가 있다")
    if np.abs(disp).max() > 100:
        raise RuntimeError(f"변위 최대 {np.abs(disp).max():.3g} mm — 비정상")
    print(f"변위 범위 {disp.min():.3f} ~ {disp.max():.3f} mm  (정상)")

    nodes, tets = parse_inp(MESH_INP)
    print(f"메쉬: 절점 {len(nodes):,}  요소 {len(tets):,}")
    grid = build_grid(nodes, tets)
    surf = grid.extract_surface(algorithm="dataset_surface")

    # 변위 배열의 행 -> 절점 번호. 손가락 절점은 1..len(nodes).
    lut = np.full(int(nnum.max()) + 1, -1, dtype=np.int64)
    lut[nnum] = np.arange(len(nnum))
    surf_ids = np.asarray(surf.point_data["vtkOriginalPointIds"]) + 1
    rows = lut[surf_ids]
    pilot_row = lut[int(nnum.max())]
    if (rows < 0).any():
        raise RuntimeError("변위에 없는 절점이 있다")

    ball0 = make_ball()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    kf = korean_font()
    font_file = str(kf) if kf else None

    probe = pv.Plotter(off_screen=True, window_size=args.size)
    probe.add_mesh(surf); probe.add_mesh(ball0)
    probe.view_vector((1.35, 0.45, 1.0), viewup=(0, 1, 0))
    probe.camera.zoom(0.92)
    CAM = probe.camera_position
    probe.close()

    nsets = disp.shape[0]
    frames = []
    for i in range(nsets):
        d = disp[i][rows]
        warped = surf.copy()
        warped.points = surf.points + d
        warped.point_data["mag"] = np.linalg.norm(d, axis=1)

        pd_ = disp[i][pilot_row]
        ball = ball0.copy()
        ball.points = ball0.points + pd_

        if i < N_CLOSE:
            label = f"1단계 파지 — 조임 {CLOSINGS[i]:.1f} mm"
            sub = f"손가락당 파지력 {[0.662, 1.040, 1.722, 2.830][i]:.2f} N"
        else:
            label = "2단계 인발 — 볼이 팁 쪽으로 빠져나감"
            sub = f"볼 이동 {pd_[1]:+.3f} mm"

        p = pv.Plotter(off_screen=True, window_size=args.size)
        p.set_background("white")
        p.add_mesh(ball, color="#9fb6cc", opacity=0.5, smooth_shading=True)
        p.add_mesh(warped, scalars="mag", cmap="turbo", clim=[0, 7.0],
                   smooth_shading=True, show_edges=False,
                   # 컬러바 제목은 ASCII 로 둔다. add_scalar_bar 는 font_file 을
                   # 받지 않아 한글을 넣으면 글리프가 깨진다.
                   scalar_bar_args=dict(title="Displacement [mm]", n_labels=4,
                                        vertical=True, position_x=0.88,
                                        position_y=0.25, height=0.5, width=0.05,
                                        title_font_size=13, label_font_size=11,
                                        color="black"))
        txt = dict(font_file=font_file) if font_file else {}
        p.add_text(label, position="upper_left", font_size=11, color="black", **txt)
        p.add_text(sub, position=(0.02, 0.895), viewport=True, font_size=10,
                   color="#444444", **txt)
        p.add_text(f"{i+1}/{nsets}", position="lower_right", font_size=9,
                   color="#999999")
        p.camera_position = CAM
        frames.append(Image.fromarray(p.screenshot(return_img=True)))
        p.close()
        if (i + 1) % 10 == 0 or i == nsets - 1:
            print(f"  프레임 {i+1}/{nsets}")

    dur = [int(1000 / args.fps)] * len(frames)
    for k in range(N_CLOSE):
        dur[k] = 700                # 파지 단계는 천천히
    dur[N_CLOSE - 1] = 1200         # 파지 완료에서 멈춤
    dur[-1] = 1800

    out = OUT_DIR / "3finger_grip_pullout.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=dur, loop=0, optimize=True)
    print(f"\n저장: {out.relative_to(PROJECT)}  "
          f"({out.stat().st_size/1024**2:.1f} MB, {len(frames)} 프레임)")

    for name, i in (("closed", N_CLOSE - 1), ("pull_peak", N_CLOSE + 6),
                    ("pull_end", nsets - 1)):
        frames[i].save(OUT_DIR / f"3finger_{name}.png")

    # --- 보고서용 깨끗한 정지 이미지 ---
    # 애니메이션 프레임에는 단계 설명과 프레임 번호가 박혀 있어 보고서에
    # 그대로 쓰기 어렵다. 오버레이 없이 더 꽉 채워 다시 렌더한다.
    tight = pv.Plotter(off_screen=True, window_size=args.size)
    tight.add_mesh(surf); tight.add_mesh(ball0)
    tight.view_vector((1.35, 0.45, 1.0), viewup=(0, 1, 0))
    tight.camera.zoom(1.55)
    CAM_T = tight.camera_position
    tight.close()

    for name, i in (("clean_closed", N_CLOSE - 1),
                    ("clean_pull_end", nsets - 1)):
        d = disp[i][rows]
        warped = surf.copy()
        warped.points = surf.points + d
        warped.point_data["mag"] = np.linalg.norm(d, axis=1)
        ball = ball0.copy()
        ball.points = ball0.points + disp[i][pilot_row]

        p = pv.Plotter(off_screen=True, window_size=args.size)
        p.set_background("white")
        p.add_mesh(ball, color="#9fb6cc", opacity=0.5, smooth_shading=True)
        p.add_mesh(warped, scalars="mag", cmap="turbo", clim=[0, 7.0],
                   smooth_shading=True,
                   # 컬러바 제목은 ASCII 로 둔다. add_scalar_bar 는 font_file 을
                   # 받지 않아 한글을 넣으면 글리프가 깨진다.
                   scalar_bar_args=dict(title="Displacement [mm]", n_labels=4,
                                        vertical=True, position_x=0.9,
                                        position_y=0.3, height=0.45, width=0.04,
                                        title_font_size=12, label_font_size=10,
                                        color="black"))
        p.camera_position = CAM_T
        Image.fromarray(p.screenshot(return_img=True)).save(
            OUT_DIR / f"3finger_{name}.png")
        p.close()
    print("보고서용 깨끗한 정지 이미지 2장 저장")


if __name__ == "__main__":
    main()
