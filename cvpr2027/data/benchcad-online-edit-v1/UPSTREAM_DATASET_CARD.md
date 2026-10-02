---
configs:
  - config_name: edit-bench
    data_files:
      - split: edit_bench
        path: "edit-bench/data/edit_bench-*.parquet"
  - config_name: code_gen
    data_files:
      - split: code_gen
        path: "code_gen/data/code_gen-*.parquet"
  - config_name: QA
    data_files:
      - split: QA
        path: "QA/qa_*.parquet"
license: cc-by-4.0
task_categories:
  - image-to-text
  - text-generation
  - question-answering
size_categories:
  - 10K<n<100K
tags:
  - cad
  - cadquery
  - 3d
  - synthetic
  - code-generation
---

# BenchCAD

Three-config dataset for CAD evaluation:

- **edit-bench** — held-out CAD edit benchmark.
- **code_gen** — 17,900 synthetic CadQuery samples (compact 12-column variant)
  covering 106 mechanical part families. Each row contains the GT CadQuery code
  plus 5 normalized renders.
- **QA** — CAD question-answering benchmark.

## code_gen schema (12 columns)

| Column | Type | Description |
|---|---|---|
| `stem` | string | unique sample identifier |
| `family` | string | mechanical part family (106 distinct) |
| `variant` | string | sub-variant within family |
| `difficulty` | string | easy / medium / hard |
| `base_plane` | string | initial workplane (XY / XZ / YZ) |
| `standard` | string | ISO/DIN standard if applicable |
| `code` | string | CadQuery Python source (ground truth) |
| `view_0_png` | image | front view (134×134 PNG) |
| `view_1_png` | image | right view |
| `view_2_png` | image | top view |
| `view_3_png` | image | iso view |
| `composite_png` | image | 2×2 composite of the four views |

## Usage

```python
from datasets import load_dataset

ds = load_dataset("BenchCAD/BenchCAD", "code_gen", split="code_gen")
print(ds[0]["family"], ds[0]["difficulty"])
ds[0]["composite_png"].show()
print(ds[0]["code"])
```
