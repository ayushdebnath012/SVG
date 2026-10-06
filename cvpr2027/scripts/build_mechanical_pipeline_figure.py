"""Method overview for the mechanical CAD paper, drawn from one real held-out edit.

Every number and drawing comes from saved artifacts: the mounting-angle test pair, the final 3B
adapter's patch, the executed solid's CadQuery SVG projections, its FEM solution and the 3B
held-out scores. Nothing is re-run.
"""
from pathlib import Path
import json, hashlib, re, collections
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT/'paper/network/figures'
OUT = ROOT/'runs/paper-mechanical-pipeline-20261003'
OUT.mkdir(parents=True, exist_ok=True)
RES = ROOT/'runs/multisource-cad-colab-20261002/results-final'
CASE = RES/'fem-examples/mounting_angle_box_x_f130'
DATA = ROOT/'data/benchcad-online-edit-v1'
PAPER = ROOT/'paper/network'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'mathtext.fontset': 'dejavusans',
                     'svg.fonttype': 'none', 'pdf.fonttype': 42})

INK = '#1b2a3a'; GREY = '#7d8894'
PURPLE, PURPLE_BG = '#6a3fb5', '#f4effc'
BLUE, BLUE_BG = '#2f6aa8', '#eef4fb'
GREEN, GREEN_BG = '#23804f', '#ecf7f0'
AMBER, AMBER_BG = '#b5700c', '#fff5e4'
RED, RED_BG = '#b8322a', '#fdeeed'
SPLIT = {'train': '#8fb3dc', 'validation': '#f0c36a', 'test': '#79c29a'}

files = []
def read(path):
    files.append(path)
    return path.read_text()
def jsonl(path):
    return [json.loads(l) for l in read(path).splitlines() if l.strip()]

# ---------------------------------------------------------------- data
source = read(CASE/'source.py').rstrip('\n')
patch = json.loads(read(CASE/'patch.json'))
record = next(r for r in jsonl(RES/'test-retained.jsonl')
              if r['code'].strip() == source.strip() and json.loads(r['target']) == patch)
pred = next(p for p in jsonl(RES/'trained-predictions.jsonl') if p['id'] == record['id'])
geo_rows = jsonl(RES/'trained-predictions-geometry.jsonl')
geo = next(g for g in geo_rows if g['id'] == record['id'])
assert json.loads(pred['prediction']) == patch and pred['exact_patch'] and geo['match_strict']
status = collections.Counter(g['status'] for g in geo_rows)
funnel = [('held-out tasks', len(geo_rows)),
          ('applicable patch', sum(p['applicable'] for p in jsonl(RES/'trained-predictions.jsonl'))),
          ('executed + scored', status['scored']),
          (r'IoU $\geq$ 0.95', sum(bool(g['match_95']) for g in geo_rows)),
          (r'IoU $\geq$ 0.99999', sum(bool(g['match_strict']) for g in geo_rows))]
ver = json.loads(read(CASE/'verification/verification.json'))
fp, ft = ver['fem']['prediction']['history'], ver['fem']['target']['history']
fem = dict(force=max(fp[-1]['relative_force_balance_error'], fp[-1]['relative_moment_balance_error']),
           energy=fp[-1]['relative_energy_error'], volume=fp[-1]['relative_mesh_volume_error'],
           refine=abs(fp[-1]['compliance_N_mm']/fp[-2]['compliance_N_mm']-1),
           target=ver['relative_target_compliance_error'], nodes=fp[-1]['nodes'], tets=fp[-1]['tetrahedra'])
contract = ver['contract']
assert ver['fem_numerical_checks_pass'] and ver['edit_reference_check_pass']
assert fem['volume'] <= contract['mesh_volume_tolerance'] and fem['refine'] <= contract['compliance_mesh_tolerance']
assert fem['target'] <= contract['response_agreement_tolerance']

# Strict counts for the two 1.5B runs come from their generated result macros.
def macro_row(path, label):
    row = re.search(re.escape(label)+r' & (\d+) & (\d+) & (\d+) & (\d+)', read(path)).groups()
    return [int(v) for v in row]
