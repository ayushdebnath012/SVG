# Material Performance Prediction — 15:1 cycloidal drive

## Method note (read first)

FEM via the FreeCAD FEM workbench was **not possible in this environment**:
no CalculiX (`ccx`), Gmsh, or Netgen backends are installed, and this
FreeCAD 1.1 build does not register `Fem::MaterialCommon` / `Fem::FemMeshGmsh` /
solver object types, so the meshing + solving path cannot run. Results below
are **analytical predictions** from STEP-measured geometry, the article's
measured 2.6 N·m output, and generic material data — conservative beam,
bearing-stress, and clearance-stack formulas. Good for design decisions and
PLA-vs-steel trade-offs; not a substitute for a physical test.

## Material data used (generic)

| Material | E | Strength (design value) | Density | Notes |
|---|---|---|---|---|
| PLA (printed) | 3.5 GPa | 50 MPa tensile / 70 MPa flexural | 1.24 g/cm³ | Tg ≈ 60 °C; creeps; fatigue limit far below static |
| Steel (pins, shafts) | 210 GPa | 250 MPa yield (structural) | 7.9 g/cm³ | 60× stiffer than PLA |
| 686 bearing steel | 210 GPa | dynamic capacity ≈ 1 kN order | — | purchased, not analyzed in detail |

## Service loads (from 2.6 N·m rated output, 0.26 N·m in)

| Load path | Force |
|---|---|
| Output pins (6× at r 24.5) | **17.7 N each** |
| Ring-lobe contacts (≈8 sharing, r 45) | **≈7 N tangential each** |
| Eccentric cam reaction (E = 1.5) | **≈173 N total** on 6802 journals |

## Part-by-part verdict

| Part | Material | Stress @ rated | Safety factor | Prediction |
|---|---|---|---|---|
| Cycloidal disk | PLA | <1 MPa (hole bearing 0.27 MPa; 2.7 MPa @ 10× shock) | >50 static | Strength fine in PLA **or** steel; life governed by wear/creep, not yielding. Print a spare. |
| Ring pins Ø6×35 | PLA → **steel recommended** | 8–17 MPa bending | PLA ≈ 4–8 static, **fails ≈10× shock (165 MPa > 70)** | Validates the article: use ground Ø6 steel rod. Steel deflection 0.003 vs PLA 0.16 mm (60× stiffer) — pin flex is the main accuracy thief. |
| Output pins + M3×20 | steel bolt / PLA core | bolt shear ≈ 3.5 MPa | >50 | Fine as designed. |
| Input-shaft journals Ø15 | PLA + 6802 | contact ≈ 2.3 MPa | >20 static | OK statically; watch bore wear/creep over time. |
| 686 bearings @ ≈20 N | bearing steel | ≪ capacity (~1 kN) | >40 | Bearings never the limit. |
| Housing/lid Ø115 drum | PLA | reaction shear negligible | very high | Stiffness, not strength, matters — keep walls/infill up. |

## System-level predictions (PLA build, NEMA 17)

- **Torque:** ~2.6 N·m rated demonstrated; practical PLA peak ≈ 2–2.5 N·m
  continuous (heat/creep), ultimate ≈ 10–20 N·m capped by pin bending.
- **Efficiency ≈ 60–70%** (matches article's 66%); metal + accurate bores → ~85–90%.
- **Backlash:** near zero when calibrated. Budget: every 0.1 mm of print
  clearance ≈ **0.23° output slop** (at r 24.5) — this is why the 0.07 mm hole
  expansion matters more than any other setting.
- **Resolution:** 0.12°/full step, 0.015° @ 8× microstep.
- **Speed:** 20 rpm out @ 300 rpm in; ≈80 rpm out at typical NEMA 17 max.
- **Mass:** ≈ 406 g printed PLA + ≈ 230 g bearings/hardware + ≈ 280 g motor
  → **≈ 0.9–1.1 kg all-in**.
- **Thermal ceiling:** keep the gearbox < 60 °C (PLA Tg); motor heat soak +
  friction are the sustained-duty limits, not tooth strength.
- **Dominant compliances (windup / positioning error):** ring-pin bending,
  then rolling-contact deflection, then disk-hole clearance — in that order.
  Steel pins buy the most accuracy per gram.

## What would change with metal disks/housing

Almost nothing at rated load (stresses are already ≈1% of PLA strength).
Metal pays off only for: continuous duty >60 °C, shock loads >10× rated,
or holding micron-level accuracy under load. Upgrade order if you need more:
**steel ring pins → steel output pins → metal disks → metal housing.**
