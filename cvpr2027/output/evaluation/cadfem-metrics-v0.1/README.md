# CADFEM evaluation metrics v0.1

See [EVALUATION_SPEC.md](EVALUATION_SPEC.md) for definitions, primary sources, track separation, calibration, and commands.

**Headline:** family-macro verified joint success. A required CAD, FEM, convergence or workflow check cannot be replaced by a high similarity score. Report CAD and FEM diagnostics separately.

- CAD: executable valid geometry, physical-unit Chamfer L1/squared L2, sampled Hausdorff/HD95, surface F1, BREP/voxel IoU, feature/interface checks and edit preservation. BenchCAD 2 formula compatibility is separate from engineering scoring.
- FEM: published scalar error; integration-weighted displacement/stress/thermal field errors; energy, force/moment balance, mode MAC and convergence diagnostics. Advanced-physics adapters are specified and remain pending.
- Thresholds: frozen per task/family after baseline calibration; null is not a pass.

Implementation: `cvpr2027/scripts/cadfem_metrics.py`; policy: `cvpr2027/configs/cadfem-metrics-v0.1.json`.

All **20 regression tests passed**. See [verification.json](verification.json), [sources.json](sources.json), and the existing-artifact demonstration JSON files. No model API calls or new solver trials were performed. This is not a full regrade of the frozen dataset.
