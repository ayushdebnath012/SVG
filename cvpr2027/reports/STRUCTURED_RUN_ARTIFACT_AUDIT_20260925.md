# Structured EngSVG run artifact audit

Artifact: `engsvg-structured-run-artifacts.zip`  
SHA-256: `cd85b205169f3707f5988155db6838d298ec1fa3cf03738468fab8dadf1f46af`

## Archive integrity

The ZIP has 23 members, no CRC failure and 20 payload files covered by `sha256-manifest.json`. Every recorded digest matches. The adapter is a readable PEFT LoRA safetensors file with 224 float32 tensors. Its base model is `Qwen/Qwen2.5-Coder-1.5B-Instruct`.

## Saved results

The saved prediction booleans exactly reconcile with both summary files.

| Evaluation | Base | Trained |
|---|---:|---:|
| Matched create/edit/clarify | 24/36 | 36/36 |
| Frozen hard single-step | 7/22 | 6/22 |
| Frozen hard rollout steps | 1/9 | 3/9 |
| Complete hard trajectories | 0/3 | 1/3 |

The hard benchmark is the useful result. Training solved the narrow matched set but slightly reduced total hard single-step accuracy. It improved clarification and one complete rollout while regressing hard create and edit cases.

## Dataset scope

The bundled data has 800 rows: 600 train, 100 validation and 100 test, with no source-group overlap. It contains zero SVG prompts and zero SVG targets. This archive therefore proves a short JSON action/parameter experiment, not direct text-to-SVG or SVG-to-SVG learning.

The exact training source snapshot is absent. `summary.json` records source digest `b1dd2843...`, while the current local `structured_engsvg.py` is `e18d722a...`. The saved outputs are internally consistent, but the exact historical run cannot be independently rerun from this ZIP alone.

## Separate SVG patch claim

The parametric patch/FEM claim belongs to repository commit `5863d77`, not this ZIP. Independent reproduction on the six-panel Pratt example confirms:

| Change | Patch operations | Patched tree equals target | Peak stress (MPa) |
|---|---:|---:|---:|
| Section depth 20 to 40 mm | 1 | yes | 42.1875 |
| Modulus 200,000 to 70,000 MPa | 1 | yes | 84.3750 |
| Per-node load 15,000 to 30,000 N | 1 | yes | 168.7500 |
| Height 2,000 to 2,600 mm | 5 | yes | 64.903846 |

The six-to-eight-panel patch does not equal the target, recovers 16 nodes but only 26 members and gives a singular stiffness matrix. Regeneration remains necessary for topology changes.

Commit `5863d77` initially handled `set_text` only during in-memory derivation/application. The normal JSON parser rejected its `text` field and the policy validator rejected the operation. The local working tree now completes that contract: `set_text` is a version-2 operation, JSON round-trip and validation work, only text-like SVG nodes are allowed, the prompt describes the operation, and regression tests pass. The namespace serialization fix also passes after importing `svgpathtools`.
