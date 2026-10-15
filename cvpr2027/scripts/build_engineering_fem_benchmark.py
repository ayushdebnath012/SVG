"""Crawl pinned engineering FEM sources; package two answer-separated pilot tracks.

No downloaded program is executed. Raw source assets remain git-ignored. Release
certification is deliberately distinct from source preparation and numerical checks.
"""
from __future__ import annotations
import argparse,hashlib,json,posixpath,re,shutil
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import requests

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/engineering-fem-v1'
CACHE=ROOT/'tmp/engineering-fem-crawl'
PACK=ROOT/'tmp/engineering-fem-v1'
SHA='06965026d6c73919ee02744192ec4b7526bb7e5c'
RAW=f'https://raw.githubusercontent.com/seamplex/feenox/{SHA}/'
PAGE='https://www.seamplex.com/feenox/examples/mechanical.html'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
def qoi(key,unit,value,kind,evidence,**extra):
    return dict(key=key,unit=unit,value=value,reference_kind=kind,evidence=evidence,**extra)

def seeds():
    quarter='First-quadrant elliptical annulus: outer (x/3250)^2+(y/2750)^2=1, inner (x/2000)^2+(y/1000)^2=1, straight edges on x=0 and y=0. Dimensions in mm. A=(0,1000), B=(0,2750), C=(3250,0), D=(2000,0).'
    common=dict(source_family='feenox',difficulty='uncalibrated',release_status='diagnostic-pilot',scored_release=False)
    return [
      common|dict(id='ENGFEM-LE1',title='Curved elliptical membrane under outer-edge traction',domain='linear_elasticity',formulation='2D plane stress',
       geometry=quarter+' Use a planar CAD face, not an invented 3D extrusion.',
       physics='E=210000 MPa, nu=0.3. On AB, ux=0; on CD, uy=0. Apply outward normal tensile traction 10 MPa to BC (outer ellipse). Inner ellipse is traction-free. Compute signed sigma_yy at D=(2000,0).',
       output_keys=['sigma_yy_D_MPa'],units={'sigma_yy_D_MPa':'MPa'},geometry_files=['nafems-le1.geo'],reference_files=['nafems-le1.fee','nafems-le1.yaml'],
       figures=['nafems-le1-figure.svg'],input_figures=['nafems-le1-figure.svg'],anchor='nafems-le1-elliptical-membrane-plane-stress-benchmark',
       qois=[qoi('sigma_yy_D_MPa','MPa',92.7,'published_benchmark','examples/nafems-le1.fee; examples/nafems-le1.yaml')],
       notes=['The original drawing omits the /1000 term in the inner y coordinate. The geometry code and explicit dimensions in task.md determine the ellipse.','Point stress requires a documented recovery method and mesh refinement.']),
      common|dict(id='ENGFEM-LE10',title='Thick curved plate under transverse pressure',domain='solid_mechanics',formulation='3D linear elasticity',
       geometry=quarter+' Extrude from z=-300 to z=300 mm. Preserve a midplane curve on the outer elliptical face.',
       physics='E=210000 MPa, nu=0.3. On y=0 face DCD\'C\', uy=0; on x=0 face ABA\'B\', ux=0. On outer elliptical face BCB\'C\', ux=uy=0. On its curve at z=0, uz=0. Apply inward normal pressure 1 MPa to the upper z=300 surface. Other surfaces are traction-free. Compute signed sigma_yy at D=(2000,0,300) mm.',
       output_keys=['sigma_yy_D_MPa'],units={'sigma_yy_D_MPa':'MPa'},geometry_files=['nafems-le10.geo','nafems-le10.step'],reference_files=['nafems-le10.fee','nafems-le10.yaml','nafems-le10-cad.geo'],
       figures=['nafems-le10-problem-input.svg','nafems-le10.png'],input_figures=[],anchor='nafems-le10-thick-plate-pressure-benchmark',
       qois=[qoi('sigma_yy_D_MPa','MPa',-5.38,'published_benchmark','mechanical.html LE10 expected result and examples/nafems-le10.yaml')],
       notes=['The source diagram includes the answer and solver recipe. It is evaluator-only. CAD-track geometry is completely specified in task.md.','Archived STEP and named geometry groups are supplied only in the analysis track.']),
      common|dict(id='ENGFEM-LE11',title='Thermal stress in a cylinder/taper/spherical shell',domain='thermoelasticity',formulation='3D quarter-turn linear thermoelasticity',
       geometry='Units m. In the r-z plane build three connected regions: (1) a spherical shell sector between inner/outer circular arcs of radii 1 and 1.4, both starting at z=0 and ending at z=sqrt(0.5), closed by horizontal segments at those elevations; (2) from its upper endpoints (r,z)=(sqrt(0.5),sqrt(0.5)) and (sqrt(1.4^2-0.5),sqrt(0.5)), extend inner wall vertically to z=sqrt(0.5)+0.69, and connect the outer endpoint linearly to (1,sqrt(0.5)+0.69); (3) extend both walls vertically a further 0.4 m. Rotate this cross-section about z through pi/2 into x>=0,y>=0. Keep shared interfaces.',
       physics='E=210e9 Pa; nu=0.3; thermal expansion alpha=2.3e-4 /degC; reference temperature 0 degC. Prescribed T(x,y,z)=sqrt(x*x+y*y)+z degC. On y=0, uy=0; on x=0, ux=0; on z=0, uz=0; on the upper annular face at z=sqrt(0.5)+1.09, uz=0. All other surfaces traction-free. Return signed sigma_zz at A=(1,0,0) m in MPa.',
       output_keys=['sigma_zz_A_MPa'],units={'sigma_zz_A_MPa':'MPa'},geometry_files=['nafems-le11.geo'],reference_files=['nafems-le11.fee','nafems-le11.yaml'],
       figures=['nafems-le11-problem.png','nafems-le11-mesh.png'],input_figures=['nafems-le11-mesh.png'],anchor='nafems-le11-solid-cylindertapersphere-temperature-benchmark',
       qois=[qoi('sigma_zz_A_MPa','MPa',-105.04,'published_solver_output','examples/nafems-le11.yaml terminal block',benchmark_magnitude_MPa=105)],
       notes=['Full source problem diagram contains the target stress and is held out. Geometry-only mesh figure is retained.','Reference is the published FeenoX output, not a newly computed solution.']),
      common|dict(id='ENGFEM-GNL5',title='Large-deformation imperfect cantilever buckling',domain='nonlinear_mechanics',formulation='3D quasistatic finite-strain Saint Venant-Kirchhoff',
       geometry='Rectangular beam x=[0,3.2], y=[-0.05,0.05], z=[-0.05,0.05] m. Left x=0 face clamped.',
       physics='E=2.1e11 Pa; nu=0. Geometrically nonlinear, source ldef=1 (Saint Venant-Kirchhoff). Proportional load lambda in [0,1]: total right-end Fx=-3.844e6*lambda N and Fy=-3.844e3*lambda N, uniformly distributed over the end face. Follow the quasistatic branch with initial increment 0.01; refine load increments around turning behavior. At tip center (3.2,0,0), return the most negative uy over the entire path. Save the full load-displacement curve separately.',
       output_keys=['minimum_tip_uy_m'],units={'minimum_tip_uy_m':'m'},geometry_files=['nafems-gnl-cantilever.geo'],reference_files=['nafems-gnl-cantilever.fee','nafems-gnl-cantilever.yaml'],
       figures=['nafems-gnl-cantilever-problem.svg','nafems-gnl-cantilever-mesh.png'],input_figures=['nafems-gnl-cantilever-problem.svg'],anchor='nafems-gnl5-large-deformation-beam',
       qois=[qoi('minimum_tip_uy_m','m',-2.58,'published_benchmark','examples/nafems-gnl-cantilever.yaml reference table',source_absolute_tolerance=0.02)],
       notes=['Source implementation is explicitly work in progress. Independent formulation/branch validation remains required.','Two final-displacement rows have duplicate labels; neither ambiguous output is used.']),
      common|dict(id='ENGFEM-COUPLED',title='Heat conduction coupled to temperature-dependent stiffness',domain='coupled_thermal_structural',formulation='3D sequential steady conduction and linear elasticity',
       geometry='Source non-dimensional coordinates. Solid box x=[0,20], y=[-5,5], z=[-5,5]. O=(0,0,0), A=(20,0,0), B=(0,5,0), C=(0,0,5). Embed these points in their respective surfaces.',
       physics='Steady thermal conductivity k=1. Inward heat flux is +2 on x=0, -2 on x=20, +3 on y=-5, -3 on y=5, +4 on z=-5, -4 on z=5. T(A)=0 removes the thermal nullspace. Then solve linear elasticity with E(T)=1000/(800-T), nu=0.3, alpha=0. Prescribe u=v=w=0 at O; u=w=0 at B; u=0 at C. Apply outward normal tensile traction 1 to both x-end faces. Other surfaces traction-free. Use the solved thermal field, not an assumed temperature. Sample temperature and displacement at the seven query points in queries.json.',
       output_keys=[f'{f}_q{i}' for i in range(7) for f in ['T','u','v','w']],units={f'{f}_q{i}':'source_nondimensional' for i in range(7) for f in ['T','u','v','w']},
       geometry_files=['parallelepiped.geo'],reference_files=['parallelepiped-thermal.fee','parallelepiped-mechanical.fee','parallelepiped-mechanical.yaml'],
       figures=['parallelepiped.svg'],input_figures=['parallelepiped.svg'],anchor='parallelepiped-whose-youngs-modulus-is-a-function-of-the-temperature',
       query_points=[[0,0,0],[20,0,0],[10,0,0],[10,2,2],[5,-2,-2],[15,3,-3],[20,5,5]],qois=[],
       reference_formula='parallelepiped_analytical',notes=['Reference arrays are evaluations of the published analytical expressions, not a new FEM solve.','Inputs specify inward heat-flux sign explicitly.']),
      common|dict(id='ENGFEM-MODAL',title='Degenerate bending modes of a copper cantilever wire',domain='modal_analysis',formulation='3D linear elastic eigenproblem',
       geometry='Circular solid cylinder with diameter 0.001948 m, z=[0,0.1515] m, centered on the z-axis. Clamp its lower z=0 end.',
       physics='E=132.4e9 Pa, nu=0, total mass 0.00401 kg, uniform density rho=mass/(pi*(diameter/2)^2*length). All lateral and free-end surfaces traction-free. Compute at least ten elastic vibration eigenmodes. Five distinct bending frequencies each occur as a near-degenerate pair; report the mean frequency of each consecutive pair among the ten lowest positive modes in Hz, and save mode shapes. Do not substitute an Euler-Bernoulli formula for a FEM solve.',
       output_keys=[f'bending_frequency_{i}_Hz' for i in range(1,6)],units={f'bending_frequency_{i}_Hz':'Hz' for i in range(1,6)},
       geometry_files=['wire-hex.geo'],reference_files=['wire.fee','wire.yaml'],figures=[],input_figures=[],source_page='https://www.seamplex.com/feenox/examples/modal.html',anchor='five-natural-modes-of-a-cantilevered-wire',
       qois=[qoi(f'bending_frequency_{i}_Hz','Hz',v,'published_solver_output','examples/wire.yaml copper hex FEM table',rounded=True) for i,v in enumerate([45.84,287.1,803.4,1573,2596],1)],
       notes=['Values are the source copper-hex FEM frequencies, not experimental measurements or Euler-Bernoulli predictions.','Mode ordering and pairing require validation for a candidate discretization.']),
      common|dict(id='ENGFEM-BIMATERIAL',title='Steel/aluminum stepped assembly displacement comparison',domain='multimaterial_elasticity',formulation='3D linear elasticity, two material cases',
       geometry='Source length coordinates, interpreted consistently as mm for an N-MPa system. Connected boxes: pink x=[0,5.5], y=[0,1], z=[0,1]; blue-left x=[5,10], y=[1,2], z=[0,1]; blue-right x=[10,15], y=[1,2], z=[0,1]. Perfectly bonded interfaces; preserve material regions. Full fixity on x=0 pink face. Pin support is the vertical edge x=10,y=1,z=[0,1], constraining uy only.',
       physics='Two cases: (1) all steel E=210000 MPa, nu=0.3; (2) pink aluminum E=69000 MPa, nu=0.25 and both blue boxes steel. Apply total Fy=-2000 N uniformly to blue-left face x=5,y=[1,2],z=[0,1], and total Fy=-1000 N uniformly to blue-right face x=15,y=[1,2],z=[0,1]. All remaining surfaces traction-free. Return maximum displacement magnitude in source length units for each case. Explain the comparison using the computed fields.',
       output_keys=['max_displacement_all_steel','max_displacement_aluminum_pink'],units={'max_displacement_all_steel':'source_length','max_displacement_aluminum_pink':'source_length'},
       geometry_files=['steel-alum.geo'],reference_files=['steel-alum.fee','steel-alum.yaml'],figures=['steel-alum.svg'],input_figures=['steel-alum.svg'],anchor='steelaluminum-paradox',
       qois=[qoi('max_displacement_all_steel','source_length',3.9,'published_solver_output','examples/steel-alum.yaml terminal block',rounding_resolution=0.1),qoi('max_displacement_aluminum_pink','source_length',2.6,'published_solver_output','examples/steel-alum.yaml terminal block',rounding_resolution=0.1)],
       notes=['Source prints only one decimal place. Targets are rounded source outputs; precision and mesh effects limit comparisons.','Pin/load entity locations were checked against the source geometry physical groups.'])
    ]

