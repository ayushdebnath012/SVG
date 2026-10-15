r"""
환경 설정 — PC 를 옮겨도 스크립트를 고치지 않아도 되게 한다.

각 스크립트 맨 위에서:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from config import ANSYS_EXE, WORK_ROOT, PROJECT, korean_font, kill_stale

환경변수로 덮어쓸 수 있다 (자동 탐지가 실패하거나 다른 버전을 쓰고 싶을 때).

    set FINRAY_ANSYS_EXE=D:\Ansys\v252\ansys\bin\winx64\ANSYS252.exe
    set FINRAY_WORK=D:\ANSYS_work
"""

import os
import subprocess
import time
from pathlib import Path

# 프로젝트 루트 = 이 파일의 상위 폴더 (04_scripts 의 부모)
PROJECT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------- ANSYS 실행파일

def _find_ansys_exe():
    """설치된 MAPDL 실행파일을 찾는다. 최신 버전을 우선한다.

    파일명이 버전마다 다르다 (ANSYS261.exe, ANSYS252.exe ...). 버전을 하드코딩하면
    다른 PC 에서 바로 깨지므로 훑어서 찾는다.
    """
    env = os.environ.get("FINRAY_ANSYS_EXE")
    if env:
        p = Path(env)
        if not p.exists():
            raise FileNotFoundError(f"FINRAY_ANSYS_EXE 가 가리키는 파일이 없다: {p}")
        return p

    roots = []
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                 os.environ.get("ProgramW6432", r"C:\Program Files"),
                 r"C:\Program Files", r"D:\Program Files"):
        for flavor in ("ANSYS Inc/ANSYS Student", "ANSYS Inc"):
            roots.append(Path(base) / flavor)

    # 환경변수 ANSYSxxx_DIR 도 단서가 된다
    for k, v in os.environ.items():
        if k.startswith("ANSYS") and k.endswith("_DIR") and v:
            roots.append(Path(v).parent)

    found = []
    for root in roots:
        if not root.exists():
            continue
        for exe in root.glob("v*/ansys/bin/winx64/ANSYS*.exe"):
            name = exe.stem.upper()
            if name.startswith("ANSYS") and name[5:].isdigit():
                found.append((int(name[5:]), exe))
    if not found:
        raise FileNotFoundError(
            "MAPDL 실행파일을 찾지 못했다. 환경변수로 직접 지정할 것:\n"
            r"  set FINRAY_ANSYS_EXE=C:\Program Files\ANSYS Inc\ANSYS Student"
            r"\v261\ansys\bin\winx64\ANSYS261.exe")
    found.sort(reverse=True)
    return found[0][1]


ANSYS_EXE = None            # 필요할 때만 찾도록 지연 평가 (아래 함수 사용)


def ansys_exe():
    global ANSYS_EXE
    if ANSYS_EXE is None:
        ANSYS_EXE = _find_ansys_exe()
    return str(ANSYS_EXE)


# --------------------------------------------------------------- 작업 디렉터리

def _work_root():
    """솔버 작업 폴더의 뿌리.

    프로젝트 폴더(OneDrive, 한글·공백 경로) 안에서 솔버를 돌리면 동기화 잠금
    충돌이 나고 비ASCII 경로에서 문제가 생긴다. 반드시 밖에 둔다.
    """
    env = os.environ.get("FINRAY_WORK")
    if env:
        return Path(env)
    # 프로젝트가 있는 드라이브에 만든다
    drive = Path(PROJECT.anchor)
    return drive / "ANSYS_work" / "summer4_1_run"


WORK_ROOT = _work_root()


def run_dir(name):
    """케이스별 작업 폴더를 만들어 경로를 돌려준다."""
    d = WORK_ROOT / name
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


# ------------------------------------------------------------------- 한글 폰트

def korean_font():
    """한글 글리프가 있는 TTF 경로. 없으면 None.

    matplotlib/pyvista/reportlab 기본 폰트에는 한글이 없어 전부 깨진다.
    """
    env = os.environ.get("FINRAY_KR_FONT")
    if env and Path(env).exists():
        return Path(env)
    win = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for name in ("malgun.ttf", "NanumGothic.ttf", "gulim.ttc", "batang.ttc"):
        p = win / name
        if p.exists():
            return p
    return None


def korean_font_bold():
    env = os.environ.get("FINRAY_KR_FONT_BOLD")
    if env and Path(env).exists():
        return Path(env)
    win = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for name in ("malgunbd.ttf", "NanumGothicBold.ttf"):
        p = win / name
        if p.exists():
            return p
    return korean_font()


def matplotlib_korean(plt, matplotlib):
    """matplotlib 에 한글 폰트를 물린다. 설치된 것 중 먼저 잡히는 것을 쓴다."""
    for cand in ("Malgun Gothic", "NanumGothic", "Gulim", "Batang", "AppleGothic"):
        if any(f.name == cand for f in matplotlib.font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = cand
            break
    plt.rcParams["axes.unicode_minus"] = False


# ------------------------------------------------------------ 임시 폴더

def scratch(sub=""):
    """중간 산출물용 임시 폴더. 프로젝트 밖(작업 디렉터리 아래)에 둔다."""
    d = WORK_ROOT / "_scratch" / sub if sub else WORK_ROOT / "_scratch"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------- 좀비 프로세스 정리

def kill_stale():
    """학생용 라이선스는 동시 세션이 1개다.

    죽은 MAPDL 프로세스가 라이선스를 물고 있으면 다음 실행이
    "capability SOLUTION was not ordered" 로 실패한다. lock 파일도 함께 지운다.
    """
    for exe in ("ANSYS.exe", "ANSYS261.exe", "ANSYS252.exe", "ANSYS242.exe"):
        subprocess.run(["taskkill", "/F", "/IM", exe],
                       capture_output=True, check=False)
    time.sleep(2)
    if WORK_ROOT.exists():
        for lock in WORK_ROOT.rglob("file.lock"):
            try:
                os.remove(lock)
            except OSError:
                pass


if __name__ == "__main__":
    print("프로젝트      ", PROJECT)
    print("작업 디렉터리 ", WORK_ROOT)
    print("한글 폰트     ", korean_font())
    try:
        print("MAPDL         ", ansys_exe())
    except FileNotFoundError as e:
        print("MAPDL          [못 찾음]", e)
