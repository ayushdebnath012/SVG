# CADFEM training v1

128 original publisher training cases and 16 original validation cases from AgentFEM (CC BY 4.0). The 32 publisher test cases and benchmark cases are excluded. Original STEP, mesh, fields and summaries are preserved; archive hashes and displacement metrics are checked.

The MLX chat data trains numerical surrogate prediction from source geometry parameters, material and physical load. It does not train a complete CAD/FEM agent. All target scalars come directly from original summaries at their recorded 1,000 or 10,000 N load; no load-normalized label is substituted.

Original STEP headers have a scale inconsistency, documented in each input. Files remain unchanged; parameters and nodal coordinates use metres. Targets are the source discretized results, not independently converged engineering truth. Validation is within the same parametric family. Keep CADFEM-Bench v1.7 for evaluation.

Attribution: Haoming Luo, AgentFEM-Bracket-Elasticity (2026), https://huggingface.co/datasets/HaomingLuo/AgentFEM-Bracket-Elasticity. Original license/notices are in source/.
