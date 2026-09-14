"""Working bridge from the pinned FEM-Bench bar solver to solver-linked SVG.

Reuses upstream FEM code unchanged; adds generated cases, numerical checks,
SVG output and an actual solve after a load edit. This is an integration anchor,
not a reproduction of the full FEM-Bench model leaderboard or a novel benchmark.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import numpy as np


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def draw(record):
    x = np.array(record['x_m']); u = np.array(record['displacement_m']) * 1000
    # Fixed plot scale across original and edited loads, so a stale shape is visible.
    upper = record['plot_max_mm']; points = ' '.join(f'{90+720*t/x[-1]:.6f},{390-260*v/upper:.6f}' for t,v in zip(x,u))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 520" data-solution-id="{record['solution_id']}">
<rect width="900" height="520" fill="white"/>
<g font-family="sans-serif" fill="#17212b">
<text x="50" y="42" font-size="24">FEM-Bench reference: axial elastic bar</text>
<text x="50" y="74" font-size="16">F = {record['force_N']:.4g} N; E = {record['E_Pa']/1e9:.4g} GPa; A = {record['area_m2']*1e6:.4g} mm²</text>
<path d="M90 125V390H810" fill="none" stroke="#64748b"/>
<polyline id="displacement" points="{points}" fill="none" stroke="#2563eb" stroke-width="3" data-quantity="axial displacement" data-unit="mm"/>
<text x="400" y="430" font-size="17">Position: 0 to {x[-1]:.4g} m</text>
<text x="50" y="115" font-size="16">Displacement: 0 to {upper:.4g} mm</text>
<text id="tip" x="50" y="468" font-size="17" data-value-m="{record['tip_m']:.17g}">Tip displacement = {record['tip_m']*1000:.6g} mm</text>
<text x="50" y="500" font-size="13">Computed with the upstream FEM-Bench linear bar solver; schematic plot, classroom anchor.</text>
</g></svg>'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--output', type=Path, required=True)
    p.add_argument('--upstream',type=Path, default=Path(__file__).resolve().parents[1]/'vendor/FEM-bench')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    path=a.upstream/'tasks/FEM_1D_linear_elastic_CC0_H0_T0.py'
    spec=importlib.util.spec_from_file_location('upstream_bar',path)
    upstream=importlib.util.module_from_spec(spec);spec.loader.exec_module(upstream)
    solver=upstream.FEM_1D_linear_elastic_CC0_H0_T0
    upstream.test_no_load_self_contained(solver)
    upstream.test_analytical_solution(solver)
    provenance=a.upstream/'UPSTREAM.json'
    commit=json.loads(provenance.read_text())['commit'] if provenance.exists() else subprocess.check_output(['git','-C',str(a.upstream),'rev-parse','HEAD'],text=True).strip()
    rng=np.random.default_rng(20270913);records=[];pairs=[]
    for case in range(12):
        length=float(rng.uniform(.5,2));E=float(rng.uniform(50,210)*1e9)
        area=float(rng.uniform(80,400)*1e-6);force=float(rng.uniform(300,1800))
        upper=1.8*force*length/(E*area)*1000
        for factor in (1.,1.5):
            F=force*factor
            problem={'length_m':length,'E_Pa':E,'area_m2':area,'force_N':F,'elements':24,
                     'left_displacement_m':0.,'distributed_load_N_per_m':0.}
            result=solver(0.,length,24,[{'coord_min':0.,'coord_max':length,'E':E,'A':area}],
                          lambda x:0.,[{'x_location':0.,'u_prescribed':0.}],
                          [{'x_location':length,'load_mag':F}])
            exact=F*result['node_coords']/(E*area)
            error=float(np.max(np.abs(result['displacements']-exact)))
            balance=abs(float(result['reactions'].sum())+F)/F
            assert error<1e-10 and balance<1e-9
            record={**problem,'case_id':case,'load_factor':factor,'upstream_commit':commit,
                    'x_m':result['node_coords'].tolist(),'displacement_m':result['displacements'].tolist(),
                    'tip_m':float(result['displacements'][-1]),'reactions_N':result['reactions'].tolist(),
                    'analytic_max_error_m':error,'force_balance_relative':balance,'plot_max_mm':upper}
            record['solution_id']=digest({'problem':problem,'commit':commit,'displacements':record['displacement_m']})
            name=f'case-{case:02d}-load-{factor:g}'
            (a.output/f'{name}.json').write_text(json.dumps(record,indent=2)+'\n')
            (a.output/f'{name}.svg').write_text(draw(record));records.append(record)
        old,new=records[-2:]
        assert old['solution_id']!=new['solution_id']
        pairs.append({'case_id':case,'instruction':'Increase the applied axial force by 50% and update the displacement plot.',
                      'old_solution_id':old['solution_id'],'new_solution_id':new['solution_id'],
                      'actual_solver_rerun':True,'tip_ratio':new['tip_m']/old['tip_m'],
                      'stale_tip_relative_error':abs(old['tip_m']-new['tip_m'])/abs(new['tip_m'])})
    summary={'scope':'FEM-Bench integration anchor, not full benchmark or model evaluation',
             'upstream_url':'https://github.com/elejeune11/FEM-bench','upstream_commit':commit,
             'upstream_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'license':'MIT, retained in upstream checkout',
             'upstream_reference_tests_passed':2,'physical_cases':12,'actual_FEM_solves':len(records),
             'max_analytic_error_m':max(r['analytic_max_error_m'] for r in records),
             'max_force_balance_relative':max(r['force_balance_relative'] for r in records),'edits':pairs,
             'limitations':['Linear one-dimensional bar anchor only.','No learned model or human edit evaluation in this integration.',
                            'Solution IDs establish provenance; they do not independently prove field correctness.']}
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='edits'},indent=2))


if __name__=='__main__':main()
