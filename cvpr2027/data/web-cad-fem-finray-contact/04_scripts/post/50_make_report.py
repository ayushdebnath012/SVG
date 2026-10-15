"""
Fin Ray 3핑거 그리퍼 해석 보고서 PDF 생성 (개정판).

초판(2026-07-30 오전)은 인발 방향을 +Y 로 잡아 0.151 kg 이라는 결론을 냈으나,
접촉 구역이 볼 적도 아래라 손가락이 볼을 아래에서 받치는 배치임이 확인되어
방향을 -Y 로 바로잡았다. 이 판은 그 수정과 실측 대조를 반영한다.

한글 출력을 위해 맑은 고딕 TTF 를 등록한다. reportlab 내장 폰트에는 한글
글리프가 없어 등록하지 않으면 전부 검은 상자로 나온다.
유니코드 상/하첨자(³)도 없으므로 <super> 태그를 쓴다.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                               Spacer, Table, TableStyle)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (PROJECT, korean_font, korean_font_bold,  # noqa: E402
                    scratch)

IMG = PROJECT / "06_image"
OUT = PROJECT / "07_docs" / "report" / "FinRay_3핑거_파지_무게_상한.pdf"

_kf, _kfb = korean_font(), korean_font_bold()
if _kf is None:
    raise SystemExit(
        "한글 글리프가 있는 TTF 를 찾지 못했다. reportlab 내장 폰트에는 한글이 "
        "없어 전부 검은 상자로 나온다.\n"
        "  set FINRAY_KR_FONT=<경로>\\malgun.ttf  로 지정할 것")
pdfmetrics.registerFont(TTFont("KR", str(_kf)))
pdfmetrics.registerFont(TTFont("KRb", str(_kfb)))
registerFontFamily("KR", normal="KR", bold="KRb", italic="KR", boldItalic="KRb")

ACCENT = colors.HexColor("#1f4e79")
GREY = colors.HexColor("#555555")
LIGHT = colors.HexColor("#eef2f7")
BAD = colors.HexColor("#b03a2e")
OK = colors.HexColor("#1e7a46")

ss = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("t", parent=ss["Title"], fontName="KRb",
                            fontSize=20, leading=26, textColor=ACCENT),
    "sub": ParagraphStyle("s", fontName="KR", fontSize=10, leading=14.5,
                          textColor=GREY, alignment=TA_CENTER, spaceAfter=12),
    "h1": ParagraphStyle("h1", fontName="KRb", fontSize=13.5, leading=18,
                         textColor=ACCENT, spaceBefore=14, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="KRb", fontSize=11, leading=15,
                         textColor=colors.HexColor("#2c3e50"),
                         spaceBefore=9, spaceAfter=4),
    "body": ParagraphStyle("b", fontName="KR", fontSize=9.5, leading=14.5,
                           alignment=TA_LEFT, spaceAfter=6),
    "small": ParagraphStyle("sm", fontName="KR", fontSize=8.3, leading=12.3,
                            textColor=GREY, spaceAfter=5),
    "cap": ParagraphStyle("cap", fontName="KR", fontSize=8.1, leading=11.8,
                          textColor=GREY, alignment=TA_CENTER, spaceBefore=3,
                          spaceAfter=9),
    "cell": ParagraphStyle("c", fontName="KR", fontSize=8.5, leading=11.8),
    "cellb": ParagraphStyle("cb", fontName="KRb", fontSize=8.5, leading=11.8),
    "key": ParagraphStyle("k", fontName="KRb", fontSize=12, leading=17.5,
                          textColor=BAD, alignment=TA_CENTER),
}


def P(t, st="body"):
    return Paragraph(t, S[st])


def table(rows, widths, header=True, align=None, hilite=None):
    data = []
    for r_i, row in enumerate(rows):
        line = []
        for c in row:
            st = "cellb" if (r_i == 0 and header) or (hilite and r_i in hilite) \
                else "cell"
            line.append(c if isinstance(c, Paragraph) else Paragraph(str(c), S[st]))
        data.append(line)
    cmd = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d2dc")),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), 3.2),
           ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
           ("LEFTPADDING", (0, 0), (-1, -1), 5),
           ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if header:
        cmd += [("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
        for c_i in range(len(rows[0])):
            data[0][c_i] = Paragraph(
                f'<font color="white">{rows[0][c_i]}</font>', S["cellb"])
    for r_i in (hilite or []):
        cmd.append(("BACKGROUND", (0, r_i), (-1, r_i), LIGHT))
    if align:
        for col, a in align.items():
            cmd.append(("ALIGN", (col, 0), (col, -1), a))
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(cmd))
    return t


TRIM = scratch("trimmed")


def img(path, width, trim=True):
    """가로 폭에 맞춰 삽입. trim 이면 흰 여백을 잘라 그림을 키운다."""
    from PIL import Image as PILImage, ImageChops
    im = PILImage.open(path).convert("RGB")
    if trim:
        bbox = ImageChops.difference(
            im, PILImage.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            p_ = 12
            im = im.crop((max(0, bbox[0] - p_), max(0, bbox[1] - p_),
                          min(im.width, bbox[2] + p_),
                          min(im.height, bbox[3] + p_)))
        TRIM.mkdir(parents=True, exist_ok=True)
        path = TRIM / f"{Path(path).stem}_t.png"
        im.save(path)
    w, h = im.size
    return Image(str(path), width=width, height=width * h / w)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("KR", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 12 * mm,
                      "Fin Ray 15deg 3핑거 파지 해석 · Ansys MAPDL 2026 R1 · 개정판")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(doc.page))
    canvas.setStrokeColor(colors.HexColor("#d5dbe1"))
    canvas.line(20 * mm, 15.5 * mm, A4[0] - 20 * mm, 15.5 * mm)
    canvas.restoreState()


CW = A4[0] - 40 * mm
st = []

# ================================================================= 표지
st += [
    Spacer(1, 4 * mm),
    P("Fin Ray 3핑거 그리퍼<br/>파지 가능 무게 상한", "title"),
    P("15deg 형상 · NinjaFlex TPU 초탄성 · 대변형 접촉 · 마찰 · 중력 하중<br/>"
      "2026-07-29 ~ 07-30 &nbsp;|&nbsp; 개정판 (인발 방향 수정, 실측 대조 반영)",
      "sub"),
    img(IMG / "figures" / "3finger_clean_closed.png", CW * 0.80),
    P("조임 5.7 mm 상태. 색은 변위 크기 — 밑동이 붉은색(구동측), 볼에 닿는 부분이 "
      "파란색으로 거의 정지해 있다. 리브가 휘며 변위를 흡수하는 Fin Ray 고유 거동.",
      "cap"),
]

key = Table([[Paragraph(
    "실측 1 kg 에서 볼은 <b>0.32 mm 내려앉고 안정적으로 유지</b>된다.<br/>"
    "모델은 신뢰 구간(3.2 kg)까지 볼을 놓치지 않는다 — "
    "<b>마찰이 아니라 형상 구속이 지배</b>한다.", S["key"])]], colWidths=[CW])
key.setStyle(TableStyle([
    ("BOX", (0, 0), (-1, -1), 1.1, BAD),
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdf3f2")),
    ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
st += [key, Spacer(1, 4 * mm)]

st += [table([
    ["항목", "내용"],
    ["해석 도구", "Ansys Mechanical APDL 2026 R1 (PyMAPDL 0.73.2), gmsh 4.15.2"],
    ["재료", "NinjaFlex TPU — Mooney-Rivlin (c10=0.385, c01=1.47 MPa)"],
    ["해석 종류", "비선형 정적 · 대변형 · 접촉 · 마찰 · 비대칭 솔버 · 중력 하중"],
    ["모델 규모", "절점 26,469 / 솔리드 95,307 / 접촉 20,337 (한도의 90%)"],
    ["수행한 해석", "형상검증 3 · 단일핑거 메쉬수렴 4 · 3핑거 인발 2 · 중력 3"],
], [30 * mm, CW - 30 * mm])]

st.append(PageBreak())

# ============================================== 1. 결론
st += [P("1. 결론", "h1")]
st += [P(
    "실측(약 1 kg)을 기준으로 모델을 대조한 결과, <b>이 그리퍼는 마찰이 아니라 "
    "형상 구속(form closure)으로 볼을 잡는다.</b> 접촉이 볼 적도 아래에 몰려 있어 "
    "세 손가락이 볼을 아래에서 받치는 배치이기 때문이다.")]

st += [table([
    ["항목", "값", "비고"],
    ["실측 파지 상한", "약 1 kg", "그리퍼가 아예 놓치는 기준"],
    ["1 kg 에서 모델의 볼 처짐", "0.32 mm", "안정적으로 유지 — 실측과 부합"],
    ["모델이 놓치지 않고 버틴 최대", "3.2 kg 이상", "신뢰 구간 끝까지 놓치지 않음"],
    ["쿨롱 근사 &#956; x N (참고)", "0.52 kg", "이 형상에서는 쓸 수 없다 (3절)"],
], [CW - 56 * mm, 26 * mm, 30 * mm], align={1: "CENTER"}, hilite=[2])]

st += [P(
    "<b>모델은 실측 1 kg 을 설명하지만 '놓치는 순간'은 재현하지 못한다.</b> "
    "신뢰 구간 안에서는 하중을 아무리 키워도 볼이 빠지지 않는다. 실제 파괴 모드가 "
    "모델에 없다는 뜻이며, 원인 후보는 6절에 정리했다.")]

st += [P("초판에서 무엇이 바뀌었나", "h2")]
st += [table([
    ["항목", "초판", "개정판"],
    ["인발 방향", "+Y (팁 쪽)", "-Y (중력 방향)"],
    ["하중", "변위 구동", "중력을 실하중으로"],
    ["볼 횡방향", "구속", "자유"],
    ["지배 기구", "마찰", "형상 구속"],
    ["무게 상한", "0.151 kg", "1 kg 에서 안정, 3.2 kg 까지 안 놓침"],
], [26 * mm, (CW - 26 * mm) / 2, (CW - 26 * mm) / 2], hilite=[5])]

st += [P(
    "초판이 틀린 이유는 방향이다. 접촉 구역이 y = 6~31 mm 인데 볼 적도가 y = 30 "
    "이므로 손가락은 볼을 <b>아래에서</b> 받친다. +Y(팁 쪽)로 빼내는 것은 볼이 "
    "바구니에서 빠져나오는 방향이라 순수 마찰만 작용하지만, 실제 중력은 -Y 로 "
    "작용해 볼을 바구니 안으로 밀어넣는다.", "small")]

# ============================================== 2. 중력 하중 결과
st += [P("2. 중력 하중 해석", "h1")]
st += [P(
    "볼에 중력을 실하중으로 걸고 0 부터 키우며 평형을 찾지 못하는 지점을 "
    "찾는 방식이다. 변위로 밀어넣으면 저항이 한없이 오르기만 해 '놓치는 순간'이 "
    "나타나지 않는다. 하중 구동이라야 한계에서 발산하고, 그 발산이 곧 '놓쳤다'는 "
    "신호가 된다.")]

st += [table([
    ["볼 질량 [kg]", "무게 [N]", "볼 처짐 [mm]", "횡이동 [mm]", "접촉압력 [MPa]"],
    ["0.2", "1.96", "0.060", "0.018", "0.34"],
    ["0.5", "4.90", "0.133", "0.050", "0.36"],
    ["1.0", "9.81", "0.315", "0.118", "0.75"],
    ["2.0", "19.61", "0.664", "0.183", "1.92"],
    ["3.2", "31.38", "0.949", "0.226", "3.12"],
    ["3.3", "32.36", "0.969", "0.227", "3.74  (신뢰 구간 끝)"],
], [CW / 5] * 5, align={i: "CENTER" for i in range(5)}, hilite=[3])]

st += [P(
    "조임 5.7 mm, &#956;=0.6, 하중을 손가락 사이 틈 쪽으로 10도 기울인 조건. "
    "접촉압력이 재료 전단계수(3.71 MPa)를 넘는 3.3 kg 부터는 결과를 믿지 않는다.",
    "small")]

st += [img(IMG / "plot" / "3finger_gravity.png", CW, trim=False)]
st += [P("(1) 조임량이 파지력을 지배한다 (2) 중력에 따른 볼 처짐, 실측 1 kg 표시 "
         "(3) 인발 방향이 30배를 가른다 (4) 접촉압력으로 본 신뢰 구간", "cap")]

st += [P("볼은 옆으로 빠지지 않는다", "h2")]
st += [P(
    "볼의 횡방향 구속을 풀었는데도 완전 대칭 조건에서는 횡이동이 "
    "<b>전 구간 정확히 0.000 mm</b> 였다. 120도 대칭이라 횡방향 합력이 수학적으로 "
    "0 이기 때문이다. 하중을 10도 기울여 대칭을 깬 뒤에야 횡이동이 생겼지만, "
    "0.25 mm 에서 포화하고 이탈로 이어지지 않았다.")]

# ============================================== 3. 쿨롱 공식
st += [P("3. 쿨롱 공식은 이 형상에 쓸 수 없다", "h1")]
st += [P(
    "접촉 구역이 y = 6.07 ~ 31.18 mm 이다. 볼 적도가 y = 30 이므로 접촉이 거의 전부 "
    "적도 아래에 있고, 접촉면 법선이 반경방향이 아니라 큰 축방향 성분을 갖는다. "
    "반경방향 파지력 8.49 N 이 그대로 마찰에 동원되지 않는다.")]

st += [table([
    ["인발 방향", "해당 자세", "최대 저항", "지배 기구", "수치 건전성"],
    ["-Y (밑동 쪽)", "실제 중력 방향", "3.2 kg 이상", "형상 구속", "3.3 kg 까지 정상"],
    ["+Y (팁 쪽)", "볼을 빼내는 방향", "0.151 kg", "마찰", "전 구간 정상"],
], [22 * mm, 34 * mm, 24 * mm, 24 * mm, CW - 104 * mm], hilite=[1])]

st += [P(
    "같은 모델에서 방향만 바꾸면 답이 20배 이상 달라진다. &#956; x N 공식은 "
    "접촉 법선이 모두 반경방향일 때만 성립하는데, 이 배치는 그렇지 않다.", "small")]

# ============================================== 4. 조임량
st += [P("4. 조임량이 파지력을 지배한다", "h1")]
st += [table([
    ["조임 [mm]", "손가락당 [N]", "총 파지력 [N]", "손가락 간 편차", "최대 관통 [mm]"],
    ["3.0", "0.662", "1.986", "0.00%", "0.0122"],
    ["4.0", "1.040", "3.120", "0.00%", "0.0105"],
    ["5.0", "1.722", "5.167", "0.00%", "0.0086"],
    ["5.7", "2.830", "8.490", "0.00%", "0.0142"],
], [CW / 5] * 5, align={i: "CENTER" for i in range(5)}, hilite=[4])]

st += [P(
    "3.0 mm 와 5.7 mm 사이에 파지력이 <b>4.3배</b> 차이난다. 본 해석은 5.7 mm 로 "
    "조였는데, 이는 물리적 근거가 아니라 <b>수치 파탄 직전까지 최대로 조인 값</b>이다. "
    "6.9 mm 에서는 메쉬 3종(2.5 mm 1차, 1.5 mm 1차, 2.5 mm 2차)이 모두 파탄한다 — "
    "힘이 급등하면서 접촉면적은 오히려 줄어드는 불가능한 조합이 나타난다.")]

st += [P(
    "<b>실제 실험의 조임량을 알면 결과가 크게 달라진다.</b> 현재 미확인 항목 중 "
    "가장 영향이 크다.", "small")]

st += [P("세 손가락 대칭성 검증", "h2")]
st += [P(
    "세 손가락 반경력이 소수점 3자리까지 동일하다(편차 0.00%). 배치·경계조건·접촉 "
    "정의가 모두 옳다는 뜻이다. 관통량도 전 구간 0.015 mm 이하로 접촉 품질이 좋다.")]

st += [P(
    "측정 주의 — FSUM 은 절점좌표계가 아니라 <b>전역</b> 좌표계로 합산한다. "
    "손가락이 120도씩 돌아가 있어 전역 FX 만 읽으면 대칭인데도 값이 제각각 나온다. "
    "그리퍼 축이 Y 이므로 반경 성분 = &#8730;(FX<super>2</super>+FZ<super>2</super>) "
    "로 구해야 한다. 구속 절점의 반력은 FSUM 으로 잡히지 않아 전 구간 0 이 나온다 — "
    "*GET,,NODE,n,RF,FY 를 써야 한다.", "small")]

# ============================================== 5. 메쉬 수렴성
st += [P("5. 메쉬 수렴성 — 기존 보고서 값의 문제", "h1")]
st += [table([
    ["밀어넣은 거리 [mm]", "1차 2.5 mm", "1차 1.5 mm", "1차 1.0 mm", "기존 PDF 기록"],
    ["2.10", "0.457", "0.275", "0.303", "0.43"],
    ["3.30", "0.962", "0.583", "0.651", "0.90"],
    ["4.50", "1.616", "0.977", "1.080", "1.44"],
], [CW / 5] * 5, align={i: "CENTER" for i in range(5)})]

st += [P(
    "2.5 mm 에서 1.5 mm 로 줄이면 접촉힘이 약 40% 떨어지고, 1.5 mm 에서 1.0 mm 로는 "
    "10% 만 변한다. <b>2.5 mm 메쉬는 수렴하지 않았다.</b> 원인은 접촉 패치 미해상이다 "
    "— 2.5 mm 에서는 접촉 패치가 요소 5~7개, 1.0 mm 에서는 24~61개로 표현된다. "
    "구조 강성은 이미 수렴해 있음(2.5 → 1.5 mm 에서 4.4% 변화)을 별도 확인했으므로 "
    "이는 구조가 아니라 접촉 쪽 문제다.")]

st += [P(
    "기존 보고서(2026-07-27~28)가 접촉힘 신뢰도를 '높음'으로 분류한 근거는 '면적 "
    "과소평가와 압력 과대평가가 상쇄된다' 였는데, 상쇄 비율이 메쉬마다 달라 성립하지 "
    "않는다. 또한 기존 4.4절 들어올리기 해석에는 볼 무게가 하중으로 걸려 있지 않다 "
    "— '응력이 소수점 15자리까지 불변' 이라는 기록 자체가 근거다.", "small")]

# ============================================== 6. 미해결
st += [P("6. 모델이 '놓치는 순간'을 재현하지 못하는 이유", "h1")]
st += [P(
    "실측 1 kg 은 모델에서 안정적으로 유지되지만, 하중을 3.2 kg 까지 키워도 볼이 "
    "빠지지 않는다. 실제 파괴 모드가 모델에 없다는 뜻이다. 후보를 영향이 큰 순서로 "
    "정리하면 다음과 같다.")]

st += [table([
    ["#", "후보", "근거 / 확인 방법"],
    ["1", "실제 조임량이 5.7 mm 보다 훨씬 작았다",
     "조임 3.0 mm 면 파지력이 4.3배 작다. 실험 조임량 확인 필요 — "
     "가장 영향이 크고 가장 쉽게 확인된다"],
    ["2", "볼이 실제로는 적도 위쪽에서 물렸다",
     "적도 위에서 감싸면 형상 구속이 사라지고 마찰이 지배해 상한이 크게 낮아진다. "
     "본 해석의 접촉 위치는 CAD 상대 배치를 그대로 쓴 것이다"],
    ["3", "모델이 지나치게 대칭적이다",
     "완전 대칭에서는 횡이동이 정확히 0. 10도 기울여도 0.25 mm 에서 포화했다. "
     "실제 공차·정렬 오차는 더 큰 비대칭을 만든다"],
    ["4", "손가락 지지부 강성",
     "본 해석은 밑동을 완전 강체로 구속했다. 실제 마운트가 휘면 파지력이 준다"],
    ["5", "자기접촉 미반영",
     "리브끼리 닿는 것을 넣지 않았다. 6.9 mm 파탄의 유력한 원인이기도 하다"],
], [8 * mm, 52 * mm, CW - 60 * mm], hilite=[1])]

# ============================================== 7. 가정과 한계
st += [P("7. 가정과 한계", "h1")]
st += [table([
    ["항목", "내용", "영향"],
    ["마찰계수", "&#956;=0.6 은 실측 없는 가정값",
     "형상 구속이 지배하므로 초판만큼 결정적이지는 않다. 다만 접촉 개시 거동에 영향"],
    ["조임량", "5.7 mm — 수치 파탄 직전까지 최대로 조인 값",
     "<b>미확인 항목 중 영향 최대.</b> 3.0 mm 면 파지력 4.3배 감소"],
    ["볼 위치", "CAD 상대 배치를 그대로 사용 (접촉 y=6~31 mm)",
     "적도 위/아래에 따라 지배 기구가 바뀐다"],
    ["메쉬", "1.5 mm — Student 요소 한도(128,000)로 3핑거는 이것이 최선",
     "1.0 mm 대비 약 &#177;10%"],
    ["신뢰 구간", "접촉압력이 전단계수(3.71 MPa)를 넘는 3.3 kg 까지",
     "그 이상은 수치 결과를 쓰지 않는다"],
    ["볼 형상", "접촉은 R=40 해석적 구면, 질량은 잘린 실제 체적 "
     "245,042 mm<super>3</super>",
     "완전구로 계산하면 무게 8.6% 과대"],
    ["동적 효과", "정적 해석이라 가속·충격·진동 미반영",
     "빠르게 들어올리면 관성력만큼 더 필요"],
], [22 * mm, 62 * mm, CW - 84 * mm], hilite=[2])]

# ============================================== 8. 검증
st += [P("8. 검증 근거", "h1")]
st += [table([
    ["검증 항목", "결과", "판정"],
    ["STEP 형상 대조 (치수·체적·면 개수)",
     "15deg 15,363.7 mm<super>3</super> vs 기록 15,364", "일치"],
    ["요소 부피 합 vs CAD 체적", "15,363.7 / 15,363.7", "오차 0.00%"],
    ["gmsh tet10 → SOLID187 절점 순서", "중간절점 좌표로 직접 확인", "매핑 일치"],
    ["단일핑거 기존 PDF 재현 (2.5 mm 1차)", "3.3 mm 까지 오차 7% 이내", "재현 성공"],
    ["3핑거 대칭성", "손가락 간 편차 0.00%", "통과"],
    ["접촉 관통량", "전 구간 0.015 mm 이하", "양호"],
    ["하중 전달 확인", "볼 처짐 최대 1.26 mm (0 이면 하중 미전달)", "정상"],
    ["실측 대조", "1 kg 에서 처짐 0.32 mm, 안정 유지", "실측과 부합"],
], [64 * mm, 54 * mm, CW - 118 * mm], hilite=[8])]

st += [P(
    "'하중 전달 확인'은 이번에 새로 넣은 검사다. 강체 타겟의 프리미티브 절점에는 "
    "하중을 걸 수 없어(파일럿 절점이 필요하다) 처음에는 8 kg 까지 처짐이 정확히 "
    "0 으로 나왔다 — 그럴듯한 표가 나오지만 전부 무의미한 값이었다. 기존 보고서의 "
    "'응력이 15자리까지 불변'과 정확히 같은 증상이다.", "small")]

# ============================================== 9. 다음
st += [P("9. 다음에 할 것", "h1")]
st += [table([
    ["우선순위", "항목", "이유"],
    ["1", "실험 조임량 확인", "미확인 항목 중 영향 최대. 그 값으로 다시 돌리면 "
     "실측과 직접 비교 가능"],
    ["2", "실제 볼 파지 위치 확인", "적도 위/아래가 지배 기구를 바꾼다"],
    ["3", "마찰계수 실측", "접촉 개시 거동의 유일한 가정값"],
    ["4", "손가락 지지부 강성 반영", "밑동 완전 구속은 낙관적 가정"],
    ["5", "자기접촉 추가", "6.9 mm 이상 조임 가능 여부 판정"],
], [16 * mm, 40 * mm, CW - 56 * mm], hilite=[1])]

st += [P("부록 — 재발하기 쉬운 함정", "h1")]
st += [table([
    ["증상", "원인 / 해결"],
    ["PREP7 은 되고 SOLVE 만 실패", "launch_mapdl() 에 license_type 을 주면 안 된다"],
    ["절점만 읽히고 요소가 0개",
     "EBLOCK 은 ET 가 먼저 정의돼 있어야 한다. 헤더 3번째 필드는 비울 것"],
    ["접촉압력이 von Mises 와 같은 값",
     "*GET,ETAB 대신 ETABLE 후 ESORT 를 거쳐 SORT 에서 읽을 것"],
    ["구속 절점 반력이 전 구간 0", "FSUM 이 아니라 *GET,,NODE,n,RF,FY 를 쓸 것"],
    ["하중을 걸었는데 아무것도 안 변함",
     "강체 타겟 프리미티브 절점은 하중을 못 받는다. TSHAP,PILO 파일럿 절점 필요"],
    ["MASS21 을 붙이니 타겟 오류", "타겟 절점은 다른 요소와 공유 불가. 점하중으로 대체"],
    ["서브스텝 하나를 몇 시간 못 넘김",
     "마찰 접촉은 NROPT,UNSYM 필수. MAPDL 이 시작 시 경고를 낸다"],
    ["결과 파일이 덮어써지고 하중스텝이 1로 리셋",
     "POST1 을 들렀다 /SOLU 로 돌아오면 해석이 새로 시작된다"],
    ["변위가 1e307 쓰레기값",
     "ansys-mapdl-reader 는 이 버전 .rst 를 못 읽는다. mapdl.post_processing 사용"],
    ["요소 한도 초과", "접촉 요소를 외피 전체가 아니라 대상 주변 띠에만 생성"],
], [52 * mm, CW - 52 * mm])]

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
    topMargin=16 * mm, bottomMargin=20 * mm,
    title="Fin Ray 3핑거 그리퍼 파지 가능 무게 상한 (개정판)",
    author="ANSYS MAPDL 2026 R1 해석")
doc.build(st, onFirstPage=footer, onLaterPages=footer)
print(f"저장: {OUT}")
print(f"      {OUT.stat().st_size/1024:.0f} KB")
