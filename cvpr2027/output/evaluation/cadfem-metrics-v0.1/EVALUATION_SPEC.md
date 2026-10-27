# CADFEM evaluation specification v0.1

Prepared 16 October 2026. This is a proposed benchmark protocol and an initial diagnostic implementation, not a newly validated dataset release or an official reproduction of another benchmark's leaderboard. No model API calls are needed to compute these metrics.

## 1. What the benchmark measures

Report each task track separately:

1. **CAD generation/editing:** create an executable, valid, dimensionally correct CAD part or assembly.
2. **FEM given CAD:** use supplied geometry, select the correct material, loads and supports, mesh it, and produce a verified numerical solution. Supplied CAD does not earn CAD-building credit.
3. **Drawing/specification to CAD to FEM:** reconstruct geometry and solve the requested engineering problem on that reconstructed geometry.
4. **CAD edit to FEM:** perform a functional edit, preserve protected geometry, and analyze the edited geometry.

Planar SVG/frame analysis, hydraulic networks, CAD-only tasks and full mechanical CAD+FEM must have separate leaderboard slices. Beam/shell FEM is legitimate FEM; it is not interchangeable with a solid-mechanics CAD reconstruction task. The geometry CLI currently accepts 3D solid STEP only; legitimate surface/shell/beam geometries require dedicated adapters.

The headline is **verified joint success**, accompanied by a CAD/FEM scorecard. A model must not compensate for incorrect physics with high shape similarity, or receive a workflow pass for returning a correct published number.

## 2. Source-to-metric mapping

