# Adaptive CAD implementation validation

12 behavioral/integration tests passed. Both local MCTS and best-first synthetic task runs passed geometry, explicit constraints, caller-declared complete semantics, FEM, and independent final robustness checks. Both exported executable CAD and STEP files. The second task retrieved one successful trajectory from the first task.

The same full native CAD/FEM example also passed on server 10.71.9.40 (`server-native-verified`). A separate server development-example run (`server-grpo-smoke`) exercised the real frozen GRPO verifier and unchanged calibration: final confidence 0.901813, threshold 0.901613, PASS for geometry/constraints/semantics. That development task had no physical contract, so FEM/robustness were explicitly outside its required profile.

These are integration tests with scripted/replayed candidates, not a new Astra/BenchCAD accuracy experiment. Fresh Astra calls: 0. Additional API cost: $0. The live Astra HTTP adapter was tested with mocked responses, including usage accounting, failure handling and budget refusal before dispatch.

Server installation: `/home/trishita/svg-compute/adaptive-cad-20261007`. Use `scripts/server_run_adaptive_cad.sh` with task, output and memory arguments. Missing FEM dependencies were installed in an isolated bundle directory. The initial server setup failure is retained separately; its missing Gmsh shared library was corrected before the successful verification run.

See validation-summary.json, implementation-sha256.json, release-mcts/result.json, release-next-task/result.json and the server result directories for graph traces and evidence. Existing BenchCAD results remain unchanged.
