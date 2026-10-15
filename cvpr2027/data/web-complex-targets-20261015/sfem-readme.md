---
license: mit
task_categories:
- other
language:
- en
tags:
- finite-element-method
- stochastic-simulation
- graph-neural-networks
- engineering
- mechanical-engineering
- stress-analysis
- pytorch-geometric
size_categories:
- 10B<n<100B
pretty_name: SFEM Dataset - Neural Network Surrogate Modeling
---

# Dataset Card for SFEM Dataset

This dataset provides 3D finite element meshes with corresponding stress distributions under stochastic point elastic loading conditions, designed for training neural network surrogate models for the stochastic finite element method (SFEM).

## Dataset Details

### Dataset Description

This dataset enables researchers to develop graph neural networks that can predict stress distributions orders of magnitude faster than traditional SFEM simulations. It contains approximately 16,000 CAD geometries with corresponding finite element analysis results under various loading conditions.

- **Curated by:** Jessica Ezemba
- **Language(s):** English (documentation)
- **License:** MIT

### Dataset Sources

- **Repository:** https://github.com/cmudrc/SFEM
- **Paper:** Neural Network Surrogate Modeling for Stochastic FEM using 3D Graph Representations: A Comparative Study (2025)

## Uses

### Direct Use

This dataset is intended for:
- Training graph neural networks for engineering design applications
- Developing surrogate models for finite element analysis
- Research in computational mechanics and machine learning
- Educational purposes in engineering simulation

### Out-of-Scope Use

This dataset should not be used for:
- Safety-critical applications without proper validation
- Real-world structural analysis without engineering oversight
- Applications requiring non-linear material behavior

## Dataset Structure

The dataset follows PyTorch Geometric conventions:

```
Dataset/
├── Pytorch_Geometric_Files/
│   ├── processed/
│   │   ├── pre_filter.pt       # Preprocessing filters
│   │   ├── pre_transform.pt    # Data transformations  
│   │   ├── train_data.pt       # Processed training data (~7GB)
│   │   └── val_data.pt         # Processed validation data (~1.2GB)
│   ├── raw_train_data.tar.gz   # Archived raw training files
│   └── raw_val_data.tar.gz     # Archived raw validation files
└── Step_Files/                 # Original CAD geometries (3GB)
    ├── 000/                    # STEP files (subset 1)
    ├── 001/                    # STEP files (subset 2)
    └── 002/                    # STEP files (subset 3)
```

**Data Fields:**
- `vertices`: 3D coordinates of mesh vertices (N × 3)
- `von_mises_stress`: Stress values at each vertex (N × 1)
- `displacement`: Nodal displacement vectors (N × 3)
- `stress_tensor`: Full stress tensor components (N × 3 × 3)
- `load_class`: Loading condition (small_Load, medium_Load, large_Load)
- `fixed_facet_mask`: Boundary condition indicators

**Data Splits:**
- Training: 85% of geometries
- Validation: 15% of geometries (geometry-based split for proper generalization)

## Dataset Creation

### Curation Rationale

Traditional stochastic finite element methods require thousands of deterministic FEM evaluations, creating prohibitive computational costs. This dataset was created to enable neural network surrogates that can predict stress distributions in milliseconds rather than hours, supporting efficient iterative design exploration.

### Source Data

#### Data Collection and Processing

- **Geometry Source:** CAD geometries generated using [BrepGen](https://github.com/samxuxiang/BrepGen)
- **Mesh Generation:** Gmsh with Frontal-Delaunay algorithm for tetrahedral meshes
- **FEM Software:** FEniCSx (DOLFINx) for finite element analysis
- **Material Properties:** Linear elastic (E = 2.303 GPa, ν = 0.4002)
- **Loading Conditions:** Stochastic point loads (200N, 2000N, 20000N)
- **Statistical Sampling:** 50 realizations per geometry/load combination

#### Who are the source data producers?

The simulation data was generated using open-source computational tools:
- BrepGen for diverse CAD geometry creation
- Gmsh for robust mesh generation
- FEniCSx for finite element computations

## Bias, Risks, and Limitations

**Technical Limitations:**
- Limited to linear elastic material behavior
- Point load conditions only (no distributed loads)
- Specific material properties (not representative of all materials)
- Mesh resolution optimized for efficiency over extreme accuracy

**Potential Biases:**
- Geometry distribution may not represent all engineering applications
- Loading scenarios focused on mechanical components
- Material properties reflect specific engineering domain

### Recommendations

Users should:
- Validate neural network predictions against known analytical solutions
- Understand limitations when applying to safety-critical applications
- Consider appropriate safety factors when using surrogate models
- Acknowledge that computational efficiency comes with inherent approximations

## Citation

**BibTeX:**

```bibtex
@article{ezemba2025neural,
  title={Neural Network Surrogate Modeling for Stochastic FEM using 3D Graph Representations: A Comparative Study},
  author={Ezemba, Jessica and McComb, Christopher and Tucker, Conrad},
  journal={Journal of Mechanical Design},
  pages={1--15},
  year={2025}
}
```

## Dataset Card Contact

For questions or issues, please open an issue in this repository.