| Source | Adopted ideas | Our explicit adaptation |
|---|---|---|
| [BenchCAD, 2026](https://arxiv.org/html/2605.10865v1), Sec. 4.3, App. N | Execution, voxel IoU, Chamfer/Hausdorff, feature F1, essential-operation recall, edit headroom and preservation | Keep physical dimensions; report implementation differences rather than claiming identical official scores. |
| [BenchCAD 2.0 official specification](https://github.com/BenchCAD-org/benchcad-2-main/blob/main/docs/METRICS.md) | Current part/topology and assembly scoring | Separate compatibility reporting; technical specification, not a paper. |
| [CADFit, ICML 2026](https://proceedings.mlr.press/v306/nehme26a.html) | Invalid ratio, volume overlap, surface distance | Add explicit engineering/setup gates. |
| [CADEngBench, 2026 preprint](https://arxiv.org/html/2608.09296v1), L0-L3 | Executable CAD, engineering/edit checks, matched geometry/reference FEA, displacement, robust stress and compliance comparison | Separate CAD, simulation reach and physical agreement; retain source-published quantities. |
| [PDEAgent-Bench, 2026 preprint](https://arxiv.org/html/2605.09636v1) | Executability, calibrated relative L2 accuracy and runtime stages | Calibrate within our own task families and hardware. |
| [FEABench, 2025](https://arxiv.org/html/2504.06260v1) | Verify target semantics/export before interpreting numerical agreement | Prefer evaluator-owned parsing and replay over self-reported results or an LLM-only judge. |
| [PDEBench, NeurIPS 2022](https://github.com/pdebench/PDEBench) | Field, boundary and conservation diagnostics | Use physical integration weights on unstructured FEM grids. |
| [CADGenBench maintainer specification](https://github.com/huggingface/cadgenbench/blob/main/docs/metrics.md) | Validity, shape, topology and interface separation | These engineering feature checks are required even when global overlap is high. This source is technical documentation, not a paper. |
| [NASA spatial convergence guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html) | Richardson/GCI diagnostics | Mesh-to-mesh change does not independently certify convergence. This is verification guidance, not a benchmark paper. |

`sources.json` records the sources and intended use. Proposed gates, sampling choices and threshold policy below are our design. We do not reproduce BenchCAD's composite weights, Feature-F1 matcher, operation extraction, rendering or alignment pipeline exactly.

### Current BenchCAD 2.0 compatibility

Its current part score is `0.8 * chance_corrected_IoU + 0.2 * topology`:
`IoU_term=clip((IoU-primitive_baseline)/(1-primitive_baseline),0,1)`;
topology multiplies `((min+1)/(max+1))^2` over three Betti counts.
Each part is normalized separately; absolute scale is not assessed. Surface F1 is diagnostic. Assembly scoring uses mean leave-one-part-type-out IoU gain; reconstruction-plus-assembly multiplies part and assembly scores. See the upstream specification for exact preprocessing and exceptions.

Our `benchcad2_part_terms` combines supplied upstream measurements only. It does not extract topology or reproduce voxelization. Use the pinned upstream evaluator for an official-comparable result. Its primitive baseline differs from BenchCAD v1's original-to-target edit baseline.

For engineering evaluation, retain physical scale, require critical interfaces, and report assembly BOM/count correctness, translation error in physical units, rotation error, gaps/penetrations and contact-pair correctness. These assembly adapters remain pending. Missing mandatory checks never redistribute weight into a pass.

## 3. CAD metrics

### 3.1 Execution and solid validity

Record CAD code replay success, STEP/BREP export/import, OpenCascade validity, positive volume, watertight/meshable representation where applicable, expected physical components and unexpected disconnected bodies. A floating boss can retain high IoU and must still fail its attachment check.

Face count, edge count and raw BREP solid count are diagnostics, not universal equality gates: equivalent CAD can be segmented differently, and a multi-material continuous body can contain many solid regions. Component/connectivity expectations belong to each task's engineering contract. Multi-part assemblies may legitimately contain separate bodies.

Invalid candidate geometry receives zero CAD success/IoU credit in aggregate reports. Distance for invalid shapes is reported as unavailable, together with invalid rate; never average only valid candidates without showing the denominator.

### 3.2 Pose, scale and sampling

- Default: compare in the task's physical coordinate frame and units.
- If the drawing leaves pose unspecified, an evaluator-authorized rigid transform may align the candidate. The initial implementation supports translation plus the 24 proper axis rotations, matching the old rigging task's permitted pose convention. Translation starts from centre-of-mass alignment and is refined by point-to-plane least squares over pairs within a cut-off that shrinks from 10x to 1x the F1 threshold. Bounding-box centres are not used: one extra 20 mm boss shifted a bounding-box-centred plate by 10 mm and cut its IoU from 0.987 to 0.82.
- Never optimize scale or reflection for the engineering grade. A scaled part can have a plausible silhouette and a different stiffness, mass or stress.
- Edited parts remain in their specified datum frame; alignment must not undo an explicitly requested move/rotation or conceal an edit of the wrong component.
- Record the selected transform. Loads, constraints, vectors, tensors and interfaces must be transformed consistently by trusted adapters before any field comparison. A CAD alignment alone does not validate FEM setup.
- Sample both surfaces uniformly by triangle area, initially 20,000 points each, fixed seed 7, tessellation tolerance `1e-4 D_ref`, where `D_ref` is the reference bounding-box diagonal. There is no per-candidate normalization.
- Each sample's distance is measured to the other part's tessellated surface (exact point-to-triangle), not to the other part's nearest sample. Point-to-point distances between two independent samplings have a sampling floor that dominated real errors: an identical plate built with different CAD operations scored CD_L1 0.48 mm and F1 0.69 at 20,000 points, worse than a plate with a 1 mm hole error (0.24 mm, F1 0.89). With point-to-surface distances the identical plate scores 0 and F1 1, and the wrong hole scores HD 1.000 mm. The remaining floor is the tessellation chord error, below `1e-4 D_ref` per surface. Run identity and CAD-reexport baselines before setting thresholds. Small critical features need local measurements even when globally undersampled.
- STEP files are read with every root shape; a multi-body file is not reduced to its first body.

### 3.3 Chamfer and Hausdorff distance

Let `P` be predicted surface samples, `Q` reference samples, `S_P` and `S_Q` the tessellated surfaces, and `d(p,S_Q)=min_{x in S_Q} ||p-x||_2`. In the formulas below `d(p,Q)` means `d(p,S_Q)` and `d(q,P)` means `d(q,S_P)`. The point-cloud helper `surface_metrics` keeps the point-to-point convention for inputs that have no surface.

```
CD_L1 = 0.5 * (mean_p d(p,Q) + mean_q d(q,P))
CD_L2_squared = 0.5 * (mean_p d(p,Q)^2 + mean_q d(q,P)^2)
nCD_L1 = CD_L1 / D_ref
nCD_L2_squared = CD_L2_squared / D_ref^2
HD = max(max_p d(p,Q), max_q d(q,P))
HD95 = max(quantile_0.95 d(P,Q), quantile_0.95 d(Q,P))
```

Report both physical and normalized values and the exact convention. Chamfer definitions differ between papers by squaring, directional sum/mean and normalization. These values must not be labelled directly comparable to an official BenchCAD CD without matching its implementation.

### 3.4 Surface F-score and volume overlap

For distance threshold `tau`, precision is the fraction of predicted samples within `tau` of the reference; recall reverses the direction. `F1=2PR/(P+R)`. The initial diagnostic uses `tau=0.005 D_ref`; this is a sampling setting, not a calibrated engineering tolerance. Report sensitivity and task-specific physical tolerances.

```
BRep IoU = volume(S_pred intersect S_ref) / volume(S_pred union S_ref)
relative volume error = |V_pred - V_ref| / V_ref
relative symmetric difference = volume(S_pred xor S_ref) / V_ref
voxel IoU = common occupied cell count / union occupied cell count
```

Exact BREP overlap and voxel IoU are distinct metrics. The CLI computes BREP overlap and optionally voxel IoU in one shared physical grid; report grid resolution/cell size, with 32/64/128 sensitivity where practical. Independently normalized official BenchCAD scores may be reported in a separate compatibility experiment using the upstream evaluator. They must not replace the physical-scale grade.

### 3.5 Features, topology and interfaces

Feature precision/recall/F1 uses evaluator-detected and geometrically matched holes, slots, fillets, chamfers, ribs and other required features. Matching checks type, center/axis, physical dimensions and host body, using task tolerances; perform one-to-one matching, not word matching on generated code. Report dimensional errors individually. Exempt unspecified features from exact-reference matching.

Report essential-operation recall only when the task requires an editable construction method. The implemented helper accepts trusted executed-operation sets; it is not BenchCAD's official extractor. Text/AST occurrence alone cannot prove an operation was used or is semantically correct. A physically equivalent alternative construction must not fail an operation gate unless construction/editability is explicitly required.

Add protected interface/keep-in/keep-out volume checks and body connectivity; these are stronger safeguards for bolt holes, bearing seats, seal faces and attachments than global Chamfer distance. Betti-number/topology extraction, automatic feature recognition and interface validators remain adapters to implement; missing results remain unverified.

### 3.6 BenchCAD edit metric and preservation

For original `S0`, generated `Sg` and target `St`, define baseline `b=IoU(S0,St)` and candidate score `a=IoU(Sg,St)`:

```
EditHeadroom = clip((a-b)/(1-b), 0, 1)
```

An unchanged input earns zero improvement, a perfect target earns one. Use BenchCAD's `b<0.99` eligibility condition for this comparison; near-no-op target pairs are flagged N/A and curated separately, not assigned a fabricated score. Report the exact IoU variant used.

Also measure non-target preservation outside an evaluator-authored edit ROI: normalized symmetric difference between generated and original protected material, plus protected dimensions/interfaces. The ROI and invariants must come from the task, not the model. This geometric preservation adapter is specified but not implemented in the initial module.

## 4. FEM metrics

### 4.1 Verified setup and solver reach

Check geometry used by the solver against submitted CAD; material assignments and units; constitutive law; thickness/plane-stress/plane-strain/shell assumptions; load magnitude, direction, distribution and region; all constraints and rigid-body stabilization; contact/friction definitions; mesh element type/order, Jacobians, quality and material interfaces; initial conditions; time/load increments; solver convergence.

Record `simulation_reached`, `solver_replay_verified`, and `setup_verified` separately. Finite stress values and a successful solver exit are not sufficient: the old wrong-hole constraint and skipped buckling-mode examples can solve the wrong problem successfully.

### 4.2 Published scalar quantities

For each scalar `q`, report absolute error, relative error where meaningful, unit, reference provenance and the fixed tolerance:

```
absolute_error = |q_pred - q_ref|
relative_error = absolute_error / |q_ref - offset|   # undefined at zero denominator
pass_q = absolute_error <= tau_abs + tau_rel * |q_ref - offset|
```

The offset is declared by the evaluator, e.g. an agreed thermal reference; it is never inferred to improve a score. Near-zero or signed outputs use meaningful absolute tolerances. Reject booleans, numeric strings, NaN/Inf, wrong units and wrong target definitions.

For strictly positive response magnitudes, optionally report `abs(log(q_pred/q_ref))`, following the multiplicative comparison idea in CADEngBench. It is inapplicable to signed cooling differences, negative eigenvalues and zero outputs. For parameterized design tasks report the worst discrepancy over predeclared states, not only a favorable state.

Preserve original published targets and labels. A nodal stress-legend maximum is not interchangeable with Gauss-point stress or p95. If independent reproduction contradicts a published target, hold the reference and document both; do not widen its band after seeing model predictions or silently replace the source value.

### 4.3 FEM fields

The evaluator maps candidate and reference solutions onto common physical quadrature/query points, with full required domain coverage, consistent component basis/units, stress recovery convention, material interface handling and time grid. Do not compare node indices across different meshes. Do not score only the overlap region or discard unmapped/nonfinite values.

For vector/tensor/scalar field `f`, positive spatial/time weights `w`:

```
e_L2(f) = sqrt(sum_i w_i ||f_pred_i - f_ref_i||^2 /
               sum_i w_i ||f_ref_i||^2)
weighted_RMSE = sqrt(sum_i w_i ||error_i||^2 / (component_count * sum_i w_i))
```

For zero reference fields relative L2 is undefined; report absolute L2/RMSE and use the task's absolute contract. For stress tensors, a six-component vector must apply the correct tensor/Frobenius shear weights or be expanded to the full 3x3 tensor. Engineering strain shear conventions require explicit conversion.

Report displacement-vector error, stress-tensor error, and temperature error as applicable. For temperature, report RMSE in kelvin and normalize only against a prescribed temperature rise/range, not the arbitrary Celsius/Kelvin origin. L-infinity/local probe errors prevent a global norm from hiding a critical local discrepancy.

The field CLI only compares evaluator-prepared common-grid NPZs. Cross-mesh interpolation, vector/tensor rotation, correspondence, time interpolation and tensor-weight conversion are not implemented automatically. Native `fields.npz` files with different meshes cannot be passed directly to this command.

### 4.4 Energy, robust stress and physics checks

For matched linear problems on common unconstrained displacement DOFs with trusted positive-definite reference operator `K_ref`:

```
e_energy = sqrt((u_pred-u_ref)^T K_ref (u_pred-u_ref) /
                (u_ref^T K_ref u_ref))
```

This helper is for small dense reference operators. Cross-mesh continuum energy norms and nonlinear constitutive-energy errors require dedicated evaluators. Do not use this expression unchanged for plasticity, different geometry/operators, thermal fields or unremoved rigid-body modes.

Add compliance/strain-energy error and volume-weighted von Mises p95 where independently sourced references exist. Retain required maxima separately; p95 reduces sensitivity to isolated stress peaks but cannot replace stress-concentration/fatigue/crack-tip checks.

For force and reaction vectors `F_i` and couples `M_i` in a declared frame:

```
force residual = ||sum F_i|| / sum ||F_i||
moment residual = ||sum (x_i cross F_i + M_i)|| /
                  (D_ref * sum ||F_i|| + sum ||M_i||)
```

Include applied loads and reactions; normalize by magnitudes rather than a near-zero net applied force. Account for inertia in dynamics; rigid stabilization forces must be disclosed. Boundary residuals, thermal storage/flux balance and contact gap/complementarity are separate physics-specific gates. Zero denominators are N/A, not automatic passes.

### 4.5 Modal, buckling and nonlinear tasks

- Modal: relative frequency errors plus mass-weighted MAC, `|phi_p^T M phi_r|^2 / ((phi_p^T M phi_p)(phi_r^T M phi_r))`. Pair modes before comparison; repeated eigenspaces need subspace comparison, not arbitrary mode-by-mode labels. The MAC helper assumes evaluator-registered real DOFs and prepaired modes.
- Buckling: smallest relevant positive factor, corresponding mode and prebuckling setup; check solver spectral/mode selection and load normalization. A repeated higher mode is not a converged first mode.
- Contact: force-displacement response, contact patch area/pressure, gap and penetration normalized by local geometry, action/reaction balance and complementarity/friction residuals. These adapters remain specified rather than implemented.
- Plasticity/postbuckling: path/curve error, yield/collapse load, displacement at fixed loads, tangent response and dissipated energy; compare the same loading path. Snap-through needs a suitable path-following protocol.
- Transient heat/dynamics: time-weighted field/curve errors, extrema and event times, initial/boundary enforcement, time-step refinement and energy balance.
- Fracture: KI/KII/J or energy-release rate, crack path/front distance and appropriate singularity treatment. Global stress maxima cannot assess fracture correctly.

Missing advanced-physics adapters do not become synthetic full-FEM passes.

## 5. Reference quality and tolerances

Before model trials, an evaluator freezes source/reference hashes, geometry/setup selectors, solver conventions, baseline mesh/time studies, target extraction, acceptable uncertainty and runtime/memory budgets. References need independent reproduction or exact analytical validation for the primary verified leaderboard; source-figure-only provisional cases remain a diagnostic slice.

PDEAgent-Bench uses calibration-baseline errors with a floor and multiplier. We adopt the calibration principle, not its numerical defaults wholesale. For our field errors a possible declared rule is `tau_field=max(alpha*e_baseline,tau_floor)`; `alpha` and `tau_floor` must be selected per physical family before model evaluation. Scalar QoI bands also include justified source rounding and spatial/time discretization uncertainty. Publish threshold-sensitivity results.

Geometry tolerances derive from drawing/manufacturing requirements plus a calibrated tessellation/sampling floor; do not adopt 0.99999 IoU as a universal BenchCAD pass rule. That threshold exists in our legacy local scripts and is not identified here as a paper-standard engineering threshold.

## 6. Convergence and reproducibility

Use at least three completed, systematic spatial levels and, for transients, time-step levels. Preserve quantities, element counts/order, quality, runtime, branch/mode identity and extraction convention. Richardson observed order and GCI are useful only when their assumptions apply. Identical values, oscillating modes, different setups or a timed-out last mesh do not establish convergence.

The initial convergence helper accepts three equally ratio-spaced coarse-to-fine mesh sizes with a monotone contracting quantity sequence. It reports observed order/GCI and always returns `convergence_certified=false`: an evaluator must review asymptotic assumptions and the calibrated acceptance criterion. Other sequences remain diagnostic rather than being forced into an extrapolation formula.

Clean execution must replay the submitted script with network/reference access blocked. Check hashes of source, CAD, mesh, fields, solver logs and reference artifacts. The FEM geometry must correspond to the submitted CAD. Reuse the current evaluator-owned, hash-bound review protocol; do not accept a candidate's `workflow_verified=true` assertion.

## 7. Joint success and aggregation

For a full CAD+FEM task, let each `G` be a verified evaluator gate:

```
JointPass = G_CAD_replay AND G_CAD_valid AND G_geometry AND G_features_interfaces
            AND G_setup AND G_mesh AND G_solver_replay AND G_QoI
            AND G_fields AND G_convergence_review AND G_artifact_hashes
```

Only task-applicable gates belong to its frozen contract. A failed gate yields joint failure; a missing required check yields an unverified non-pass, with that status visible. An unavailable/unvalidated reference yields a held case excluded from the primary ranking, with coverage counts reported. The metric helper consumes trusted evaluator evidence but does not create or authenticate it.

Report CAD success rate, simulation reach, numerical success, workflow-verified success and joint success separately. No arithmetic weighted average can establish joint success. Continuous raw metrics remain useful diagnostics and should have their own coverage/denominator.

Headline aggregation:

```
JointSR_family_macro = mean_over_families(mean_over_eligible_tasks(JointPass))
```

Also report task-micro rates, per-family/per-physics/per-track values, source/reference readiness, stage failures and abstention. Generation/edit variants and repeated samples of one design are correlated: bootstrap at source-design/family level. Keep single-attempt and tool-assisted/repair protocols separate. Report first-attempt success, success after a fixed repair budget, number of calls and cumulative cost; do not pool them as independent tasks.

API rejections and corrupt/missing references are infrastructure/data exclusions, not model capability failures. Explicit abstention is analysis incompletion, not a wrong numerical claim. Resource-limited noncompletion must be tagged separately; it is not by itself evidence of incorrect physics. Report best-of-k/pass@k only with declared sampling/selection and appropriate denominators.

## 8. Cost and efficiency

Log input/cached/output/reasoning tokens, API spend, solver CPU/wall time, peak memory and time to verified solution. Cost per verified success uses verified successes only and is undefined when none pass. Publish accuracy-versus-cost/latency curves under equal tool access and fixed budgets. Credit-budget/API failures never count as model failures.

## 9. Implemented artifacts and limits

- Metric code: `cvpr2027/scripts/cadfem_metrics.py`.
- Machine-readable policy: `cvpr2027/configs/cadfem-metrics-v0.1.json`.
- Regression checks: `cvpr2027/tests/test_cadfem_metrics.py`.
- Sources: `sources.json` in this directory, with downloaded research snapshots under `sources/`.

Available: physical point-to-surface distances/F1, BREP/optional voxel IoU, edit improvement, feature-count PRF helper, executed-operation recall helper, BenchCAD 2 part-formula helper from supplied trusted measurements, weighted field L2/RMSE, scalar errors, small linear energy norm, force/moment balance, MAC, convergence diagnostics, conservative joint-gate handling and family aggregation.

Not yet automatic: extracting engineering features/topology/interfaces, protected-ROI preservation, cross-mesh registration/interpolation, advanced contact/fracture/transient adapters and trusted full-workflow verification. The profile leaves pass thresholds null until calibration. This specification does not certify the existing 54 tasks under the new metric, and does not relabel historical Astra failures.

## 10. Running diagnostic metrics

```sh
cvpr2027/tmp/cq-env/bin/python cvpr2027/scripts/cadfem_metrics.py geometry \
  --candidate /path/to/submission/part.step --reference /path/to/evaluator/reference.step \
  --pose fixed --samples 20000 --out /path/to/geometry-metrics.json

cvpr2027/tmp/cq-env/bin/python cvpr2027/scripts/cadfem_metrics.py fields \
  --candidate /path/to/evaluator/interpolated-candidate.npz \
  --reference /path/to/evaluator/common-grid-reference.npz \
  --field displacement --out /path/to/field-metrics.json

cvpr2027/tmp/cq-env/bin/python -m unittest discover \
  -s cvpr2027/tests -p test_cadfem_metrics.py -v
```

Common-grid NPZs contain `evaluation_points` (identical physical query points), `field_unit`, `coordinate_unit`, `field_basis` (same component convention), the selected field, and reference-owned positive `weights`. Native candidate NPZs are not trusted common-grid files. CLI results are diagnostics with `workflow_verified=null`; they never execute submitted code or issue a full pass.

## 11. Existing-run demonstration

`demo-existing-astra-geometry.json` evaluates the already-existing Astra B-FEMCAD-067 STEP against its reference at the configured 20,000 points. Exact solid IoU is 1.0, point-to-surface CD_L1, Hausdorff and HD95 are below 1e-12 mm, and F1 is 1.0. The first version of this demonstration (5,000 points, point-to-point) reported CD_L1 2.84 mm and F1 0.22 for the same exact match; that was sampling noise, corrected on 26 October 2026.

`demo-existing-astra-scorecard.json` combines this diagnostic with its existing published-temperature comparison. It deliberately leaves missing workflow/field/convergence reviews unverified. No new model inference or solver rerun was performed for this demonstration.
