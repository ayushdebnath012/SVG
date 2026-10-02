# ReSolve paper

Current title: **ReSolve: Parse, Patch, and Check Engineering SVGs**.

The paper covers the learned network editor, a bounded deterministic truss/plate editing route, and separately identified frame/CAD diagnostics. The legacy directory name is retained. [Current evidence and examples](../../reports/ENGINEERING_EDITOR_OVERVIEW_20261001.md) lists the evaluated contracts and results.

- `main.tex`: manuscript entry point; `main.pdf`: current rendered draft.
- `sections/structures.tex`: structural/mechanical method, audit, examples and broader learned-patcher limits.
- `figures/editor-overview.svg`: editable bridge/plate overview; `editor-*-source.svg` and `editor-*-edited.svg`: full replayed artifacts.
- `figures/astra-frame-decline-annotated.svg`: checked frame example, with presentation highlights.
- `../../runs/paper-engineering-examples-20261001/`: reproducible edit outputs, patches and verification records.

Build from this directory with XeLaTeX, BibTeX and two further XeLaTeX passes. Rebuild examples from the package root with `../.venv/bin/python scripts/build_engineering_paper_examples.py`. The example builder reads local saved data and makes no API calls.

The current PDF is a research draft. Its different protocols are not a pooled benchmark of one universal learned editor. Preserve the distinction between FEM equilibrium, design-limit compliance, geometry checks and learned edit fidelity when revising claims.
