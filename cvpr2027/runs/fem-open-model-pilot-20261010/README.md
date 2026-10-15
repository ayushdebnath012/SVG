# Open-weight FEM generation pilot

Two existing source studies were provided with the full crawled tutorial and original reference image. Candidate code was not hand-repaired.

Kimi K3 and Inkling could not be evaluated: gateway requests returned HTTP 429; Hugging Face requests returned HTTP 402 (no remaining credits). A diagnostic Kimi request confirmed the gateway purchase lock. DeepSeek V4.1 Flash returned actual model outputs through the configured gateway.

Direct-provider follow-up: Moonshot authenticated and listed `kimi-k2.6` and `kimi-k2.7-code`; both models rejected both source-study requests with HTTP 429 and an explicit insufficient-balance message. The earlier direct K3 probe was also rejected for insufficient balance. Inkling rejected both full source-study requests with HTTP 402. Minimal probes on both documented Tinker OpenAI-compatible and Anthropic-compatible routes confirmed an explicit billing-status block. These are access failures before generation, not model performance failures. Keys were supplied through standard input and were not persisted. See `moonshot-direct/available-models/low-reasoning/generation-summary.json` and `tinker-direct/access-check.json`.

| Published study | Unmodified geometry execution | Source/FEM fidelity |
|---|---|---|
| Rubber boot, FEMCAD-ADV-001 | STEP and mesh generated; 5,105 nodes and 14,546 volume elements | Incorrect 90-degree sector versus source half-domain; approximate profile. FEM code is an incomplete FEniCS template, not a solved contact model. |
| Hyperelastic seal, FEMCAD-ADV-011 | Failed at line 12: invalid numeric Gmsh option Geometry.OCCTargetUnit | No STEP/mesh. Candidate admits estimated cavity dimensions; FEM code contains placeholders and linear-elastic substitution. |

These rows use the thinking-disabled configuration with a 16,000-token cap. Default-thinking attempts used the entire 8,000-token allowance without an answer. A second 24,000-token, low-reasoning attempt also exhausted the allowance for the seal; its boot code failed geometry construction. Token-limit outcomes are inconclusive.

Neither study was reproduced end to end in this pilot. No FEM solver execution or numerical agreement was established; FEM templates were inspected, and they omit essential source physics. This does not prove either task is impossible for these models or generalize to the other 48 studies.

The successful boot mesh is a counterexample to a blanket claim that open-weight models cannot generate geometry for these examples: it produces executable approximate geometry, but does not satisfy source reproduction requirements.

Provider-reported total inference cost: $0.11550.

Evidence: `results.json`, `protocol.json`, per-attempt prompts, raw model responses, generated code, geometry execution logs, and the boot geometry preview. The dataset PDF was not modified.
