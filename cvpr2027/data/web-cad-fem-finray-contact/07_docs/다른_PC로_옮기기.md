# 다른 PC 에서 이어서 하기

## 요약

옮길 것은 **프로젝트 폴더 하나**뿐이다. 나머지(가상환경, 솔버 작업 폴더)는
새 PC 에서 다시 만든다. 경로는 스크립트가 자동으로 찾으므로 **코드를 고칠
필요가 없다.**

---

## 1. 새 PC 에 필요한 것

| 항목 | 비고 |
|---|---|
| Ansys Student (또는 상용) | 버전 무관 — 스크립트가 설치된 버전을 자동 탐지 |
| Python 3.10 이상 | |
| 한글 TTF 폰트 | Windows 면 맑은 고딕이 이미 있다 |
| 디스크 여유 20 GB 이상 | 결과 파일(.rst)이 케이스당 수 GB |

Ansys 버전이 다르면 절점/요소 한도나 기본 설정이 다를 수 있다. Student 는
**128,000 요소 한도**가 있고 본 모델은 115,646 개(90%)를 쓴다.

---

## 2. 옮길 것 / 안 옮길 것

### 옮긴다 — 프로젝트 폴더 전체

```
summer4_1/
├─ 01_geometry/     STEP 원본  (필수)
├─ 02_mesh/         메쉬 .inp  (없으면 재생성 가능)
├─ 04_scripts/      스크립트   (필수)
├─ 05_results/      CSV, 변위 캐시 .npz
├─ 06_image/        그림, GIF
└─ 07_docs/         보고서, 기록
```

용량이 문제되면 `02_mesh/*.inp` 와 `06_image` 는 빼도 된다 — 스크립트로
다시 만들 수 있다. `05_results/processed/3finger_disp.npz` 는 **가져가는 것을
권한다.** 이게 있으면 애니메이션을 라이선스 없이 다시 뽑을 수 있다.

### 안 옮긴다

- `C:\ANSYS_work\venv` — 새로 만든다 (경로가 박혀 있어 복사해도 안 된다)
- `C:\ANSYS_work\summer4_1_run` — 솔버 중간 파일. 수 GB 이고 재생성된다

---

## 3. 새 PC 설정 (약 10분)

```powershell
# (1) 가상환경 — 프로젝트 폴더 '밖'에 만든다
python -m venv C:\ANSYS_work\venv

# (2) 패키지
C:\ANSYS_work\venv\Scripts\python.exe -m pip install -r `
    "<프로젝트경로>\04_scripts\requirements.txt"

# (3) 확인 — 경로가 제대로 잡히는지
C:\ANSYS_work\venv\Scripts\python.exe "<프로젝트경로>\04_scripts\config.py"
```

(3) 의 출력이 이렇게 나오면 준비 끝이다.

```
프로젝트       ...\summer4_1
작업 디렉터리  C:\ANSYS_work\summer4_1_run
한글 폰트      C:\WINDOWS\Fonts\malgun.ttf
MAPDL          C:\Program Files\ANSYS Inc\ANSYS Student\v261\...\ANSYS261.exe
```

`MAPDL [못 찾음]` 이 나오면 환경변수로 직접 지정한다.

```powershell
$env:FINRAY_ANSYS_EXE = "D:\Ansys\v252\ansys\bin\winx64\ANSYS252.exe"
```

---

## 4. 환경변수 (필요할 때만)

| 변수 | 용도 | 예 |
|---|---|---|
| `FINRAY_ANSYS_EXE` | MAPDL 실행파일 직접 지정 | `D:\...\ANSYS252.exe` |
| `FINRAY_WORK` | 솔버 작업 폴더 위치 | `D:\ANSYS_work` |
| `FINRAY_KR_FONT` | 한글 폰트 직접 지정 | `C:\Windows\Fonts\malgun.ttf` |

전부 선택 사항이다. 지정하지 않으면 자동으로 찾는다.

**`FINRAY_WORK` 는 SSD 여유가 있는 드라이브로 지정하는 것을 권한다.**
결과 파일이 케이스당 3 GB 를 넘는다.

---

## 5. 작업 폴더를 프로젝트 밖에 두는 이유

프로젝트가 OneDrive 안에 있고 경로에 한글·공백(`바탕 화면`)이 들어 있다.

- 솔버가 대용량 파일을 계속 쓰는 동안 OneDrive 가 동기화를 걸어 **파일 잠금
  충돌**이 난다
- 수 GB 짜리 `.rst` 가 클라우드 용량을 잠식한다
- 비ASCII 경로에서 일부 Ansys 구성요소가 경로 파싱에 실패한다

그래서 솔버는 항상 `C:\ANSYS_work`(ASCII, 공백 없음, 동기화 없음) 에서 돌린다.
`config.py` 가 이 규칙을 강제한다.

---

## 6. 이어서 할 작업

새 PC 에서 바로 이어가려면 `07_docs\실행방법.md` 의 순서를 따른다.
현재 미해결 과제는 `07_docs\report\FinRay_3핑거_파지_무게_상한.pdf` 6절에 있다.

가장 중요한 것 하나만 꼽으면 — **모델이 실측 1 kg 의 '놓치는 순간'을 재현하지
못한다.** 밑동을 변위로 고정하면 볼이 손가락을 벌릴 수 없어 형상 구속이
절대적이 되기 때문으로 보이며, 힘 구동(`--grip-force`)으로 검증 중이었다.

---

## 7. 새 PC 에서 먼저 확인할 것

```powershell
$PY = "C:\ANSYS_work\venv\Scripts\python.exe"
cd "<프로젝트경로>"

# 형상이 제대로 읽히는지 (라이선스 불필요, 30초)
& $PY 04_scripts\mesh\01_check_geometry.py

# 후처리가 도는지 (라이선스 불필요, 1분)
& $PY 04_scripts\post\31_plot_gravity.py
& $PY 04_scripts\post\50_make_report.py

# 솔버가 뜨는지 (라이선스 필요, 1분)
& $PY 04_scripts\journal\10_single_finger.py --order 1 --size 1.5 --dist 2.10
```

마지막 것이 `0.275 N` 근처를 내면 환경이 원래 PC 와 동일하게 재현된 것이다.
