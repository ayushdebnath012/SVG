# `fem/compare/` — PLA vs PETG-CF material selection

Question: for the DIY 15:1 cycloidal drive, should the printed parts be PLA
or PETG-CF? Evidence: two full FEA phases with identical meshes/BCs/loads,
only the material card changed.

| File | What it is |
|---|---|
| `index.html` | **Detailed engineering report (webpage).** Open in any browser (works from disk, no server needed). Verdict, method, cards, live-SF results table, all 15 part comparisons, selection guide, caveats, repro. |
| `MATERIAL_COMPARISON.md` | Written comparison + conclusion (same analysis, markdown form). |
| `side_by_side/` | Figs. 01–15: PLA (left) vs PETG-CF (right) composites, 2560×1080, peak/SF/dmax labeled. Figs. 02–03 are the unchanged steel-pin runs. |
| `make_side_by_side.py` | Generator for the composites (PIL). |

Sources: `../pla/` (E 3500 MPa, yield 50 MPa) and `../petg_cf/`
(E 3000 MPa, yield 45 MPa generic). One-line answer: statics tie
(Δσ ≈ 0 everywhere) → decide on temperature/creep: PLA for cool short
runs, PETG-CF for warm sustained duty; same cam-fillet watch item either way.
