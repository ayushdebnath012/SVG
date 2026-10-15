"""Build a source-bound CAD+FEM task catalog; never invent source physical inputs.

Run from any directory. Requires the existing official-site crawl and v1 figure
curation. Full source text and images stay in ignored tmp/, not this dataset.
"""
from __future__ import annotations
import hashlib
import html
import json
import math
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/femcad-source-v2'
OLD = ROOT / 'data/femcad-hard-v1'
CACHE = ROOT / 'tmp/wolfram-fem-scrape'
REVIEW = ROOT / 'tmp/femcad-figures/continuation-review'
CATEGORIES = ['Geometric Modeling', 'Mesh Generation', 'Heat Transfer', 'Fluid Dynamics', 'Mass Transport', 'Solid Mechanics', 'Acoustics', 'Electromagnetics', 'Multiphysics', 'System Physics']

def digest(data):
    return hashlib.sha256(data).hexdigest()

def allowed(url):
    host = urlparse(url).hostname or ''
    return urlparse(url).scheme == 'https' and (host == 'mfem.org' or host.endswith('.mfem.org') or host == 'wolfram.com' or host.endswith('.wolfram.com'))

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

# A range identifies zero-based HTML input-code cells, NOT Wolfram In[] labels.
# Earlier definitions on the same page remain prerequisites, not new assumptions.
BASE = [
 (11, 'brake-disc', 'Heat Transfer', 'complex', 'Disc brake: axisymmetric friction heating', [(0,17)], [0,1], 'Reconstruct the disc and pad-track partition. Reproduce the source axisymmetric transient thermal analysis, including its actual flux and natural boundary conditions.', 'Temperature field and hottest-point temperature at the source end time.'),
 (14, 'shrink-fit-assembly', 'Heat Transfer', 'complex', 'Shrink-fit rod and frame: transient assembly clearance', [(0,28)], [2], 'Reconstruct both contacting regions. Reproduce the source transient heat problem and its clearance calculation.', 'Temperatures of both components and assembly-clearance history.'),
 (15, 'anemometer-chip', 'Heat Transfer', 'hardest', 'Etched anemometer: stationary thermal sensing', [(0,33)], [4,5], 'Reconstruct the etched membrane, heater, cavity and channel with original region and boundary markers. Reproduce the stationary source model; resolve the source length scale explicitly.', 'Temperature field, heater temperature and region/boundary marker map.'),
 (16, 'branched-chamber', 'Fluid Dynamics', 'complex', 'Branched spherical chamber: ramped transient flow', [(0,1),(55,69)], [6], 'Reconstruct the connected chamber and pipes. Use the source transient Navier–Stokes equations, ramped inlet and initial conditions; preserve the mixed interpolation orders.', 'Velocity and pressure fields at the final source time, inlet/outlet fluxes and continuity residual.'),
 (19, 'hook-a', 'Geometric Modeling', 'hardest', 'Printed hook A: filleted curved design under load', [(0,67)], [11], 'Reconstruct hook1 with all source fillets and countersunk fixation holes. Apply the material calibration, infill choice, supports and load of the source mechanical comparison.', 'Displacement and stress fields, resultant support force, and comparison quantities for hook1.'),
 (20, 'hook-b', 'Solid Mechanics', 'complex', 'Printed hook B: pocketed reinforced design under load', [(0,67)], [11], 'Reconstruct hook2 including its pocket and fixation holes. Apply the source mechanical comparison setup and its calibrated material.', 'Displacement and stress fields and comparison quantities for hook2.'),
 (21, 'hook-c', 'Solid Mechanics', 'complex', 'Printed hook C: filleted angular design under load', [(0,67)], [11], 'Reconstruct hook3 including the five specified edge fillets and fixation holes. Preserve the source load and calibrated material.', 'Displacement and stress fields and comparison quantities for hook3.'),
 (22, 'dogbone', 'Solid Mechanics', 'hardest', 'Dogbone: fitted Yeoh model with stiff clamp regions', [(0,74)], [19,20], 'Reconstruct the specimen and clamps. Reproduce the source fitted Yeoh FEM experiment, including the actual 2D model, thickness, clamp material and continuation schedule.', 'Full force–extension history and source strain/stress comparison quantities.'),
 (23, 'biaxial-specimen', 'Solid Mechanics', 'hardest', 'Perforated biaxial specimen: finite-strain loading', [(0,27)], [23], 'Reconstruct the quarter specimen and suture-hole boundaries. Reproduce the source displacement-controlled hyperelastic experiment and symmetry reduction.', 'Reaction forces, stress and displacement through the source loading schedule.'),
 (26, 'helmholtz-resonator', 'Acoustics', 'complex', 'Neck-and-cavity resonator: forced frequency response', [(0,30)], [24], 'Reconstruct the resonator air volume. Reproduce the source pressure-driven axisymmetric frequency sweep and frequency-dependent mesh sizing.', 'Complex pressure responses and cavity response over the source sweep; identify resonant peaks.'),
 (33, 'coil-pair', 'Electromagnetics', 'complex', 'Coil pair: axisymmetric magnetostatic field', [(0,54)], [25], 'Reconstruct both windings and the exterior air region. Reproduce the source magnetostatic setup and its axis treatment.', 'Magnetic vector potential, flux density and center-field value with its limiting treatment on the axis.'),
 (34, 'mems-beam', 'Multiphysics', 'hardest', 'MEMS actuator: electrostatic and structural coupling', [(0,47)], [26], 'Reconstruct the beam, electrode and air regions. Follow the source electrostatic-to-structural coupling and displacement iteration.', 'Potential, beam displacement and converged electrostatic load, with iteration history.'),
 (36, 'hygroscopic-gasket', 'Mass Transport', 'hardest', 'Gasket: coupled diffusion, heat and hyperelastic swelling', [(0,74)], [27], 'Reconstruct the gasket and loading plate. Keep the source diffusion, thermal and mechanical coupling and continuation; retain deformation-dependent transport coefficients.', 'Concentration, temperature and displacement fields through the complete continuation.'),
 (38, 'dew-condenser', 'Multiphysics', 'hardest', 'Passive condenser: wind, radiation and dew collection', [(0,168)], [28], 'Reconstruct the condenser, insulation, supports and flow domain. Preserve the source meteorological inputs, sky radiation, heat transfer and condensation calculation.', 'Flow and temperature fields, surface-temperature history and predicted condensed-water quantity.'),
 (55, 'bookshelf-bracket', 'Solid Mechanics', 'complex', 'Bookshelf bracket: mounted eigenmodes', [(0,30),(82,98)], [32,40], 'Reconstruct the complete bracket and mounting features. Use the source material entity and mounting conditions in its six-mode eigenanalysis.', 'Six source-convention eigenfrequencies and normalized mode fields.'),
 (56, 'bookshelf-bracket', 'Solid Mechanics', 'complex', 'Bookshelf bracket: unconstrained eigenmodes', [(0,30),(82,102)], [32,40], 'Reconstruct the complete bracket. Reproduce the source unconstrained twelve-mode solve, retaining and identifying rigid-body modes.', 'Twelve eigenvalues, rigid-mode identification and elastic mode fields.'),
 (57, 'filleted-l-bracket', 'Mesh Generation', 'hard', 'L-bracket: fillet stress convergence', [(0,1),(547,563)], [42], 'Reconstruct the source filleted L-bracket. Reproduce its refined curved-boundary stress analysis and compare the documented mesh variants.', 'Mesh-dependent maximum von Mises stress and convergence evidence; distinguish the sharp-corner singularity from the filleted case.'),
 (61, 'bimetal-insert', 'Solid Mechanics', 'complex', 'Steel block with aluminum insert: thermal expansion', [(0,1),(286,301)], [45], 'Reconstruct both material regions and their shared interface. Reproduce the source plane-stress thermal-strain problem with original thickness and constraints.', 'Displacement, interface tractions and stress components.'),
 (62, 'plate-hole-3d', 'Solid Mechanics', 'hard', 'Plate with bore: 3D tensile verification', [(0,2),(161,175)], [46], 'Reconstruct the perforated plate. Reproduce the source 3D verification case, including both documented equation formulations.', 'Source probe displacement/stress values and verification error against the source test target.'),
 (63, 'plate-hole-plastic', 'Solid Mechanics', 'hardest', 'Perforated plate: plastic loading and unloading history', [(0,0),(150,173)], [48], 'Reconstruct the quarter plate. Reproduce the source extended-plane-strain loading/unloading sequence without resetting plastic state between increments.', 'Displacement and plastic strain at every step, including residual deformation after unloading.'),
 (64, 'magnet-coin', 'Electromagnetics', 'hardest', 'Horseshoe permanent magnet and coin', [(0,43)], [49], 'Reconstruct the magnet segments, coin and exterior domain. Reproduce the source magnetization directions, material interfaces and scalar-potential FEM analysis.', 'Potential, flux-density field and source secondary magnetic quantities.'),
 (66, 'looped-manifold', 'Fluid Dynamics', 'complex', 'Looped manifold: non-Newtonian flow', [(0,1),(158,173)], [67], 'Reconstruct the branched planar flow region. Reproduce the source power-law fluid, inlet and pressure reference, preserving the planar model and source units.', 'Velocity, pressure, apparent viscosity and viscous stress fields.'),
 (67, 'heated-tube', 'Heat Transfer', 'hard', 'Internally heated tube: axisymmetric verification', [(0,0),(36,46)], [68], 'Reconstruct the tube cross-section and heated inner-wall band. Reproduce the source axisymmetric steady heat verification.', 'Temperature at the official probe and source verification residual.'),
 (68, 'heating-coil', 'Multiphysics', 'complex', 'Tungsten heating coil: current and Joule heat', [(0,38)], [70,71], 'Reconstruct the rounded wire coil and terminal faces. Reproduce the source electric-current and heat-transfer chain, including heat loss and source material properties.', 'Potential, current density, Joule source and final temperature field.'),
 (69, 'brake-disc', 'Multiphysics', 'hardest', 'Disc brake: transient thermal stress', [(0,49)], [0,1], 'Reconstruct the source disc. Solve its thermal history followed by the documented axisymmetric structural analysis, carrying the spatial temperature field into each structural step.', 'Displacement and stress history with source temperature-to-stress transfer.'),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    old = {int(r['id'][-3:]):r for r in map(json.loads, (OLD/'tasks.jsonl').read_text().splitlines())}
    curation = json.loads((OUT/'figure-curation.json').read_text())
    reviewed = {int(i): f for i, f in curation['legacy_figures'].items()}
    candidates = {int(i): f for i, f in curation['muffler_figures'].items()}
    pages = {}
    for p in sorted(CACHE.glob('*.json')):
        r = json.loads(p.read_text())
        if p.with_suffix('.html').exists(): pages[r['url']] = (p,r)
    used, records = {}, []

    def source(url):
        if url in used: return used[url]
        path, rec = pages[url]
        raw = path.with_suffix('.html').read_bytes()
        soup = BeautifulSoup(raw, 'html.parser')
        cells = []
        for idx, el in enumerate(soup.select('figure.figure-input')):
            node = el.select_one('[data-code]')
            code = el.select_one('code')
            caption = code.get_text() if code else ''
            assert node is not None, (url, idx)
            cells.append(dict(index=idx, anchor=node.get('id'), url=urljoin(url,node['data-code']),
                              caption_sha256=digest(caption.encode()), caption_is_abbreviated='...' in caption))
        used[url] = dict(url=url, title=rec['title'], html_sha256=digest(raw), fetched_utc=rec['fetched_utc'],
                         cached_html=str(path.with_suffix('.html').relative_to(ROOT)), cells=cells)
        return used[url]

    def findpage(key):
        return next(u for u in pages if '/PDEModels/' in u and u.endswith('/'+key+'.html'))

    def add(title, family, category, tier, url, ranges, figures, objective, outputs, selection=None, legacy=None, geometry_url=None):
        src = source(url)
        indexes = sorted({i for a,b in ranges for i in range(a,b+1)})
        assert indexes and max(indexes) < len(src['cells']), (title,max(indexes),len(src['cells']))
        figs=[]
        for f in figures:
            assert allowed(f['url']) and f.get('local') and (ROOT/f['local']).is_file(), f
            figs.append(dict(url=f['url'], local=f['local'], kind=f.get('kind','part-mesh'),
                             review='manually accepted engineering geometry; no solution field or graph',
                             sha256=digest((ROOT/f['local']).read_bytes())))
        assert figs
        geom = source(geometry_url)['url'] if geometry_url else url
        selector = selection or {'type':'documented_analysis','focus_cell_indices':indexes}
        prompt = (f'{objective}\n\nAuthoritative FEM source: {url}\nGeometry source: {geom}\n'
                  f'Source input cells (zero-based HTML order): {indexes}. Resolve their prerequisites from the same source page. '
                  'Use the full downloadable code-cell URLs in sources.json; abbreviated screen-reader captions are not executable specifications. '
                  f'Case selection: {json.dumps(selector,ensure_ascii=False)}.\n\n'
                  'Deliver a reproducible CAD construction, STEP geometry (or planar CAD where the source is 2D), '
                  'a boundary/material region map, mesh, FEM implementation and results.json. Preserve source dimensions, units, '
                  'fillets, constitutive law, loads, boundary/initial conditions and model dimensionality. Resolve and record '
                  'all source material-entity values and installation support files; report a missing dependency instead of guessing. '
                  'Include mesh-convergence and appropriate balance/residual checks. Do not use solution-field or graph images as CAD inputs.\n'
                  f'Required results: {outputs}')
        split_group = ('printed-hooks' if family.startswith('hook-') else
                       'automotive-mufflers' if family.startswith('muffler-') else
                       'perforated-plates' if family.startswith('plate-hole-') else family)
        rec=dict(id=f'FEMCAD2-{len(records)+1:03d}', title=title, geometry_family=family, split_group=split_group,
                 category=category, tier=tier, difficulty_status='proposed; not empirically calibrated',
                 source=dict(url=url,html_sha256=src['html_sha256'],focus_cell_indices=indexes,geometry_url=geom),
                 source_case=selector,figures=figs,prompt=prompt,required_results=outputs,
                 physical_inputs_origin='official source cells only; no locally added physical values',
                 rubric_origin='dataset author; CAD export and convergence requirements are evaluation instructions',
                 readiness=dict(level='source-linked task specification', solver_run=False, gold_answer_available=False,
                                dependency_resolution='pending: full source prerequisites, runtime data and support files'),
                 model_evaluation=dict(status='not attempted',failure_established=False),legacy_id=legacy)
        records.append(rec)

    for i,family,cat,tier,title,ranges,figids,objective,outputs in BASE:
        r=old[i]
        g=r['source'].get('geometry_page',{}).get('url')
        add(title,family,cat,tier,r['source']['url'],ranges,[reviewed[j] for j in figids],objective,outputs,legacy=r['id'],geometry_url=g)
    # Two additional documented FEM formulations replace v1 entries with only 2D-mesh pictures.
    add('Internally heated tube: full 3D verification','heated-tube','Heat Transfer','complex',findpage('HeatTransferVerificationTests'),[(0,0),(36,51)],[reviewed[68]],
        'Construct the full tube with the source inner-wall band. Reproduce the explicitly documented 3D thermal verification and compare its axisymmetric counterpart.',
        'Temperature at the 3D source probe, source verification residual and agreement with the axisymmetric solution.')
    add('Dogbone: fitted Neo-Hookean 3D tensile experiment','dogbone','Solid Mechanics','hardest',findpage('HyperelasticModelComparison'),[(0,52)],[reviewed[19],reviewed[20]],
        'Reconstruct the extruded dogbone and clamp extensions. Reproduce the source 3D Neo-Hookean experiment and its fitted material parameters and incremental force schedule.',
        'Force–extension history, deformed geometry and strain field.')

    bracket_url=findpage('SolidMechanics')
    bracket_geometry=old[55]['source']['geometry_page']['url']
    def bracket(title,tier,ranges,objective,outputs,selection):
        add(title,'bookshelf-bracket','Solid Mechanics',tier,bracket_url,[(0,30)]+ranges,[reviewed[32],reviewed[40]],objective,outputs,selection,geometry_url=bracket_geometry)
    for force in range(100,1001,100):
        bracket(f'Bookshelf bracket: source force sweep, {force} N','hard',[(103,108)],
                'Reconstruct the source bracket with fillets, chamfers and fixation holes. Solve this member of the published force sweep using the original material entity and supports.',
                'Displacement magnitude at the source sweep probe, displacement/stress fields and support reactions.',
                dict(type='published_sweep_member',parameter='force',value=force,unit='N',source_cell_index=107,source_expression='Range[100, 1000, 100]'))
    for k in range(31):
        exponent=3+k/20
        bracket(f'Bookshelf bracket: source harmonic case {k+1:02d}','complex',[(114,123)],
                'Reconstruct the source bracket. Solve this published frequency-sweep member with the exact source frequency-dependent load expression, including its sine factor; do not substitute a constant-amplitude force.',
                'Complex displacement/stress fields and the source query-point displacement measure; state complex-amplitude conventions.',
                dict(type='published_sweep_member',parameter='angular_frequency',value=10**exponent,unit='rad/s',exact_expression=f'10^({60+k}/20)',frequency_hz=10**exponent/(2*math.pi),source_cell_index=117,source_expression='Table[10.^i/(2 Pi), {i, 3, 4.5, 0.05}]'))
    bracket('Bookshelf bracket: transient sinusoidal loading','hardest',[(82,94)],
            'Reconstruct the bracket and reproduce the complete source time-dependent load case, initial conditions and mounting conditions.',
            'Query-point displacement and stress histories through the source end time.',dict(type='documented_analysis',name='Time-Dependent Analysis'))
    bracket('Bookshelf bracket: source Poisson-ratio comparison','complex',[(103,113)],
            'Reconstruct the bracket and reproduce the source normalized-material comparison as written. Keep its normalization explicit; do not interpret its unit Young modulus as titanium.',
            'Displacement and stress comparison for all three documented Poisson ratios.',dict(type='published_sweep',parameter='PoissonRatio',values=[0.1,0.3,0.4],unit='1',source_cell_index=111))

    muffler_url=findpage('AcousticMuffler')
    # Ten selected frequencies are literal members of the published 20:10:1000 Hz sweep.
    for variant,figidx,tier,extra in [('classical',0,'complex',[(0,11),(27,29)]),('perforated',1,'hardest',[(0,16),(27,29)]),('padded',0,'hardest',[(0,11),(17,22),(27,29)])]:
        for freq in range(100,1001,100):
            add(f'{variant.capitalize()} muffler: {freq} Hz','muffler-perforated' if variant=='perforated' else 'muffler-classical',
                'Acoustics',tier,muffler_url,extra,[candidates[figidx]],
                f'Reconstruct the {variant} muffler air volume from the source support geometry, retaining internal partitions and apertures. Solve the selected source frequency. For the padded case also reconstruct its material subregions and use its empirical complex coefficients.',
                'Complex acoustic pressure and source-defined transmission loss, using the documented outlet probe and power convention.',
                dict(type='published_sweep_member',model=variant,parameter='frequency',value=freq,unit='Hz',source_cell_index=11 if variant=='classical' else 16 if variant=='perforated' else 22,source_expression='Table[f, {f, 20, 1000, 10}]'))

    assert len(records)==100, len(records)
    assert len({r['id'] for r in records})==100
    assert len({r['prompt'] for r in records})==100
    for s in used.values():
        assert allowed(s['url']) and all(allowed(c['url']) for c in s['cells'])
    (OUT/'tasks.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    dump(OUT/'sources.json',dict(index_convention='zero-based HTML figure.figure-input order; not In[]',pages=list(used.values())))
    retained={r['legacy_id'] for r in records if r['legacy_id']}
    reasons={1:'FEM setup locally added to CAD-only source',2:'FEM setup locally added to CAD-only source',3:'FEM setup locally added to CAD-only source',4:'FEM setup locally added to CAD-only source',5:'FEM setup locally added to CAD-only source',6:'FEM setup locally added to CAD-only source',8:'Not selected: simplified cross-section; no need to fill quota with a weaker visual case',17:'Flow properties and inlet locally added',31:'Plain spherical domain',32:'Permittivity locally added; no verified replacement selected',42:'Family study overlaps retained hook tasks; not counted separately',43:'Detailed CAD transferred to a different source thermal model',44:'MFEM geometry page lacks this task’s FEM loading setup',54:'Covered by the source 500 N force-sweep member, restoring source material',58:'Plain spherical domain',59:'Plain annular domain',60:'Only a 2D mesh image accepted previously; units assigned locally',65:'Only a 2D mesh image accepted previously'}
    dump(OUT/'legacy-audit.json',{'retained_and_rewritten':sorted(retained),'excluded':[{'id':r['id'],'title':r['title'],'source_url':r['source']['url'],'reason':reasons[i]} for i,r in old.items() if r['id'] not in retained],
        'corrections':['All v1 numerical prompts replaced with authoritative source bindings.','Restored source fillets and material entities.','Chamber changed back to source transient Navier–Stokes.','Resonator changed back to source driven frequency response.','Restored gasket thermal coupling and condenser radiative model.','No v1 analytic or estimated reference answers inherited.']})
    families=Counter(r['geometry_family'] for r in records)
    dump(OUT/'families.json',[
        dict(geometry_family=f, split_group=next(r['split_group'] for r in records if r['geometry_family']==f),
             case_ids=[r['id'] for r in records if r['geometry_family']==f],
             source_urls=sorted({r['source']['url'] for r in records if r['geometry_family']==f}))
        for f in sorted(families)])
    stats=dict(tasks=len(records),geometry_families=len(families),split_groups=len({r['split_group'] for r in records}),families=dict(sorted(families.items())),categories={c:sum(r['category']==c for r in records) for c in CATEGORIES},tiers=dict(Counter(r['tier'] for r in records)),source_pages=len(used),source_sites={'wolfram.com':100,'mfem.org':0},known_model_failures=0,solver_validated_cases=0,unique_figures=len({f['url'] for r in records for f in r['figures']}))
    dump(OUT/'validation.json',dict(status='PASS: structural/provenance checks only',checks=['100 unique IDs and prompts','All sources and image URLs on allowed domains','Every task has manually reviewed engineering geometry','Every image exists locally and has SHA256','Every selected cell index resolves','Family grouping present for split protection'],statistics=stats))
    mfem=json.loads((OLD/'mfem-sources.json').read_text())
    dump(OUT/'coverage.json',dict(requested_sites=['https://mfem.org','https://www.wolfram.com/language/core-areas/fem/'],statistics=stats,
         gaps=['System Physics: no qualifying source-defined FEM + engineering CAD drawing case selected.','MFEM: no qualifying complete engineering CAD plus FEM case selected from the existing crawl; no physics invented for a geometry-only example.'],
         mfem_pages_crawled=len(mfem['pages']),mfem_crawl_manifest='../femcad-hard-v1/mfem-sources.json',wolfram_crawl_manifest='../femcad-hard-v1/wolfram-sources.json'))
    lines=['# FEMCAD Source v2','',f'100 source-linked CAD + FEM cases across {len(families)} geometry families. This is **not 100 distinct parts**.',
           '', 'The allowed sources are Wolfram’s FEM documentation and mfem.org. The accepted cases currently come from Wolfram. The MFEM crawl is recorded in coverage.json; its CAD-only cross-heat example was excluded rather than assigning new loads.',
           '', '## What is included','',
           '- 27 selected source analyses, 10 bracket force cases, 31 bracket harmonic cases, one bracket transient case, one normalized material comparison and 30 muffler frequency cases.',
           '- Engineering geometry drawings/CAD renders/part meshes only. No solution fields or graph inputs. Some source geometries are planar or axisymmetric engineering cross-sections, explicitly preserved as such.',
           '- Every task requires CAD construction **and** a FEM prediction, with original source material, boundary conditions and physical model.',
           '- `tasks.jsonl`: prompts, exact case selectors, source bindings, geometry families, figure URLs/hashes and evaluation status.',
           '- `sources.json`: cached page hashes and downloadable full code-cell URLs. Indices are zero-based HTML input order, not Mathematica In[] numbers.',
           '- `families.json`: a deduplicated shape-family index and case IDs, with 21 conservative split groups.',
           '- `legacy-audit.json`: exclusions and corrections to v1. The prior dataset is preserved.',
           '- `coverage.json` and `validation.json`: category gaps, family counts and structural validation.',
           '- `figure-curation.json`: persistent manually reviewed geometry-image selection.',
           '- `cell-fetch.json` and `dependencies.json`: full-cell retrieval evidence and unresolved runtime/support-file dependencies (generated by the companion fetch script).',
           '- `index.html`: browsable catalog with search and category/difficulty filters; local source images must be present under tmp/.',
           '', '## Readiness and difficulty','',
           '**This is a task-specification dataset, not a solved or execution-validated benchmark.** No task has a validated gold answer or an established model failure. Hard/complex/hardest are proposed labels. Simple load/frequency variants may be easier once their shared family is solved.',
           '', 'The official tutorials include worked solutions. This catalog is an open-book reproduction/generation dataset, not a set of unseen examination problems. An image-only or held-out evaluation would require a separate input/reference split and independently checked answers.',
           '', 'Prompts deliberately reference the authoritative full source instead of substituting guessed parameters. Before execution, resolve prerequisite cells, material entities, Wolfram runtime defaults and support files. For example, muffler CAD is provided through ClassicalMuffler.stl / PerforatedMuffler.stl in the Wolfram installation; the bracket tutorial imports BookShelfBracket.wxf. Those installation files are not bundled or falsely marked as downloaded. The matching CAD construction tutorial is linked where available.',
           '', 'CAD export and convergence checks are author-created evaluation instructions, not claimed source measurements. Preserve planar/axisymmetric physics; do not invent thickness, convert an axisymmetric problem to arbitrary 3D loading, omit fillets, or infer boundary markers from pictures.',
           '', '**Split by split_group**, never randomly by row. The stricter split groups keep all hook designs together, all mufflers together and both perforated-plate studies together. Bracket cases and dogbone formulations also stay together. Geometry-family counts describe shapes, not independent test problems.',
           '', '## Rebuild','', '```sh','cvpr2027/tmp/femref-venv/bin/python cvpr2027/scripts/build_femcad_source_dataset.py','cvpr2027/tmp/femref-venv/bin/python cvpr2027/scripts/fetch_femcad_source_cells.py --all-selected','cvpr2027/tmp/femref-venv/bin/python cvpr2027/scripts/validate_femcad_source_dataset.py','```',
           '', 'The rebuild uses the existing crawled HTML and manually reviewed figure cache. Source images/full pages remain in git-ignored tmp/; the dataset records their original URLs and attribution. This does not grant a redistribution license for source assets.',
           '', '## Category coverage','', '| Category | Cases |','|---|---:|']
    lines += [f'| {c} | {stats["categories"][c]} |' for c in CATEGORIES]
    lines += ['', 'System Physics remains uncovered. Categories are not filled with unrelated CAD-only tasks.', '', '## Geometry families','', '| Family | Cases |','|---|---:|']
    lines += [f'| {f} | {n} |' for f,n in sorted(families.items())]
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    cards=[]
    for r in records:
        images=''.join(f'<a href="{html.escape(f["url"])}"><img loading="lazy" src="../../{html.escape(f["local"])}" alt="Source geometry: {html.escape(r["title"])}"></a>' for f in r['figures'])
        cards.append(f'<article data-category="{r["category"]}" data-tier="{r["tier"]}"><h2>{r["id"]} · {html.escape(r["title"])}</h2><p>{r["category"]} · {r["tier"]} · family: {r["geometry_family"]}</p><div class="images">{images}</div><a href="{html.escape(r["source"]["url"])}">Official FEM source</a><details><summary>Task and source case</summary><pre>{html.escape(r["prompt"])}</pre></details></article>')
    catalog='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>FEMCAD Source v2</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px;background:#f3f5f7;color:#18202a}article{background:white;border:1px solid #d5dbe2;padding:20px;border-radius:12px;margin:18px 0}h2{font-size:19px}.images{display:flex;flex-wrap:wrap;gap:16px}img{width:280px;height:230px;object-fit:contain;background:white}pre{white-space:pre-wrap;font:14px/1.55 system-ui}input,select{font:inherit;padding:9px;margin:4px}details{margin-top:15px}.note{background:#fff2cb;padding:18px;border-radius:8px}a{color:#075ca9}</style><h1>FEMCAD Source v2</h1>'''
    catalog+=f'<p>100 CAD + FEM cases · {len(families)} geometry families · official source drawings</p><p class="note">Task specifications only. Difficulty is proposed; gold answers, dependency resolution and model failures are unverified. Repeated load/frequency cases are grouped by geometry family. Source images © their respective owners.</p><input id="search" placeholder="Search parts or families" aria-label="Search"><select id="cat" aria-label="Category"><option value="">All categories</option>'+''.join(f'<option>{c}</option>' for c in CATEGORIES)+'</select><select id="tier" aria-label="Difficulty"><option value="">All difficulty levels</option><option>hard</option><option>complex</option><option>hardest</option></select><p id="count"></p>'+''.join(cards)
    catalog+='''<script>const q=document.querySelector('#search'),c=document.querySelector('#cat'),t=document.querySelector('#tier');function filter(){let n=0;document.querySelectorAll('article').forEach(a=>{let show=a.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!c.value||a.dataset.category===c.value)&&(!t.value||a.dataset.tier===t.value);a.hidden=!show;n+=show});document.querySelector('#count').textContent=n+' cases shown'}[q,c,t].forEach(x=>x.addEventListener('input',filter));filter();</script></html>'''
    (OUT/'index.html').write_text(catalog)
    print(json.dumps(stats,indent=2))

if __name__=='__main__': main()
