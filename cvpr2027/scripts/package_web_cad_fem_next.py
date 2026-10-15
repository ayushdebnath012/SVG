from pathlib import Path
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[1];D=R/'data/web-cad-fem-next-179';D.mkdir(exist_ok=True)
a=json.loads((R/'data/web-agentfem-brackets/catalog.json').read_text());c=json.loads((R/'data/web-cadworld-fem/catalog.json').read_text())
summary=dict(collection='Additional published CAD/FEM source pairs',date='2026-10-12',cad_result_pairs=179,source_collections=2,agentfem_parametric_bracket_family_cases=176,cadworld_complex_geometry_candidates=2,cadworld_basic_specimens=1,certified_benchmark_admissions=0,original_dimensioned_drawing_cases=0,no_local_geometry_generation=True,solver_runs=0,model_calls=0,sources=[dict(catalog='../web-agentfem-brackets/catalog.json',source=a['source'],revision=a['revision'],count=176,status='Held: STEP scale metadata; mesh convergence; independent replay'),dict(catalog='../web-cadworld-fem/catalog.json',source=c['source'],revision=c['revision'],count=3,status='Held: physical validity; independent replay; one basic specimen')],earlier_variety_catalog='../web-cad-fem-variety/catalog.json',earlier_169_catalog='../web-cad-fem-additions/catalog.json')
(D/'catalog.json').write_text(json.dumps(summary,indent=2))
(D/'README.md').write_text('''# Additional original web CAD + FEM pairs

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
''')
(D/'search-log.json').write_text(json.dumps(dict(date='2026-10-12',retained_sources=[a['source'],c['source']],held_leads=[dict(source='https://pages.nist.gov/CAD-PMI-Testing/',status='Downloaded original NIST-PMI-STEP-Files ZIP (49 members), no AP209 result samples found inside. Web AP209 viewer is not proof of paired downloadable native BREP and numerical reference; not counted.'),dict(source='https://data.uni-hannover.de/dataset/cad-data-and-simulation-results-for-a-study-on-thermal-management-in-multi-material-microreactors',status='ANSYS Fluent CFD results: not classified as FEM.'),dict(source='https://research.aalto.fi/en/datasets/research-data-supporting-fracture-toughness-of-semi-regular-latti/',status='STL geometry and simulation spreadsheet leads; no native BREP verified, not counted.')]),indent=2))
selected=R/'data/web-complex-fem/selected-dataset.json';s=json.loads(selected.read_text());s['additional_web_cad_fem_sources']=dict(catalog='cvpr2027/data/web-cad-fem-next-179/catalog.json',pdf='cvpr2027/output/pdf/web-cad-fem-new-sources-179.pdf',package='cvpr2027/output/datasets/web-cad-fem-new-sources-179.zip',cad_result_pairs=179,source_collections=2,bracket_variants=176,cadworld_complex_geometry_candidates=2,cadworld_basic_specimens=1,certified_benchmark_admissions=0,status='Downloaded and audited; source unit and physical-validity blockers remain explicit. No locally generated CAD, FEM or model trials.');selected.write_text(json.dumps(s,indent=2)+'\n')
files=[]
for folder in [D,R/'data/web-agentfem-brackets',R/'data/web-cadworld-fem']:
 for p in sorted(folder.rglob('*')):
  if p.is_file(): files.append(p)
assets=[dict(path=str(p.relative_to(R/'data')),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
(D/'package-manifest.json').write_text(json.dumps(dict(assets=assets),indent=2));files.append(D/'package-manifest.json')
zipout=R/'output/datasets/web-cad-fem-new-sources-179.zip'
with zipfile.ZipFile(zipout,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,str(p.relative_to(R/'data')))
 z.write(R/'output/pdf/web-cad-fem-new-sources-179.pdf','web-cad-fem-new-sources-179.pdf')
 for n in ['collect_agentfem_web_pairs.py','audit_cadworld_web_fem.py','report_web_cad_fem_new_sources.py','package_web_cad_fem_next.py']:z.write(R/'scripts'/n,'audit-scripts/'+n)
with zipfile.ZipFile(zipout) as z:assert len(z.namelist())==len(set(z.namelist()));assert z.testzip() is None
print('Package CRC passed',zipout,zipout.stat().st_size,'bytes',len(files),'data files')
