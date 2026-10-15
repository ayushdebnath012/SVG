# Astra-guided CAD patch repair

The active manuscript describes a frozen Astra pipeline: retrieval, candidate patches, graph search, geometric and semantic verification, FEM, robustness, and repair/backtracking. No model training or learned local verifier is part of this pipeline.

Build `main.tex` with `tectonic main.tex --keep-logs`. `astra-results.tex` and `pipeline-results.tex` preserve saved Astra-only results. The full graph result is 85/124 versus 89/124 for the single Astra answer; retrieval-only is 94/124 and post hoc. Implemented capabilities are distinguished from stages exercised in the recorded experiment.

Earlier manuscript versions and retired model/verifier details are preserved in `../../archive/student-grpo-retired-20261007`; raw experiment artifacts and checkpoints remain in their original directories.
