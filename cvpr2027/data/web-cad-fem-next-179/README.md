# Additional original web CAD + FEM pairs

179 newly collected original CAD/result pairs from two sources. None generated locally. This is a candidate collection, not 179 distinct complex engineering families or certified scores.

- AgentFEM: 176 native STEP solids, original Gmsh meshes and finite displacement/stress NPZ fields. 128 train / 16 validation / 32 test. One parametric bracket family. Publisher SHA-256 hashes and archive CRC checked; all solids valid; physical load, fixed-face values and source summary values audited. STEP declares mm but its coordinates match FEM metres numerically: source factor-1000 scale inconsistency, retained unchanged. Nominal 9 mm mesh, not converged industrial qualification.
- CADWorld: 3 original precondition and solved native FCStd projects plus result CSVs, task JSON/evaluators and two task screenshots. A multi-feature part and curved chain-link are geometry candidates; the third is a basic stress specimen. 102,433 CSV rows total, finite. Native arrays and CSV extrema agree after displacement mm/m and stress MPa/Pa conversion. Publisher 5% evaluator tolerance reproduced by reading, not running solver. Very high elastic stress/deformation values require physical validity review. No verified contact between separate chain links.

## Files and provenance

`../web-agentfem-brackets/catalog.json` indexes every original extracted pair, physical inputs, units and reference values. Publisher ZIPs are retained too. Source model errors (`evaluation.json`) are separate from FEM ground truth.
`../web-cadworld-fem/catalog.json` indexes CAD, solved FEM, CSVs, materials, loads and boundary-face references. Original publisher evaluators are retained without execution.
Download manifests pin source revision and SHA-256 for each downloaded asset. Validation reports record completed audits. Collection ZIP includes these sibling folders with their original structure.

## Benchmark status

Zero new certified admissions; zero solver runs; zero frontier model calls. Supplied-CAD track only gains candidates. No new original dimensioned drawings verified; PDF CAD inspection renders and publisher task screenshots do not replace dimensioned drawings. Proposed displacement vector relative L2, nodal stress error, and seat/scalar relative errors require consistent coordinates, units and independent replay before certification. Keep drawing and CAD input tracks separately reported. Do not use implausible linear-elastic outputs as validated strength/failure labels.

## Attribution

AgentFEM: https://huggingface.co/datasets/HaomingLuo/AgentFEM-Bracket-Elasticity ; revision 8b020d1f3ae22e1583dfa3f2e466627d38ebeab3 ; Haoming Luo (2026), CC BY 4.0 data, Apache-2.0 source code.
CADWorld: https://github.com/Zdong104/CADWORLD ; revision e5d0ebab8bd28da6e98c68c61db05747d1647f7b ; https://huggingface.co/datasets/Zihan1004/CADWORLD publisher metadata declares Apache-2.0. Original embedded material-card licenses retained.

Earlier collections remain unchanged and linked in the main selected-dataset manifest.
