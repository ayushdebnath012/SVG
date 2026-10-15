# PETG-CF phase — plan (FEA of the same parts in PETG-CF)

## Proposed generic material card (VERIFY against your spool before running)

| Property | Proposed value | Source |
|---|---|---|
| Young's modulus | **3000 MPa** | mid-range: Bambu TDS 2460±230 MPa (X-Y); SUNLU flexural 2700 MPa; generic PETG-CF 2500–4000 MPa |
| Poisson's ratio | 0.36 | same assumption as PLA (unfilled-test data scarce) |
| Density | 1300 kg/m³ | CF-filled PETG ≈ 1.27–1.33 g/cm³ |
| Design tensile (yield) | **45 MPa** | conservative: SUNLU 35 MPa … Bambu-class 50–60 MPa; confirm brand |
| Heat deflection | ~75–80 °C | vs 60 °C PLA — the real reason to switch |

`batch_fea_setup.py` takes the material as a dict, so rerunning is mechanical:

```python
PETGCF = {"Name": "PETG-CF-Generic", "YoungsModulus": "3000 MPa",
          "PoissonRatio": "0.36", "Density": "1300 kg/m^3",
          "YieldStrength": "45 MPa", "UltimateTensileStrength": "55 MPa"}
```

## Procedure (mirror of PLA)

1. Confirm brand/datasheet → lock the card above (edit this file with the
   final numbers + source).
2. Decide scope: same 15 runs (recommended — meshes/BCs are proven), or
   torque-path subset first (disk, cam P2, flanges, coupler, ring pin).
   Steel pins stay steel (not printed) — no rerun needed.
3. For each part: same doc pattern (`FEM_<Part>_PETGCF`), same faces (see
   `../pla/fea_all_parts.md` load-case table), same mesh sizes → INP →
   `fix_cload_units.py` → `ccx` → load results → equilibrium check.
4. Expectation (linear statics): with E 3000 vs 3500 MPa, stresses will be
   **near-identical** to PLA (stress in a statically-determinate fixture is
   load/area, not E); displacements scale ×(3500/3000) ≈ **+17 %**.
   The comparison that matters is SF vs the new yield + temperature/creep
   headroom, not the stress field.
5. Store under `fem/petg_cf/FEM_*/`, figures in `fem/petg_cf/report_images/`
   (same 01–15 numbering), results in `fem/petg_cf/fea_all_parts_PETGCF.md`.

## What to tell me when ready

- Filament brand (or "use the generic card above").
- Full rerun or torque-path subset.