def fetch_asset(path,nodes):
    dest=CACHE/'repo'/path;dest.parent.mkdir(parents=True,exist_ok=True)
    # Resolve repository symlinks without creating filesystem symlinks.
    target=path;resolved=[]
    while nodes.get(target,{}).get('mode')=='120000':
        if target in resolved:raise ValueError('repository symlink cycle')
        resolved.append(target)
        r=requests.get(RAW+target,timeout=45);r.raise_for_status()
        target=posixpath.normpath(posixpath.join(posixpath.dirname(target),r.text.strip()))
        if target.startswith('../') or target not in nodes:raise ValueError('invalid repository symlink')
    if not dest.exists() or resolved:
        r=requests.get(RAW+target,timeout=60);r.raise_for_status();dest.write_bytes(r.content)
    return dict(path=path,source_url=RAW+target,repository_commit=SHA,resolved_symlinks=resolved,local=str(dest.relative_to(ROOT)),sha256=digest(dest),bytes=dest.stat().st_size)

def crawl():
    CACHE.mkdir(parents=True,exist_ok=True)
    tree_path=CACHE/'feenox-pinned-tree.json'
    if not tree_path.exists():
        r=requests.get(f'https://api.github.com/repos/seamplex/feenox/git/trees/{SHA}?recursive=1',timeout=45);r.raise_for_status();save(tree_path,r.json())
    tree=json.loads(tree_path.read_text());assert tree['sha']==SHA
    nodes={x['path']:x for x in tree['tree']}
    paths={'COPYING'}
    for case in seeds():
        paths.update('examples/'+f for group in ['geometry_files','reference_files','figures'] for f in case[group])
    with ThreadPoolExecutor(max_workers=4) as pool: assets=list(pool.map(lambda p:fetch_asset(p,nodes),sorted(paths)))
    for name in ['mechanical','thermal','modal']:
        url=f'https://www.seamplex.com/feenox/examples/{name}.html';dest=CACHE/f'{name}.html'
        if not dest.exists():
            r=requests.get(url,timeout=45);r.raise_for_status();dest.write_bytes(r.content)
        assets.append(dict(path=name+'.html',source_url=url,local=str(dest.relative_to(ROOT)),sha256=digest(dest),bytes=dest.stat().st_size))
    save(DATA/'source-assets.json',dict(fetched_utc=datetime.now(timezone.utc).isoformat(),repository_commit=SHA,assets=assets))
    print('Pinned crawl:',len(assets),'assets',flush=True)