mlx = macro_row(PAPER/'mechanical-results.tex', 'Fresh online-pair QLoRA')
cuda = macro_row(PAPER/'cuda-results.tex', 'CUDA final LoRA')
ref_valid = int(re.search(r'onlineReferenceValid\}\{(\d+)', read(PAPER/'mechanical-results.tex')).group(1))
train_3b = len(jsonl(RES/'train-retained.jsonl'))
runs = [('1.5B', 'MLX 4-bit, M5', '492', f'{mlx[3]}/{ref_valid}'),
        ('1.5B', 'BF16, H100', '492', f'{cuda[3]}/{ref_valid}'),
        ('3B', 'NF4, T4', f'{train_3b:,}', f'{funnel[-1][1]}/{funnel[0][1]}')]

split_rows = {s: jsonl(DATA/f'{s}.jsonl') for s in ('train', 'validation', 'test')}
family_sizes = {s: collections.Counter(r['family'] for r in rows) for s, rows in split_rows.items()}

def svg_paths(path):
    """Visible-edge polylines of a CadQuery SVG export, in model units (y up)."""
    text = read(path).split('<!-- solid lines -->', 1)[1]
    return [np.array([[float(v) for v in p.split(',')] for p in re.findall(r'(-?[\d.]+(?:e-?\d+)?,-?[\d.]+(?:e-?\d+)?)', d)])
            for d in re.findall(r'<path d="([^"]+)"', text)]

# ---------------------------------------------------------------- canvas
# Units are 1/100 inch, so a 1 pt font is 1.39 units tall; layout widths below were sized to the text.
W, H = 720, 418
fig = plt.figure(figsize=(W/100, H/100))
A = fig.add_axes([0, 0, 1, 1]); A.set_xlim(0, W); A.set_ylim(0, H); A.axis('off')
def inset(x, y, w, h, **kw):
    ax = fig.add_axes([x/W, y/H, w/W, h/H], **kw); ax.set_axis_off(); return ax
def T(x, y, s, size=4.6, color=INK, **kw):
    kw.setdefault('va', 'center'); return A.text(x, y, s, fontsize=size, color=color, **kw)
def panel(x, y, w, h, tag, title, edge, bg):
    A.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=7', fc=bg, ec=edge, lw=1.0))
    A.add_patch(Circle((x+10, y+h-10), 5.2, fc=edge, ec='none'))
    T(x+10, y+h-10, tag, 5.6, 'white', ha='center', fontweight='bold')
    T(x+18, y+h-10, title, 6.4, edge, fontweight='bold')
def card(x, y, w, h, fc='white', ec='#c9d6e4', lw=0.6, r=3):
    A.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec, lw=lw))
def arrow(p0, p1, color=INK, lw=1.1, ls='-', head=7):
    A.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=head, lw=lw, color=color, linestyle=ls,
                                shrinkA=0, shrinkB=0))
def mono(x, y, lines, size=4.5, lh=7.4, color=INK, colors=None, gutter=None):
    for i, line in enumerate(lines):
        if gutter is not None:
            T(x, y-i*lh, str(gutter+i), size, GREY, family='DejaVu Sans Mono', ha='right')
        T(x+(4 if gutter is not None else 0), y-i*lh, line, size, (colors or {}).get(i, color),
          family='DejaVu Sans Mono', ha='left')
def lines(x, y, rows, size=4.4, lh=7.4, **kw):
    for i, row in enumerate(rows):
        T(x, y-i*lh, row, size, **kw)
def tick(x, y, ok=True, size=5.4):
    T(x, y, '✓' if ok else '✗', size, GREEN if ok else RED, ha='left', fontweight='bold')
def stamp(x, y, s, color, size=6.2, rot=6):
    T(x, y, s, size, color, ha='center', fontweight='bold', rotation=rot,
      bbox=dict(boxstyle='round,pad=0.28,rounding_size=0.25', fc='white', ec=color, lw=1.1, alpha=.92))

TOP, TOP_H = 188, 226     # pipeline row: y 188..414
BOT, BOT_H = 46, 128      # data / physics / outcome row: y 46..174
P = {1: (4, 140), 2: (152, 152), 3: (312, 132), 4: (452, 122), 5: (582, 134)}

