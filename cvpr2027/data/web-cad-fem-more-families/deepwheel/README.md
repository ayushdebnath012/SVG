---
license: cc-by-nc-4.0
pretty_name: DeepWheel
size_categories:
  - 1K<n<10K
task_categories:
  - tabular-regression
  - image-to-3d
tags:
  - engineering-design
  - automotive
  - wheel
  - wheel-design
  - 3d
  - mesh
  - cad
  - depth-estimation
  - surrogate-modeling
  - modal-analysis
---

<div align="center">
  <img src="assets/banner.png" alt="DeepWheel — generated 3D wheel designs" width="100%">
</div>

<h1 align="center">DeepWheel</h1>
<p align="center"><b>Generating a 3D Synthetic Wheel Dataset for Design and Performance Evaluation</b></p>

<p align="center">
  <a href="https://doi.org/10.1115/1.4069899"><img src="https://img.shields.io/badge/J.%20Mech.%20Des.-10.1115%2F1.4069899-2ea44f.svg" alt="Journal of Mechanical Design"></a>
  <a href="https://arxiv.org/abs/2504.11347"><img src="https://img.shields.io/badge/arXiv-2504.11347-b31b1b.svg" alt="arXiv"></a>
  <img src="https://img.shields.io/badge/license-CC--BY--NC%204.0-blue.svg" alt="License: CC-BY-NC 4.0">
</p>

<p align="center"><b>Published in ASME Journal of Mechanical Design</b> (2026) 148(5): 051702 &nbsp;·&nbsp; KAIST SmartDesignLab / Narnia Labs</p>

---

## Contents
- [Overview](#overview)
- [The data, qualitatively](#the-data-qualitatively)
- [Dataset structure](#dataset-structure)
- [Usage](#usage)
- [Applications](#applications)
- [Citation](#citation)
- [License](#license)

---

## Overview

> **DeepWheel** is a **synthetic automotive wheel** dataset for **design and performance evaluation**,
> generated with a generative-AI framework: 2D renders are synthesized with **Stable Diffusion**, lifted to
> 3D via **2.5D depth estimation + reconstruction**, and **structurally simulated** to extract engineering
> performance. It provides **6,000+ photo-realistic images** and **900+ structurally-analyzed 3D models**,
> each as multi-view images, depth maps, a reconstructed surface mesh, and a parametric CAD model, paired with
> **performance labels** (mass and modal natural frequencies) — coupling **3D geometry ↔ performance** for
> data-driven design, surrogate modelling, and image-to-3D research.

<div align="center">
  <img src="assets/teaser.gif" alt="A generated wheel spinning about its axle" width="42%">
  <br><sub>A reconstructed wheel design, spinning about its axle.</sub>
</div>

| | |
|---|---|
| **Domain** | automotive wheels (rims) |
| **Scale** | 6,000+ rendered images · 900+ structurally-analyzed 3D models |
| **Modalities** | rendered images · depth maps · 3D meshes · CAD models |
| **Performance labels** | mass · modal frequencies (Mode 7, Mode 11) |
| **Paper** | *J. Mech. Des.* (2026) 148(5):051702 · [doi:10.1115/1.4069899](https://doi.org/10.1115/1.4069899) · [arXiv:2504.11347](https://arxiv.org/abs/2504.11347) |

---

## The data, qualitatively

<div align="center">
  <img src="assets/banner.png" alt="Variety of generated wheel designs" width="100%">
  <br><sub><b>Generated wheel-design variety</b> — reconstructed 3D rim meshes spanning a range of spoke geometries.</sub>
</div>

---

## Dataset structure

```
DeepWheel/
├── 1_rendered_images.zip      # multi-view renders of each design
├── 2_predicted_depth_maps.zip # predicted depth maps
├── 3_3D_recon_meshes.zip      # reconstructed surface meshes (.stl)
├── 4_3D_cad_models.zip        # parametric CAD models
├── deepwheel_sim_results.csv  # performance labels (per design)
└── readme.docx                # official documentation (incl. file-matching instructions)
```

**Modalities**

| Modality | File | Content |
|---|---|---|
| Rendered images | `1_rendered_images/…` | multi-view RGB renders |
| Depth maps | `2_predicted_depth_maps/…` | predicted per-view depth |
| 3D meshes | `3_3D_recon_meshes/*.stl` | reconstructed surface meshes |
| CAD models | `4_3D_cad_models/…` | parametric CAD geometry |
| Performance labels | `deepwheel_sim_results.csv` | `file_name, Mass, Mode7 Freq, Mode11 Freq` |

---

## Usage

```bash
huggingface-cli download KAIST-SmartDesignLab/DeepWheel --repo-type dataset --local-dir DeepWheel
cd DeepWheel && for f in *.zip; do unzip -q "$f"; done
```

```python
import pandas as pd, trimesh
labels = pd.read_csv("deepwheel_sim_results.csv").set_index("file_name")
case   = labels.index[0]
mesh   = trimesh.load(f"stl/{case}.stl")          # reconstructed wheel
mass, f7, f11 = labels.loc[case, ["Mass", "Mode7 Freq", "Mode11 Freq"]]
```

---

## Applications

- **Surrogate modelling** — predict mass and modal frequencies from 3D geometry or rendered views.
- **Image-to-3D** — reconstruct wheel geometry from images / depth (paired renders + meshes + CAD).
- **Generative & inverse design** — generate manufacturable wheel rims with target performance.
- **Multimodal learning** — images ↔ depth ↔ mesh ↔ CAD ↔ performance.

---

## Citation

```bibtex
@article{deepwheel2026,
  title   = {DeepWheel: Generating a 3D Synthetic Wheel Dataset for Design and Performance Evaluation},
  journal = {Journal of Mechanical Design},
  volume  = {148},
  number  = {5},
  pages   = {051702},
  year    = {2026},
  doi     = {10.1115/1.4069899}
}
```

---

## License

Released under **CC BY-NC 4.0** (Creative Commons Attribution-NonCommercial 4.0 International). Use,
modification, and redistribution are permitted for **non-commercial** purposes with attribution;
commercial use of the dataset or derivative models is prohibited. See `readme.docx` and the paper
([doi:10.1115/1.4069899](https://doi.org/10.1115/1.4069899)) for details. DeepWheel — KAIST Smart Design Lab / Narnia Labs.
