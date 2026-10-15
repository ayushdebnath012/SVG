# Process Log — Cycloidal Gearbox Project (full session record)

Goal: reproduce the HowToMechatronics DIY 15:1 cycloidal drive project
(source: https://howtomechatronics.com/how-it-works/what-is-cycloidal-driver-designing-3d-printing-and-testing/)
as a local workspace, then analyze the author's original CAD (STEP) and
prove the key part with FEA.

Environment: Linux, Python 3.14 (numpy + matplotlib, no pip), FreeCAD 1.1.3
via MCP (`STEP_Analysis`/`FEM_Disk` docs), CalculiX 2.21 (installed mid-session).

---

## Phase 1 — Workspace scaffolding + profile math

1. Fetched the tutorial; extracted the design inputs **N=16, R=45, Rr=6.5,
   E=1.5** and the epitrochoid equations (via Omar Younis / SOLIDWORKS blog):
   `x = R·cos t − Rr·cos(t+φ) − E·cos Nt`,
   `y = −R·sin t + Rr·sin(t+φ) + E·sin Nt`,
   `φ = atan2(sin((1−N)t), R/(EN) − cos((1−N)t))`.
2. Created `README.md`, `parameters.json` (single source of truth),
   `docs/{design_notes,BOM,printing,assembly,testing}.md`,
   `electronics/nema17_test.ino`, `slicer/README.md`.
3. Wrote `cad/cycloidal_profile.py` (numpy-only → CSV/DXF/SVG/PNG).
   Verification (`--check`): r 37–40 mm (= R−Rr∓E ✓), lobe FFT peak = 15,
   closure gap 0.39 mm → **PASS**.

## Phase 2 — Parametric FreeCAD build (later discarded)

4. Wrote `cad/freecad_build.py`: epitrochoid disk (600-pt polygon → face →
   extrude 8 mm, Ø22 bore, 6× Ø16 holes, witness hole), housing base/lid,
   eccentric input shaft, output flanges, pins, coupler.
5. Bugs hit and fixed: `__file__` undefined under MCP `exec()` (hardcoded-root
   fallback); `Shape.fuse(a,b)` takes one arg (chained `.fuse()`).
6. Built OK: 8 valid closed solids, STLs exported. Disk Ø79.6×8,
   housing Ø124×34. Screenshots confirmed a plausible stack.

## Phase 3 — Pivot to the author's STEP

7. User supplied their own file; per their choice I **deleted `cad/` and
   `models/`**, closed the generated doc, and adopted
   `Cycloidal Drive - 3D Printable DIY.STEP` (3.0 MB) as the reference.
8. Imported via `Import.insert()` into FreeCAD doc `STEP_Analysis`:
   **216 objects**. Wrote `docs/step_analysis.md`.

## Phase 4 — Assembly analysis (measured, not assumed)

9. Grouped 216 labels → exact BOM census (44× 686, 4× 6802, 2× 6807,
   2 disks, 16+6 pins, spacers, bolts, inserts — all match the article).
10. Key measurements: ring-pin max pair distance = **90.00** (PCD ✓),
    adjacent 17.56 = 2·45·sin(π/16) ✓; output pin circle **Ø49**; disks Ø79.6×5
    stacked 8.0 apart with opposed mass offsets (180° ✓); cams opposed ±~1.5;
    stack order along X mapped (motor 20–80 … output flange to 129).
    Views: full assembly + shell-hidden internals screenshots.

## Phase 5 — Part-by-part reference

11. Per-part cylinder-face inventories (bore counts/sizes), volumes, stack
    positions → `docs/cad_model_understanding.md`: 9 printed groups, purchased
    parts, power path, do-not-break list, remodel rules. Notable finds: disks
    are 5 mm (not 8); "4 mm" rings measure 3.0.

## Phase 6 — Performance prediction (analytical)

12. From 2.6 N·m rated load: pin forces 17.7 N, lobe loads ≈7 N, cam reaction
    ≈173 N. Hand calcs (beam bending, hole bearing stress, clearance stack):
    disk <1 MPa (SF>50), PLA ring pins SF 4–8 but fail ≈10× shock → steel rods
    justified (60× stiffer: 0.16 → 0.003 mm). Backlash budget 0.23°/0.1 mm.
    → `docs/material_performance.md`.

## Phase 7 — FEA of the cycloidal disk (PLA, 200 N shock)

13. Copied disk to fresh doc `FEM_Disk`; mapped faces (bore = Face8+13,
    one output hole = Face2+19, found by nearest-COM pairing).
14. Built `Analysis_PLA`: `ConstraintFixed` (bore), `ConstraintForce` 200 N
    tangential (`DirectionVector`, since `Direction` is a geometry link),
    PLA card (`App::MaterialObject`: E3500/ν0.36/ρ1240/yield50),
    Netgen C3D10 mesh (16,489 nodes / 9,516 volumes).
    Gotchas: `References` needs `[(obj, ("Face8","Face13"))]` tuple form;
    material must be `ObjectsFem.makeMaterialSolid` (plain `App::MaterialObject`
    is invisible to the solver tools); mesh type here is
    `FemMeshShapeNetgenObject` (no Gmsh type in this build).
15. Wrote deck via `femtools.ccxtools.FemToolsCcx` → `fem/DiskPLA.inp`
    (valid: C3D10, *ELASTIC 3500/0.36, *BOUNDARY, 372 *CLOADs).
16. **Found a real 1000× load bug**: meshtools wraps
    `Quantity(Force.getValueAs("N"))`, but `Quantity(float)` is dimensionless
    in FreeCAD, so only **0.2 N** was applied (first solve: 0.0057 MPa max —
    caught by checking). Fix: `fem/fix_cload_units.py` rescales *CLOAD ×1000
    with before/after totals (|F| = 199.77 N ✓).
17. User installed `calculix-ccx`; solver object via
    `ObjectsFem.makeSolverCalculiXCcxTools` (name differs from older docs).
    Ran `ccx -i DiskPLA_fixed` in background: 48,699 eqs, ~2.4 s, converged.
18. Loaded `CCX_Results001` + equilibrium check (reactions = applied ✓):
    **von Mises max 5.70 MPa** (loaded-hole edge), mean 0.98 MPa,
    **displacement max 0.050 mm** → SF ≈ 8.8 @ 200 N shock (≈0.5 MPa @ rated).
19. Visualization: post `ContoursFilter`/`WarpFilter` grouping is broken in
    this build (`addObject` unbound), so rendered via the pipeline ViewObject
    itself (`Pipeline_Fixed200N002.ViewObject.Field = "von Mises Stress"`).
    Saved session `fem/FEM_Disk.FCStd`; results `fem/fea_results.md`.

## Final workspace tree

```text
├── Cycloidal Drive - 3D Printable DIY.STEP   (author's reference CAD)
├── README.md  parameters.json
├── docs/  step_analysis.md  cad_model_understanding.md
│       design_notes.md  BOM.md  printing.md  assembly.md  testing.md
├── electronics/nema17_test.ino  slicer/README.md
└── fem/  FEM_Disk.FCStd  DiskPLA.inp  DiskPLA_fixed.inp  DiskPLA_fixed.{frd,dat,sta,cvg}
         fix_cload_units.py  fea_results.md
```

## Standing warnings for future work

- Re-verify *CLOAD totals after every deck rewrite (1000× bug, §18).
- `CCX_Results` in the saved doc is the buggy 0.2 N run — use `CCX_Results001`.
- Print calibration (hole expansion 0.07 mm) dominates real-world accuracy more
  than any analysis refinement.