# ---------------------------------------------------------------- 1 source + request
x, w = P[1]; panel(x, TOP, w, TOP_H, '1', 'Source CAD + request', BLUE, BLUE_BG)
T(x+8, 391, 'published instruction, held-out family', 4.4, GREY, ha='left')
card(x+6, 364, w-12, 21, ec=BLUE)
words = '“'+record['instruction']+'”'
split_at = words.rfind(' ', 0, len(words)//2+6)
lines(x+w/2, 378.5, [words[:split_at], words[split_at+1:]], 4.9, 7.2, ha='center', style='italic')
code_lines = source.splitlines()
T(x+8, 355, f'program C ({len(code_lines)} lines; no line hint)', 4.4, GREY, ha='left')
card(x+6, 270, w-12, 80)
mono(x+16, 343, code_lines[:9], size=4.6, lh=7.6, gutter=0)
T(x+20, 274.5, '⋮', 5.2, GREY, ha='left')
src_iso = svg_paths(ROOT/'runs/paper-mechanical-diagrams-20261003/mounting_angle_box_x_f130-source-isometric.svg')
ax = inset(x+26, 212, 88, 52); ax.add_collection(LineCollection(src_iso, lw=.45, color=BLUE)); ax.autoscale(); ax.set_aspect('equal')
lines(x+w/2, 205, ['source solid, reference only:', 'the editor reads code + text only'], 4.3, 6.6, color=GREY, ha='center')

# ---------------------------------------------------------------- 2 patch editor
x, w = P[2]; panel(x, TOP, w, TOP_H, '2', 'Patch editor (LoRA)', PURPLE, PURPLE_BG)
T(x+8, 391, 'Qwen2.5-Coder-Instruct (fresh base)', 4.6, INK, ha='left')
T(x+8, 381, 'predicted patch p (3B, this case)', 4.4, GREY, ha='left')
T(x+w-8, 381, '= gold', 4.4, PURPLE, ha='right', style='italic', fontweight='bold')
card(x+6, 348, w-12, 28, fc='#2a2238', ec=PURPLE, lw=.8)
mono(x+11, 369, ['{"edits":[{"start":3,"delete":1,', ' "insert":[',
                 '  "    .box(42.9, 33.0, 83.0)"]}]}'], size=4.5, lh=7.4, color='#f1e9ff')
n_blocks, bx0, bw, gap, by, bh = 10, x+27, 7.2, 3.0, 302, 32
for i in range(n_blocks):
    lora = i >= n_blocks-3
    bxi = bx0+i*(bw+gap)
    A.add_patch(FancyBboxPatch((bxi, by), bw, bh, boxstyle='round,pad=0,rounding_size=1.6',
                               fc=PURPLE if lora else '#d9d4e3', ec='none'))
    if lora:
        for yy in (by+bh+1.5, by-5):
            A.add_patch(Rectangle((bxi+1.4, yy), bw-2.8, 3.5, fc='#b79be6', ec='none'))
T(bx0-4, by+bh/2, 'C, u', 5.4, INK, ha='right', fontweight='bold')
arrow((bx0+(n_blocks-1.5)*(bw+gap), by+bh+6), (bx0+(n_blocks-1.5)*(bw+gap), 347), PURPLE, head=6)
T(bx0+3.5*(bw+gap), by-11, 'frozen backbone', 4.5, GREY, ha='center')
T(bx0+8.5*(bw+gap)-gap/2, by-11, 'LoRA', 4.8, PURPLE, ha='center', fontweight='bold')
lines(x+w/2, 278, ['adapters on 7 attention/MLP projections', 'in the last 8 (1.5B) or 12 (3B) blocks;',
                   'loss on patch tokens only'], 4.3, 6.8, ha='center')
cols = [x+9, x+29, x+89, x+117]
for c, head in zip(cols, ['size', 'precision, GPU', 'train', 'strict']):
    T(c, 248, head, 4.4, GREY, ha='left', fontweight='bold')
A.plot([x+8, x+w-8], [243.5, 243.5], color=GREY, lw=.4)
for i, row in enumerate(runs):
    for c, s in zip(cols, row):
        T(c, 236-i*9, s, 4.6, PURPLE if (i == 2 and c == cols[-1]) else INK, ha='left',
          fontweight='bold' if c == cols[-1] else 'normal')
T(x+w/2, 199, 'strict: held-out volume IoU ≥ 0.99999', 4.3, GREY, ha='center')

# ---------------------------------------------------------------- 3 validate + execute
x, w = P[3]; panel(x, TOP, w, TOP_H, '3', 'Validate + execute', BLUE, BLUE_BG)
for i, s in enumerate(['schema: start, delete, insert', 'ordered, disjoint, in range', 'original-line indices',
                       'patched program parses']):
    tick(x+9, 391-i*9); T(x+18, 391-i*9, s, 4.6, ha='left')
T(x+9, 352, r'executed program $\hat C=\mathcal{E}(C,p)$', 4.7, ha='left')
card(x+6, 324, w-12, 22)
A.add_patch(Rectangle((x+7, 335.5), w-14, 9, fc=RED_BG, ec='none'))
A.add_patch(Rectangle((x+7, 325.5), w-14, 9, fc=GREEN_BG, ec='none'))
mono(x+11, 340, ['3 − .box(33.0, 33.0, 83.0)', '3 + .box(42.9, 33.0, 83.0)'], size=4.6, lh=10,
     colors={0: RED, 1: GREEN})
card(x+6, 285, w-12, 31)
T(x+w/2, 307.5, 'restricted CadQuery run', 4.9, ha='center', fontweight='bold')
lines(x+w/2, 297, ['allow-listed imports, no file I/O,', '45 s per case'], 4.4, 7, ha='center')
arrow((x+w/2, 284), (x+w/2, 277), BLUE, head=6)
card(x+10, 258, w-20, 18, fc=BLUE, ec=BLUE)
T(x+w/2, 267, f"solid  V = {geo['predicted_volume']:,.1f} mm³", 4.9, 'white', ha='center', fontweight='bold')
card(x+6, 196, w-12, 52, fc=RED_BG, ec=RED, lw=.6)
T(x+11, 239, '✗  otherwise: unverified', 5.0, RED, ha='left', fontweight='bold')
lines(x+11, 227, ['no retry, no repair. Held-out 3B:', f"{status['invalid_patch']} invalid patches, "
                  f"{status['execution_error']} execution", f"errors, {status['timeout']} timeout"], 4.4, 7.4, ha='left')

# ---------------------------------------------------------------- 4 linked views
x, w = P[4]; panel(x, TOP, w, TOP_H, '4', 'Linked SVG views', BLUE, BLUE_BG)
T(x+w/2, 391, 'views of the predicted solid', 4.6, ha='center')
for i, view in enumerate(['front', 'top', 'right', 'isometric']):
    cx, cy = x+6+(i % 2)*57, 300-(i//2)*84
    card(cx, cy, 53, 78)
    ax = inset(cx+4, cy+5, 45, 60)
    ax.add_collection(LineCollection(svg_paths(CASE/f'verification/{view}.svg'), lw=.4, color=INK))
    ax.autoscale(); ax.set_aspect('equal')
    T(cx+26.5, cy+71, view, 4.8, BLUE, ha='center', fontweight='bold')
lines(x+w/2, 205, ['one solid drives all four views;', 'each view is autoscaled'], 4.3, 6.6, color=GREY, ha='center')

# ---------------------------------------------------------------- 5 scoring
x, w = P[5]; panel(x, TOP, w, TOP_H, '5', 'Independent scoring', GREEN, GREEN_BG)
T(x+w/2, 391, 'vs. a hash-pinned reference solid', 4.6, ha='center')
T(x+w/2, 372, r'IoU$=\dfrac{V(\hat B\cap B^\star)}{V(\hat B)+V(B^\star)-V(\hat B\cap B^\star)}$', 5.3, ha='center')
T(x+8, 353, f"this case: IoU = {ver['volume_iou']:.9f}", 4.7, ha='left')
assert f"{geo['predicted_volume']:,.3f}" == f"{geo['reference_volume']:,.3f}"
T(x+8, 344, r'$\hat V=V^\star=$'+f" {geo['reference_volume']:,.3f} mm³", 4.5, ha='left')
T(x+8, 335, 'program AST = released target', 4.5, ha='left'); tick(x+w-15, 335)
stamp(x+w/2, 318, 'STRICT MATCH', GREEN)
T(x+8, 299, 'final 3B adapter, held-out set', 4.5, GREY, ha='left', fontweight='bold')
fx, fw = x+67, 44
for i, (label, n) in enumerate(funnel):
    yy = 286-i*14.5; last = i == len(funnel)-1
    T(fx-3, yy, label, 4.5, ha='right')
    bar = fw*n/funnel[0][1]
    A.add_patch(Rectangle((fx, yy-4.5), bar, 9, fc=GREEN if last else '#a9d5bb', ec='none'))
    T(fx+bar+2, yy, f'{n}', 4.7, ha='left', fontweight='bold' if last else 'normal')
lines(x+w/2, 205, [f"{status['reference_error']} reference errors and {status['timeout']} timeout", f"stay in n = {funnel[0][1]}"], 4.3, 6.6,
      color=GREY, ha='center')

# ---------------------------------------------------------------- D data and split
x, w = 4, 300; panel(x, BOT, w, BOT_H, 'D', 'Training data + leakage-safe split', BLUE, BLUE_BG)
steps = [('748', ['BenchCAD', 'edit pairs']), ('710', ['mechanical', '(−38 pipe/circuit)']),
         ('533/50/127', ['family-component', 'split']), ('492/44/126', ['fit 3,072-token', 'context'])]
sx, sw = [12, 72, 148, 228], [50, 66, 70, 70]
for i, ((num, lab), cx, cw) in enumerate(zip(steps, sx, sw)):
    card(cx, 119, cw, 30, ec=BLUE)
    T(cx+cw/2, 141.5, num, 5.6, BLUE, ha='center', fontweight='bold')
    lines(cx+cw/2, 131, lab, 4.3, 6.4, ha='center')
    if i: arrow((sx[i-1]+sw[i-1]+1, 134), (cx-1, 134), BLUE, head=6)
T(x+8, 109, f"{sum(len(v) for v in family_sizes.values())} part families, each kept whole (width ∝ pairs):", 4.6, ha='left')
total = sum(sum(c.values()) for c in family_sizes.values()); cx = x+8; span = w-16
for s in ('train', 'validation', 'test'):
    for fam, n in sorted(family_sizes[s].items(), key=lambda kv: -kv[1]):
        ww = span*n/total
        A.add_patch(Rectangle((cx, 89), ww, 13, fc=SPLIT[s], ec='white', lw=.25)); cx += ww
lx = x+8
for s, lab in [('train', f"train {len(family_sizes['train'])} families"), ('validation', f"val {len(family_sizes['validation'])}"),
               ('test', f"test {len(family_sizes['test'])}, incl. mounting angle")]:
    A.add_patch(Rectangle((lx, 77), 7, 6, fc=SPLIT[s], ec='none')); T(lx+9, 80, lab, 4.5, ha='left'); lx += 9+len(lab)*2.6+10
lines(x+8, 67, ['families sharing a numeric-masked AST template are merged before hash-ranked',
                'assignment; each target is a comment-stripped line diff replayed to its target'], 4.4, 6.8, ha='left')
T(x+8, 52, f'3B run adds CAD-Editor sketch–extrude pairs: {train_3b:,} training pairs in total', 4.4, GREY, ha='left')

# ---------------------------------------------------------------- 6 conditional FEM audit
x, w = 312, 262; panel(x, BOT, w, BOT_H, '6', 'Conditional FEM audit', AMBER, AMBER_BG)
T(x+w-8, BOT+BOT_H-10, 'explicit contract only', 4.5, AMBER, ha='right', style='italic')
card(x+6, 54, 80, 98, ec=AMBER)
T(x+46, 145, 'test contract', 4.9, AMBER, ha='center', fontweight='bold')
m, band = contract['material'], contract['band_fraction']*100
lines(x+11, 134, ['units: mm, N, MPa', f"E {m['E_MPa']/1000:.0f} GPa, ν {m['poisson_ratio']}", f'fixed: bottom {band:.0f} %',
                  f"{contract['total_force_N']:.0f} N load, top {band:.0f} %", 'hashed before solve'], 4.3, 10, ha='left')
lines(x+46, 76, ['hypothetical', 'material; no', 'safety rating'], 4.2, 6.2, color=GREY, ha='center', style='italic')
arrow((x+87, 103), (x+92, 103), AMBER, head=5)
sol_path = CASE/'verification/prediction-mesh-1/solution.npz'; files.append(sol_path); sol = np.load(sol_path)
t = sol['tetrahedra']; faces = np.concatenate([t[:, [0, 1, 2]], t[:, [0, 1, 3]], t[:, [0, 2, 3]], t[:, [1, 2, 3]]])
owners = np.tile(np.arange(len(t)), 4)
uniq, ix, cnt = np.unique(np.sort(faces, axis=1), axis=0, return_index=True, return_counts=True)
surf, owner = uniq[cnt == 1], owners[ix[cnt == 1]]
xyz = sol['points']; vm = sol['vm_MPa']; cap = np.percentile(vm, 95)
ax = fig.add_axes([(x+86)/W, 60/H, 74/W, 82/H], projection='3d'); ax.set_axis_off(); ax.set_facecolor((1, 1, 1, 0))
pc = Poly3DCollection(xyz[surf], facecolors=plt.cm.turbo(Normalize(0, cap)(vm[owner])), edgecolors='none')
pc.set_rasterized(True); ax.add_collection3d(pc)
axis = np.array(contract['axis']); q = (xyz*axis).sum(axis=1); nodes = np.unique(surf)
fixed = nodes[q[nodes] <= q.min()+contract['band_fraction']*np.ptp(q)]
ax.scatter(*xyz[fixed[::max(1, len(fixed)//70)]].T, color='#1852b0', s=1.2, depthshade=False)
top = xyz[q >= q.max()-contract['band_fraction']*np.ptp(q)].mean(axis=0); span = np.ptp(xyz, axis=0).max()
ax.quiver(*top, *(axis*span*.3), color='#d0261e', linewidth=1.2, arrow_length_ratio=.35)
mid = (xyz.max(0)+xyz.min(0))/2; rad = span*.47
ax.set_xlim(mid[0]-rad, mid[0]+rad); ax.set_ylim(mid[1]-rad, mid[1]+rad); ax.set_zlim(mid[2]-rad, mid[2]+rad)
ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=22, azim=-58)
T(x+123, 145, r'solve $Kq=f$', 4.9, ha='center', fontweight='bold')
lines(x+123, 58, [f"{fem['nodes']:,} nodes", 'von Mises, p95-clipped'], 4.1, 6, color=GREY, ha='center')
arrow((x+155, 103), (x+160, 103), AMBER, head=5)
cx, cw = x+162, w-168
card(cx, 54, cw, 98, ec=AMBER)
T(cx+cw/2, 145, 'numerical checks', 4.9, AMBER, ha='center', fontweight='bold')
rows = [('force balance', f"{fem['force']:.0e}"), ('energy identity', f"{fem['energy']:.0e}"),
        ('mesh volume', f"{fem['volume']*100:.2f} %"), ('refinement ΔC', f"{fem['refine']*100:.2f} %"),
        ('C vs. target', f"{fem['target']*100:.4f} %")]
for i, (k, v) in enumerate(rows):
    yy = 134-i*10
    T(cx+5, yy, k, 4.3, ha='left'); T(cx+cw-12, yy, v, 4.2, ha='right', family='DejaVu Sans Mono'); tick(cx+cw-10, yy, size=5)
T(cx+5, 85, 'C: compliance; tol. 3 / 5 / 10 %', 3.9, GREY, ha='left')
lines(cx+cw/2, 72, ['geometry is checked first:', 'wrong shapes can match C'], 4.3, 6.6, color=RED, ha='center', style='italic')

# ---------------------------------------------------------------- 7 outcome
x, w = 582, 134; panel(x, BOT, w, BOT_H, '7', 'Recorded outcome', GREEN, '#f6faf7')
card(x+6, 114, w-12, 40, fc=GREEN_BG, ec=GREEN, lw=.8)
T(x+11, 146, '✓ VERIFIED (diagnostic)', 5.0, GREEN, ha='left', fontweight='bold')
lines(x+11, 133, ['strict geometry + FEM checks:', '4 of 6 illustrated 3B cases'], 4.4, 7.4, ha='left')
card(x+6, 54, w-12, 54, fc=RED_BG, ec=RED, lw=.8)
T(x+11, 100, '✗ UNVERIFIED, kept', 5.0, RED, ha='left', fontweight='bold')
lines(x+11, 88, ['patch, execution or mesh', 'failure; no gold edit,', 'no retry, no repair'], 4.4, 7.4, ha='left')

# ---------------------------------------------------------------- flow arrows
arrow((P[1][0]+P[1][1]+1, 318), (P[2][0]-1, 318))
arrow((P[2][0]+P[2][1]+1, 362), (P[3][0]-1, 362), PURPLE)
arrow((P[3][0]+P[3][1]+1, 267), (P[4][0]-1, 267))
arrow((P[4][0]+P[4][1]+1, 300), (P[5][0]-1, 300))
arrow((228, BOT+BOT_H+1), (228, TOP-1), BLUE, ls='--', head=6)
T(232, 181, 'fine-tune', 4.6, BLUE, ha='left', fontweight='bold')
arrow((352, TOP-1), (352, BOT+BOT_H+1), AMBER, ls='--', head=6)
T(356, 181, 'prediction + target solids, if a contract exists', 4.6, AMBER, ha='left', fontweight='bold')
arrow((649, TOP-1), (649, BOT+BOT_H+1), GREEN, head=6)
T(645, 181, f'all {funnel[0][1]} tasks', 4.6, GREEN, ha='right', fontweight='bold')
arrow((575, 110), (581, 110), AMBER, head=5)

# ---------------------------------------------------------------- training vs evaluation strip
card(4, 6, 712, 33, ec='#c3cbd3', lw=.7, r=6)
lines(12, 26.5, ['What trains', 'vs. what checks'], 5.0, 7.6, ha='left', fontweight='bold')
card(88, 10, 262, 25, fc=PURPLE_BG, ec=PURPLE, lw=.7)
T(219, 27, r'$\mathcal{L}(\theta)=-{\sum}_{i\in p}\;\log p_\theta\,(y_i\mid y_{<i},\,C,\,u)$', 5.8, ha='center')
T(219, 16, 'the only training signal: next-token loss on patch tokens', 4.5, PURPLE, ha='center', fontweight='bold')
card(356, 10, 236, 25, fc=AMBER_BG, ec=AMBER, lw=.7)
T(474, 27, 'patch checks · execution · IoU · AST · FEM', 5.0, ha='center', fontweight='bold')
T(474, 16, 'evaluation only: never a reward, loss, retry or repair', 4.5, AMBER, ha='center', fontweight='bold')
lines(600, 26.5, ['Every held-out task is', 'reported, failures included.'], 4.5, 7.6, ha='left')

def save(name, dirs):
    for d in dirs:
        for ext in ('pdf', 'svg', 'png'):
            fig.savefig(d/f'{name}.{ext}', dpi=300)
import sys
save('mechanical-pipeline-overview', [OUT] if '--preview' in sys.argv else [OUT, FIG])
(OUT/'provenance.json').write_text(json.dumps({
    'figure': 'paper/network/figures/mechanical-pipeline-overview.{pdf,svg,png}',
    'case': record['id'], 'instruction': record['instruction'], 'note': 'saved artifacts only; no training, inference or FEM re-run',
    'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in dict.fromkeys(files)}}, indent=2)+'\n')
print('Exported mechanical-pipeline-overview', '(preview only)' if '--preview' in sys.argv else '')