def analytic_reference(case):
    out=[];nu=.3;A=.002;B=.003;C=.004;D=.76;h=10
    for i,(x,y,z) in enumerate(case['query_points']):
        values={'T':40-2*x-3*y-4*z,
         'u':A/2*(x*x+nu*(y*y+z*z))+B*x*y+C*x*z+D*x-nu*A*h/4*(y+z),
         'v':-nu*(A*x*y+B/2*(y*y-z*z+x*x/nu)+C*y*z+D*y-A*h/4*x-C*h/4*z),
         'w':-nu*(A*x*z+B*y*z+C/2*(z*z-y*y+x*x/nu)+D*z+C*h/4*y-A*h/4*x)}
        out += [qoi(f'{f}_q{i}','source_nondimensional',value,'published_analytical_expression',f'examples/parallelepiped-{"thermal" if f=="T" else "mechanical"}.fee',point=[x,y,z]) for f,value in values.items()]
    return out

def package():
    assets=json.loads((DATA/'source-assets.json').read_text())['assets'];index={a['path']:a for a in assets};cases=seeds();records=[]
    for case in cases:
        if case.get('reference_formula'):case['qois']=analytic_reference(case)
        cid=case['id']; source=case.get('source_page',PAGE)+'#'+case['anchor']
        reference=PACK/'evaluator-only'/cid;reference.mkdir(parents=True,exist_ok=True)
        for f in set(case['geometry_files']+case['reference_files']+case['figures']):shutil.copy2(CACHE/'repo/examples'/f,reference/f)
        contract={**case,'source_url':source,'comparison':'signed absolute/relative error; no certified pass/fail except source tolerances reported diagnostically','diagnostic_relative_bands':[0.01,0.02,0.05,0.10],'release_blockers':['Independent baseline replay and discretization/recovery validation pending.','Trusted geometry/physics and artifact-chain evaluator not yet certified.'],
                  'reference_access':'evaluator only','joint_pass':None,'geometric_criteria':None,'validated_acceptance_tolerances':None}
        save(reference/'contract.json',contract)
        for track in ['cad_fem','analysis_fem']:
            folder=PACK/'candidate-inputs'/track/cid;folder.mkdir(parents=True,exist_ok=True)
            for f in case['input_figures']:shutil.copy2(CACHE/'repo/examples'/f,folder/f)
            if track=='analysis_fem':
                for f in case['geometry_files']:shutil.copy2(CACHE/'repo/examples'/f,folder/f)
            if case.get('query_points'):save(folder/'queries.json',dict(points=case['query_points'],ordering='zero-based, matching q-index in output keys'))
            instructions=('Construct the CAD from the supplied dimensions and permitted figures. Export part.step and mesh YOUR geometry. Do not import any unavailable reference geometry.' if track=='cad_fem' else 'Use the supplied geometry and its named physical groups. Generate/refine the FEM mesh; do not replace the physical part with a beam, shell, or closed-form surrogate unless the formulation explicitly requires it.')
            text=f"# {case['title']}\n\nTrack: {track}\nFormulation: {case['formulation']}\n\n## Geometry\n{case['geometry']}\n\n## Engineering analysis\n{case['physics']}\n\n## Submission\n{instructions}\nAuthor main.py, using the available solver libraries, so running it constructs/meshes/solves the problem and writes results.json. Save mesh.msh, fields (VTK/XDMF/NPZ), solver.log, and mesh-refinement data. For nonlinear tasks also save the load-displacement history; for modes save mode shapes. Provide a concise explanation tied to computed quantities.\n\nresults.json must contain a qois object with keys and units: {json.dumps(case['units'],sort_keys=True)}. Include solver/version, formulation, material/load/constraint declarations, convergence status, mesh counts, and a refinement list. Do not fill numerical answers from memory without computing them. Explain any inability to produce an FEM result.\n\n## Source-input cautions\n"+'\n'.join('- '+n for n in case['notes'] if not any(k in n for k in ['Reference is','Targets are','reference arrays','Reference arrays','Source prints','Source implementation','published FeenoX','Source diagram','Full source']))+'\n'
            (folder/'task.md').write_text(text)
            # Do not place target values, reference URLs, solver recipes or contracts in candidate inventories.
            files=[dict(path=p.name,sha256=digest(p),bytes=p.stat().st_size) for p in sorted(folder.iterdir()) if p.is_file() and p.name!='task.json']
            task=dict(id=cid,track=track,title=case['title'],domain=case['domain'],formulation=case['formulation'],status='diagnostic-pilot',scored_release=False,output_units=case['units'],files=files,entrypoint='main.py',required_outputs=['results.json','mesh.msh','solver.log']+(['part.step'] if track=='cad_fem' else []))
            save(folder/'task.json',task)
            records.append(dict(id=cid,track=track,domain=case['domain'],title=case['title'],source_url=source,candidate_manifest=str((folder/'task.json').relative_to(ROOT)),private_contract=str((reference/'contract.json').relative_to(ROOT)),numerical_targets=len(case['qois']),status='diagnostic-pilot',scored_release=False))
    expansion=[]
    legacy=ROOT/'data/femcad-hard-v1'
    for row in map(json.loads,(legacy/'advanced-tasks.jsonl').read_text().splitlines()):
        expansion.append(dict(id=row['id'],title=row['title'],domain=row.get('category'),source=row.get('source_url',row.get('source')),status='blocked-scoring',tracks=['cad_fem','analysis_fem'],blockers=['Per-output numerical reference contract missing.','Input completeness and compatible solver runtime not certified.'],existing_joint_manifest=row.get('joint_benchmark')))
    for row in map(json.loads,(legacy/'tasks.jsonl').read_text().splitlines()):
        expansion.append(dict(id=row['id'],title=row['title'],domain=row['category'],source=row['source'],status='legacy-reference-review',tracks=['cad_fem','analysis_fem'],reference_status=row['reference']['status'],blockers=['Legacy physics/input and geometry scoring contracts need fresh review.']))
    save(DATA/'catalog.json',dict(version=1,unique_open_cases=len(cases),prepared_track_tasks=len(records),certified_scored_tasks=0,records=records,expansion_cases=expansion,
      related_sources=[dict(name='SimJEB',role='structural design and supplied-CAD sub-benchmark',status='existing separate suite'),dict(name='SFEM',role='archived stochastic stress-field surrogate prediction',status='not deterministic FEM solving; sampled load facets/seeds missing')]))
    save(DATA/'curation.json',cases)
    print('Prepared',len(cases),'source cases;',len(records),'track packages;',len(expansion),'expansion records',flush=True)

