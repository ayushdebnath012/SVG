# Carbon/Epoxy Composite Pipe — FEA (ANSYS Composite PrepPost / ACP)

Finite element analysis of a **carbon-fibre/epoxy composite pipe** using
**ANSYS Composite PrepPost (ACP)** in ANSYS Workbench. The project defines a layered
composite lay-up on the pipe geometry (ACP-Pre), solves a structural analysis on the
layered shell, and evaluates the laminate in post-processing (ACP-Post), including
composite failure criteria.

**Author:** Momin Ali Khan — Mechanical / Aeronautical Engineer
(ANSYS FEA; SOLIDWORKS / Creo CAD)

---

## Overview

Composite pipes made from carbon/epoxy laminates are used where high stiffness-to-weight
and corrosion resistance matter (pressure lines, structural tubing, aerospace ducting). The
mechanical behaviour depends not just on the geometry but on the **lay-up** — the number,
orientation, and thickness of each ply. This study models that lay-up explicitly with the
ANSYS ACP workflow rather than treating the wall as an isotropic solid.

The Workbench project chains three linked systems:

1. **ACP (Pre)** — imports the pipe surface, defines the fabric/material, ply thicknesses,
   rosettes (fibre directions), oriented element sets, and the stack-up, then builds the
   layered shell model.
2. **Static Structural** — solves the layered model under the applied loads and supports.
3. **ACP (Post)** — maps results back onto the plies and evaluates laminate results and
   composite **failure criteria** (e.g. maximum stress / Tsai-Wu type) ply-by-ply.

---

## What's in this repository

```
composite-pipe-fea/
├── README.md
├── LICENSE
├── .gitignore
├── Carbon+epoxy.wbpj                 # ANSYS Workbench project (carbon/epoxy ACP)
├── Carbon+epoxy_files/               # its project data (ACP-Pre, MECH, ...)
├── composite pipe.wbpj               # second Workbench project (ACP-Pre/Post + MECH)
├── composite pipe.wbpz               # archived Workbench project
├── composite pipe_files/             # its project data
├── composite pipe.SLDPRT             # solid CAD model (SolidWorks)
├── compsite pipe surface.SLDPRT      # mid-surface model (for shell/ACP)
├── composite pipe.IGS                # neutral CAD (IGES)
├── composite pipe.x_t                # neutral CAD (Parasolid)
├── compsite pipe surface.x_t         # surface model (Parasolid)
└── composite pipe.STL                # tessellated geometry
```

The `*_files/` directories contain the ACP definitions (`ACPCompositeDefinitions.h5`,
`*.acph5`), the Mechanical databases (`*.mechdb`), and the results file (`file.rst`), so the
full analysis can be reopened and re-solved in ANSYS.

---

## How to open

1. Open `Carbon+epoxy.wbpj` (or `composite pipe.wbpj`) in **ANSYS Workbench**.
2. Edit the **ACP (Pre)** cell to review the material, fabric, ply thicknesses, orientations,
   and stack-up.
3. Open the **Model / Static Structural** cell to review mesh, supports, and loads, then
   **Solve**.
4. Open **ACP (Post)** to review deformation, ply stresses/strains, and the composite
   failure criteria.

> `composite pipe.wbpz` is a self-contained Workbench archive — in Workbench use
> **File ▸ Restore Archive** to unpack it if you prefer a clean copy.

---

## Notes / to confirm

The numeric analysis inputs (exact carbon/epoxy ply properties, the lay-up sequence and ply
angles, and the applied load/pressure and boundary conditions) live inside the ANSYS ACP and
Mechanical databases and are not reproduced here in text. Open the project to read or adjust
them. If you'd like, these can be documented explicitly in this README along with result
screenshots (deformation, ply stress, failure factor).

---

## Tools used

- **ANSYS Workbench — Composite PrepPost (ACP)** and **Static Structural**
- **SolidWorks** (solid and mid-surface CAD; IGES / Parasolid / STL exports)

---

## License

Released under the [MIT License](LICENSE) for the documentation. CAD models and the ANSYS
project remain the author's work — please credit if reused.
