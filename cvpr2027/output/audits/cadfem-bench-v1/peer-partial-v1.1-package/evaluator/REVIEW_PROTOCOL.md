# Trusted workflow review

The numeric scorer never runs candidate code. A correct number and plausible files are insufficient for an end-to-end pass. Use an evaluator-controlled, isolated runtime to inspect/run candidate code if authorized; keep reference data and review files inaccessible to the candidate. No automatic execution sandbox or FEM runner is provided in this pilot.

Create an unapproved template outside the candidate submissions directory:

```sh
python evaluator/prepare_review.py --tasks candidate/tasks.jsonl --task-id A-VALVE-transient --submissions runs/model --run-id trial-001 --out reviews/valve.jsonl
```

The trusted reviewer must verify all five conditions and supply a substantive evidence note for each. Record reviewer identity, exact task hash, run ID and all artifact hashes. Keep the template's hashes only if these are exactly the files inspected/executed. Each review line applies to one task; concatenate reviewed records into an evaluator-owned JSONL file. Never accept candidate-authored approval records.

1. `execution_verified`: execute or inspect a trusted execution trace for the submitted main.py in isolation. Confirm the recorded solver, environment, inputs, exit status and field outputs belong to this run. A candidate log alone is insufficient.
2. `geometry_verified`: inspect valid solid geometry, dimensions, holes and interfaces against the supplied CAD or drawing/specification. Check units and coordinate frame. For rigging reconstruction, also satisfy the automated source-frame shape-overlap check. An overlap threshold alone does not prove all features correct.
3. `setup_verified`: inspect materials, physics, load magnitudes/directions/distributions, constraints, connections, element formulation and sampling definitions. Identify and resolve ambiguous assumptions; mark false if the source does not support an unambiguous setup.
4. `field_outputs_verified`: independently extract each requested output from the submitted field/mesh using the recorded IDs, units, masks, times and stress convention. Confirm it agrees with results.json and comes from the submitted run. Modal vectors have arbitrary normalization; missing values must remain masked.
5. `convergence_reviewed`: inspect the actual distinct mesh refinements and their quantity changes, or reproduce an explicitly specified publisher mesh protocol. Explain any source mesh limitations. Set false if numerical uncertainty prevents the chosen tolerance from being justified.

A review is an explicit trusted attestation, not a cryptographic execution proof. The scorer rejects missing/false decisions, missing evidence notes, task/run mismatches and any changed artifact. The path outside submissions enforces separation only; the operator remains responsible for authenticating reviewer provenance and controlling access.

`numerical_passed` means all requested scalars match the reference tolerances. `workflow_verified` means artifacts pass the mechanical gates and a matching trusted review approves all five conditions. `passed` requires both. Neither field independently certifies real-world engineering safety or validates the source model. The pilot has zero independently reproduced reference tasks.