def validate():
    catalog=json.loads((DATA/'catalog.json').read_text());inventory=json.loads((DATA/'source-assets.json').read_text())['assets'];checks=0
    for a in inventory:assert digest(ROOT/a['local'])==a['sha256'];checks+=1
    for r in catalog['records']:
        taskpath=ROOT/r['candidate_manifest'];task=json.loads(taskpath.read_text());folder=taskpath.parent
        assert task['track']==r['track'] and task['scored_release'] is False
        for f in task['files']:assert digest(folder/f['path'])==f['sha256'];checks+=1
        assert not list(folder.glob('*.fee')) and not list(folder.glob('*contract*'))
        if task['track']=='cad_fem':assert not list(folder.glob('*.geo')) and not list(folder.glob('*.step'))
        assert 'qois' not in task and 'source_url' not in task
        contract=json.loads((ROOT/r['private_contract']).read_text());assert contract['qois']
        assert set(q['key'] for q in contract['qois'])==set(task['output_units'])
        for q in contract['qois']:assert q['unit']==task['output_units'][q['key']]
    report=dict(status='passed-structural-validation',source_cases=catalog['unique_open_cases'],track_packages=len(catalog['records']),hash_checks=checks,certified_scored_tasks=0,limits=['This is provenance/package validation, not a numerical baseline or a complete semantic leakage audit.','Original images can contain source drawing typos. Reviewed exclusions and cautions are recorded.'])
    save(DATA/'validation.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['crawl','package','validate','all']);a=p.parse_args()
    if a.action in ['crawl','all']:crawl()
    if a.action in ['package','all']:package()
    if a.action in ['validate','all']:validate()
