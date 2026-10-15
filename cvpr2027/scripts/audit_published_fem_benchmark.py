"""Audit published assets and curate a source-excerpt FEM pilot.

No geometry program, solver or model API is executed. All physical inputs and
reference values come from the downloaded publications; missing data stay missing.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'cvpr2027/data/published-fem-pilot-v1'
PACK = ROOT / 'cvpr2027/tmp/published-fem-pilot-v1'
SOURCE = ROOT / 'cvpr2027/data/web-complex-fem'
CACHE = ROOT / 'cvpr2027/tmp/benchmark-audit'


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def path(value):
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def rel(p):
    return str(p.resolve().relative_to(ROOT))


def evidence(p, **extra):
    return dict(path=rel(p), sha256=sha(p), bytes=p.stat().st_size, **extra)


def source_cards(p, pattern):
    regex = re.compile(pattern, re.I)
    with p.open(errors='replace') as stream:
        return [dict(line=i, text=line.rstrip()) for i, line in enumerate(stream, 1) if regex.search(line)]


def float_card(text):
    return float(re.sub(r'(?<=[\d.])([+-])(?=\d+$)', r'e\1', text.strip()))


def deck_bounds(p):
    bounds = [[math.inf, -math.inf] for _ in range(3)]
    count = 0
    def add(v):
        nonlocal count
        count += 1
        for i, value in enumerate(v):
            bounds[i][0] = min(bounds[i][0], value)
            bounds[i][1] = max(bounds[i][1], value)
    stream = p.open()
    lines = iter(stream)
    reading = False
    for line in lines:
        if p.suffix.lower() == '.inp':
            if line.startswith('*'):
                reading = line.strip().lower() == '*node'
            elif reading:
                bits = line.split(',')
                if len(bits) == 4:
                    add([float(v) for v in bits[1:]])
        elif line.startswith('GRID*'):
            continuation = next(lines)
            add([float_card(line[40:56]), float_card(line[56:72]), float_card(continuation[8:24])])
        elif line.startswith('GRID '):
            add([float_card(line[24:32]), float_card(line[32:40]), float_card(line[40:48])])
    stream.close()
    if not count:
        raise ValueError('No original nodes parsed: ' + str(p))
    return dict(node_count=count, bounds=bounds)


def check_references(c, workbooks):
    """Verify labels against publisher bytes, independently of the PDF plots."""
    cid = c['case_id']; f = path(c['results_file']); refs = c['reference_values']
    if cid.startswith('SFEM'):
        import h5py, numpy as np
        with h5py.File(f) as h:
            actual = [float(h['VonMises'][()].max()), float(np.linalg.norm(h['u'][()], axis=1).max())]
        expected = [refs['max_of_published_median_VonMises_Pa'], refs['max_norm_of_published_median_u_m']]
    elif cid.startswith('BATH'):
        wb = workbooks[str(f)]; prefix, angle = cid[5:].rsplit('_', 1)
        stem = {'Circ': 'Circular', 'Poly': 'Parabolic', 'Sine': 'Sinusoid'}[prefix]
        names = [stem + ' ' + angle] + (['Sinusoidal ' + angle] if prefix == 'Sine' else [])
        sheet = next(wb[n] for n in names if n in wb.sheetnames)
        rows = list(sheet.values); actual_by_key = {str(k): v for k, v in zip(rows[0], rows[2]) if k}
        expected = [v['value'] for v in refs.values()]; actual = [actual_by_key[k] for k in refs]
    elif cid.startswith('WING'):
        wb = workbooks[str(f)]; sheet = wb['Modal Test Result']
        actual = [sheet[v['cell']].value for v in refs.values()]; expected = [v['value'] for v in refs.values()]
    elif cid.startswith('MSHELL'):
        angle = int(cid.split('-')[1])
        with f.open() as s:
            reader = csv.DictReader(s); next(reader)
            rows = [r for r in reader if float(r['UnitCell_angle']) == angle]
        actual = [len(rows), min(float(r['Phi']) for r in rows), max(float(r['Phi']) for r in rows),
                  min(float(r['Torque']) for r in rows), max(float(r['Torque']) for r in rows)]
        expected = [refs['rows'], *refs['twist_range_rad'], *refs['torque_range_mN_m']]
    elif cid.startswith('COLUMN'):
        with f.open() as s:
            rows = list(csv.reader(s, delimiter='\t'))
        actual = [float(rows[v['row'] - 1][2]) for v in refs.values()]
        expected = [v['value'] for v in refs.values()]
    else:
        from bs4 import BeautifulSoup
        text = BeautifulSoup(f.read_text(), 'html.parser').get_text(' ', strip=True)
        actual = [v['value'] for v in refs.values() if str(v['value']) in text]
        expected = [v['value'] for v in refs.values()]
    if len(actual) != len(expected) or any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-14)
                                         for a, b in zip(actual, expected)):
        raise ValueError('Published reference mismatch: ' + cid)
    return len(expected)


def audit():
    import openpyxl, cadquery as cq
    manifest = json.loads((SOURCE / 'published-100.json').read_text())
    workbooks = {str(path(c['results_file'])): None for c in manifest['cases']
                 if path(c['results_file']).suffix == '.xlsx'}
    for f in workbooks:
        workbooks[f] = openpyxl.load_workbook(f, data_only=True)
    checks = {}; records = []; label_checks = 0
    for c in manifest['cases']:
        cid = c['case_id']; ev = []
        for field in ['cad', 'results_file', 'drawing']:
            if c.get(field):
                f = path(c[field]); s = str(f)
                if s not in checks:
                    checks[s] = sha(f)
                if checks[s] != c[field + '_sha256']:
                    raise ValueError('Source asset changed: ' + s)
                ev.append(dict(role=field, path=rel(f), sha256=checks[s], bytes=f.stat().st_size))
        label_checks += check_references(c, workbooks)
        common = dict(case_id=cid, family=c['family'], source_url=c['source_url'],
                      evidence=ev, label_integrity='verified', certified_scored_release=False,
                      independent_baseline_verified=False, acceptance_tolerance_verified=False,
                      candidate_tracks=[], complexity='uncalibrated', public_training_contamination='possible')
        if cid.startswith('SFEM'):
            status = 'exclude_deterministic_solving'
            blockers = ['Realized load coordinates and random samples absent.',
                        'Component-wise median fields do not represent one deterministic FEM solution.',
                        'No dimensioned source drawing verified.']
        elif cid.startswith('BATH'):
            deck = CACHE / 'bath' / (cid[5:] + '.dat')
            cards = source_cards(deck, r'^\s*(/units|MP,EX|MP,NUXY|et,|antype,|nlgeom,|d,_CM|time,|nsub,)')
            ev.append(evidence(deck, role='original_solver_deck', cards=cards))
            status = 'stage_complex_source'; common['complexity'] = 'intricate_lattice_geometry'
            blockers = ['Native Inventor IPT import/meshing route not verified in the benchmark runtime.',
                        'Boundary component coordinates must be mapped to CAD; node IDs cannot transfer to a new mesh.',
                        'DP0 workbook/deck mesh and measurement correspondence needs baseline verification.',
                        'Embedded preview is not a dimensioned drawing.']
        elif cid.startswith('WING'):
            deck = path(c['setup']['file']); parsed = deck_bounds(deck)
            shape = cq.importers.importStep(str(path(c['cad']))).val(); b = shape.BoundingBox()
            cad_lengths = [b.xlen, b.ylen, b.zlen]
            deck_lengths = [v[1] - v[0] for v in parsed['bounds']]
            unit = 'mm' if deck.suffix == '.inp' else 'm'
            numerical_length_mm = max(deck_lengths) * (1 if unit == 'mm' else 1000)
            difference = max(cad_lengths) - numerical_length_mm
            if not math.isclose(difference, 19, abs_tol=1e-6):
                raise ValueError('Unexpected specimen/FEM correspondence: ' + cid)
            ev.append(evidence(deck, role='original_solver_deck', mesh=parsed, coordinate_unit=unit,
                               cad_bbox_lengths_mm=cad_lengths, analysis_length_mm=numerical_length_mm,
                               cad_excess_length_mm=difference))
            status = 'stage_geometry_mapping'; common['complexity'] = 'simple_uniform_or_stepped_plate'
            blockers = ['CAD specimen length exceeds its FEM domain by 19 mm; grip exclusion and coordinate transform unverified.',
                        'FEM shell idealization and thickness regions must be mapped to the original STEP.',
                        'No dimensioned source drawing verified.']
        elif cid.startswith('MSHELL'):
            angle = int(cid.split('-')[1]); deck_angle = 30 if angle == 31 else angle
            folder = CACHE / 'metashell/original/Inputfiles'
            for suffix in ['', '_CCW']:
                deck = folder / f'Model_{deck_angle:02d}degree_th50mm{suffix}.inp'
                cards = source_cards(deck, r'^\*(Hyperelastic|Uniaxial|Element,|Contact Pair|Friction|Surface Behavior|Step,|Static|Coupling|Kinematic)|^Set-\d+, 6, 6,')
                ev.append(evidence(deck, role='original_solver_deck', direction='ccw' if suffix else 'cw', cards=cards))
            status = 'stage_nonlinear_mapping'; common['complexity'] = 'large_strain_hyperelastic_self_contact'
            blockers = ['Ogden parameters are fitted from original uniaxial test data; fitted values/solver fitting convention not archived.',
                        'Deck prescribes +/-6.283 rad, paper states pi; CSV signed angle/rotation and frame mapping unverified.',
                        'CSV is raw FEM torque; author visualization rescales it to experiment. Do not mix those targets.',
                        'Source gripping rings are integrated into FEM geometry; their CAD/fixture mapping needs verification.',
                        'No dimensioned source drawing verified.']
            if angle == 31:
                blockers.insert(0, 'CAD/CSV identify 31 degrees but solver filenames identify 30 degrees; correspondence unresolved.')
        elif cid.startswith('COLUMN'):
            status = 'stage_physics_incomplete'; common['complexity'] = 'nonlinear_buckling_scan_geometry'
            blockers = ['Full nonlinear material law, joint/contact treatment and loading history not verified.',
                        'Boundary-condition sketch is available but no complete source solver deck is verified.',
                        'STL surface-to-volume/section idealization and critical-force definition need verification.']
        elif cid == 'NAFEMS-GNL-CANTILEVER':
            status = 'exclude_provisional_reference'
            blockers = ['Publisher explicitly labels large-strain implementation WORK IN PROGRESS.',
                        'Reference table has duplicated final vertical-displacement labels.',
                        'Branch tracking and finite-strain formulation need independent verification.']
        else:
            status = 'admit_source_complete_pilot'
            common['candidate_tracks'] = ['cad_fem', 'analysis_fem']
            common['complexity'] = 'calibration_curved_geometry_and_boundary_conditions'
            blockers = ['Independent convergence/stress-recovery baseline and acceptance tolerances pending.',
                        'Compatible isolated replay runtime unavailable locally; model execution remains pending.']
            if cid == 'NAFEMS-LE1':
                blockers.append('Inner-ellipse equation in original drawing omits /1000; labelled coordinates and source parameters resolve it.')
            if cid == 'NAFEMS-LE11':
                blockers.append('Drawing rounds a spherical junction height; original source coordinates use sqrt(0.5).')
            for role, value in c['setup'].items():
                if role in ['file', 'mesh_definition']:
                    ev.append(evidence(path(value), role='original_' + role))
            if cid == 'NAFEMS-LE11':
                ev.append(evidence(CACHE / 'init.c', role='source_solver_temperature_default', source_url='https://raw.githubusercontent.com/seamplex/feenox/06965026d6c73919ee02744192ec4b7526bb7e5c/src/pdes/mechanical/init.c', locator='Global zero initialization at line 25; T0 override at lines 373-391.'))
        records.append(common | dict(status=status, blockers=blockers))
    supplementary = []
    for e in json.loads((SOURCE / 'additional-complex-drawings.json').read_text())['entries']:
        p = path(e['local_source'])
        if sha(p) != e['source_sha256']:
            raise ValueError('Supplement source changed')
        if e['fem']:
            status = 'stage_paper_specification'
            blockers = ['Drawing plus reported FEM values does not establish complete geometry, load application and material specification.',
                        'Original solver deck, CAD model and convergence/stress-recovery evidence unverified.']
        else:
            status = 'drawing_only_exclude_fem'; blockers = ['Matching FEM references absent.']
        supplementary.append(dict(source_id=e['id'], title=e['title'], source_url=e['url'], status=status,
                                  evidence=evidence(p), blockers=blockers, certified_scored_release=False))
    report = dict(version=1, collection_case_count=len(records), supplementary_document_count=len(supplementary),
                  admitted_source_complete_cases=sum(r['status'] == 'admit_source_complete_pilot' for r in records),
                  certified_scored_cases=0, distinct_collection_assets_verified=len(checks), reference_values_verified=label_checks,
                  counts=dict(Counter(r['status'] for r in records)), records=records, supplementary=supplementary,
                  policy='Published inputs/labels only; no generated CAD, missing physics, synthetic tasks or new FEM references.',
                  source_audit_is_not_convergence_certification=True, model_trials_run=False)
    save(DATA / 'audit.json', report)
    for wb in workbooks.values():
        wb.close()
    print(json.dumps({k: report[k] for k in ['collection_case_count', 'admitted_source_complete_cases', 'certified_scored_cases', 'counts', 'reference_values_verified']}))


def without_mesh_recipe(p):
    """Copy original geometry statements only; mesh instructions are evaluator-only."""
    lines = []
    for line in p.read_text().splitlines():
        if re.match(r'\s*(Mesh\.|Transfinite|Recombine|Print\s)', line):
            continue
        line = re.sub(r'Layers\{[^}]+\};\s*Recombine;', '', line)
        lines.append(line)
    return '\n'.join(lines) + '\n'


def declaration_excerpt(p):
    kept = []
    for line in p.read_text().splitlines():
        if (re.match(r'\s*(BC\s|E\s*=|nu\s*=|alpha\s*=|T\(x,y,z\)\s*=)', line)):
            kept.append(line)
    return '\n'.join(kept) + '\n'


def build():
    from PIL import Image
    audit_report = json.loads((DATA / 'audit.json').read_text())
    source_cases = {c['case_id']: c for c in json.loads((SOURCE / 'published-100.json').read_text())['cases']}
    declarations = {
        'NAFEMS-LE1': dict(geometry_unit='mm', stress_unit='MPa', formulation='2D plane stress', query=[2000, 0], key='sigma_yy_at_D',
                           figure=None, caution='The drawing inner-ellipse equation has a typo. Original parameters are a=1000, b=2750, c=3250, d=2000 mm; use the labelled endpoints.'),
        'NAFEMS-LE10': dict(geometry_unit='mm', stress_unit='MPa', formulation='3D linear elasticity', query=[2000, 0, 300], key='sigma_yy_at_D',
                            figure=[0, 0, 570, 800], caution='Drawing dimensions are in metres; supplied source geometry uses mm. Pressure=1 MPa. All named boundary faces are defined in the drawing.'),
        'NAFEMS-LE11': dict(geometry_unit='m', stress_unit='Pa', formulation='3D linear thermoelasticity', query=[1, 0, 0], key='sigma_zz_at_A',
                            reference_temperature_degC=0, figure=[0, 0, 1240, 1740], caution='Source uses the exact spherical junction z=sqrt(0.5), not the rounded 0.7 on the drawing. The two taper intervals are .345 m each. Thermal expansion is 2.3e-4 /degC, as published.'),
    }
    rows = []
    if PACK.exists():
        raise ValueError('Pack exists; use a fresh pack path or explicitly remove only this generated pack.')
    for r in audit_report['records']:
        if r['status'] != 'admit_source_complete_pilot':
            continue
        cid = r['case_id']; c = source_cases[cid]; spec = declarations[cid]; private = PACK / 'evaluator-only' / cid
        private.mkdir(parents=True)
        original = path(c['setup']['file'])
        source_text = original.read_text()
        key, ref = next(iter(c['reference_values'].items()))
        contract = dict(case_id=cid, family=c['family'], source_url=c['source_url'], public_training_contamination='possible',
                        qois=[dict(key=spec['key'], unit='MPa', value=ref['value'], kind='published_FEM_solver_output', locator=c['result_locator'])],
                        accepted_tolerances=None, certified_scored_release=False, independent_baseline_verified=False,
                        expected_physics=declaration_excerpt(original), expected_formulation=spec['formulation'],
                        original_assets=r['evidence'], geometry_criteria='Trusted review of topology, dimensions, units and CAD-to-mesh correspondence.',
                        convergence_criteria='Trusted review of at least two distinct refinements and stress recovery; numeric agreement alone does not pass.')
        save(private / 'contract.json', contract)
        for role in ['cad', 'results_file', 'drawing']:
            shutil.copy2(path(c[role]), private / path(c[role]).name)
        shutil.copy2(original, private / original.name)
        meshfile = path(c['setup']['mesh_definition'])
        if meshfile.name != path(c['cad']).name:
            shutil.copy2(meshfile, private / meshfile.name)
        for track in ['cad_fem', 'analysis_fem']:
            folder = PACK / 'candidate-inputs' / track / cid; folder.mkdir(parents=True)
            image = Image.open(path(c['drawing']))
            if spec['figure']:
                image = image.crop(spec['figure'])
            image.save(folder / 'published-problem.png')
            (folder / 'published-physics.txt').write_text(declaration_excerpt(original))
            if track == 'analysis_fem':
                if path(c['cad']).suffix == '.step':
                    shutil.copy2(path(c['cad']), folder / 'part.step')
                    (folder / 'published-geometry.geo').write_text(without_mesh_recipe(meshfile).replace('nafems-le10.step', 'part.step'))
                else:
                    (folder / 'published-geometry.geo').write_text(without_mesh_recipe(meshfile))
            input_spec = {k: spec[k] for k in ['geometry_unit', 'stress_unit', 'formulation', 'query', 'key', 'caution']}
            if 'reference_temperature_degC' in spec:
                input_spec.update(reference_temperature_degC=spec['reference_temperature_degC'], reference_temperature_provenance='Original source solver zero default; verified from pinned initialization code.')
            input_spec.update(output_unit='MPa', quantity='signed normal stress', source_input_policy='Original source excerpts; do not infer missing physics.')
            save(folder / 'input.json', input_spec)
            prompt = ('Construct CAD from the original published diagram and its source precision notes.' if track == 'cad_fem'
                      else 'Use the supplied original STEP/Gmsh geometry definition; generate and refine your own analysis mesh.')
            (folder / 'task.md').write_text('# Published FEM problem\n\n' + prompt + '\n\n'
              'The problem, material data, loads and constraints are supplied in published-problem.png, published-physics.txt and input.json. '
              'The text declarations are original source excerpts, not a solution program. In those declarations u/v/w denote x/y/z displacement. '
              'Pressure p is inward normal pressure; tension is outward normal traction. '\
              'Units and the requested sampling point are in input.json.\n\n'
              'Solve this physical problem using FEM. Save executable main.py, mesh.msh, field output (VTK/XDMF/NPZ), '
              'solver.log and refinement.json with at least two distinct mesh resolutions and the requested quantity at each. '
              'For cad_fem, export part.step. Include an explanation of formulation, physical setup and stress recovery. '
              'Do not return a recalled stress value without a solver workflow.\n\n'
              'results.json format: {"qois": {"'+spec['key']+'": {"value": <signed number>, "unit": "MPa"}}}.\n'
              'No reference values or acceptance thresholds are supplied.\n')
            files = [evidence(p) | dict(path=p.name) for p in sorted(folder.iterdir())]
            task = dict(case_id=cid, track=track, family=c['family'], title=c['title'], files=files,
                        output_keys={spec['key']: 'MPa'}, status='source_complete_diagnostic_pilot', certified_scored_release=False,
                        required_artifacts=['main.py', 'mesh.msh', 'solver.log', 'refinement.json', 'results.json'] + (['part.step'] if track == 'cad_fem' else []),
                        field_artifact_required=True)
            save(folder / 'task.json', task)
            rows.append(dict(case_id=cid, track=track, family=c['family'], title=c['title'], complexity=r['complexity'],
                             candidate_manifest=rel(folder / 'task.json'), private_contract=rel(private / 'contract.json'),
                             status='source_complete_diagnostic_pilot', certified_scored_release=False))
    catalog = dict(version=1, cases=len({r['case_id'] for r in rows}), track_tasks=len(rows), certified_scored_cases=0,
                   records=rows, separate_track_reports=True, separate_complexity_reports=True, model_trials_run=False,
                   source_policy='Published source excerpts only; missing inputs are admission blockers.',
                   release_blockers=['No verified isolated runtime.', 'No independently verified refinement/recovery baseline or acceptance tolerances.',
                                     'No blind trusted physics/CAD/mesh reviewer certification.', 'Public example contamination cannot be ruled out.'])
    save(DATA / 'catalog.json', catalog)
    (DATA / 'submission-example.json').write_text(json.dumps(dict(qois=dict(sigma_yy_at_D=dict(value=None, unit='MPa'))), indent=2)+'\n')
    print('Prepared', catalog['cases'], 'source cases in', catalog['track_tasks'], 'answer-separated track packages.')


def validate():
    catalog = json.loads((DATA / 'catalog.json').read_text()); checked = 0
    for row in catalog['records']:
        f = path(row['candidate_manifest']); task = json.loads(f.read_text()); folder = f.parent
        contract = json.loads(path(row['private_contract']).read_text())
        assert set(task['output_keys']) == {q['key'] for q in contract['qois']}
        assert task['track'] == row['track'] and not task['certified_scored_release']
        assert {p.name for p in folder.iterdir()} == {'task.json'} | {x['path'] for x in task['files']}
        for item in task['files']:
            p = folder / item['path']; assert sha(p) == item['sha256']; checked += 1
            assert p.suffix not in ['.fee', '.html', '.yaml', '.xlsx', '.h5']
            if task['track'] == 'cad_fem':
                assert p.suffix not in ['.step', '.geo', '.inp', '.bdf', '.ipt', '.stl']
            if p.suffix in ['.md', '.txt', '.json', '.geo']:
                text = p.read_text()
                assert 'SOLVE_PROBLEM' not in text and 'PRINTF' not in text
                for q in contract['qois']:
                    assert str(q['value']) not in text
        assert contract['accepted_tolerances'] is None
    report = dict(status='passed', packages=len(catalog['records']), candidate_asset_hash_checks=checked,
                  answer_separation='Text and allowed-file checks passed; source image crops manually inspected.',
                  certified_scored_cases=0, numerical_replay_performed=False)
    save(DATA / 'validation.json', report); print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['audit', 'build', 'validate', 'all'])
    args = parser.parse_args()
    if args.action in ['audit', 'all']: audit()
    if args.action in ['build', 'all']: build()
    if args.action in ['validate', 'all']: validate()
