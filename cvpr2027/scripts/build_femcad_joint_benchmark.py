#!/usr/bin/env python3
"""Prepare a single end-to-end CAD+FEM protocol from existing source evidence."""
import html
import copy
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from package_fem_evaluation_inputs import ROOT, DATA, OUT as ASSISTED, nodes, selected, txt, render, image_urls, sha, save

OUT=ROOT/'tmp/femcad-joint-benchmark'
# Prioritize images with dimension/scale annotations for review, without certifying adequacy.
DIMENSIONED={5,10,11,21,34,48}
SPECIAL={
  3:'Base thermal model defines loads/conditions outside this tutorial.',
  5:'Source suppresses individual perforations in CAD; reproduce the declared effective-acoustics geometry, not every photographed hole.',
  6:'Club head and 362 dimples are not fully dimensioned in the model-definition drawings.',
  11:'Dimensioned seal cross-section and constitutive/contact data are present; precise contour interpretation and both air-pressure cases need review.',
  18:'Only manufacturing-variation sketches are supplied here; base gyroscope geometry/physics is external.',
  24:'Airfoil coordinate files were removed as explicit geometry; the illustrations alone do not define exact airfoil profiles.',
  26:'Homogenized material properties depend on a separate model.',
  30:'The load-colored figure is held out. A visually reviewed original geometry-only image from setup block 60 is retained without its instructions. Dimensions and LES forcing remain incomplete.',
  31:'The board assembly and base structural model are external.',
  39:'Binary material library removed; all needed material properties must be established in permitted input specifications.',
  40:'Binary material library removed. Supplied circuit curves are upstream data from study 039; isolate each task/context.',
  48:'Dimensioned axisymmetric drawing and constitutive equations are present; magnetic susceptibility, mechanical loading cases and remaining material data require completeness review.',
}


def problem_blocks(study):
    all_nodes=nodes(study); active=False; allowed=set()
    for i,n in enumerate(all_nodes):
        if n.get('class','').startswith('Head2'):active=txt(n)=='Model Definition'
        if active:allowed.add(i)
    retained=[];excluded=[]
    # Start with the already-audited numerical-answer exclusions.
    for i,n in selected(study)[0]:
        if i not in allowed:continue
        text=txt(n); cl=n.get('class','')
        # No CAD construction, UI recipe, or mesh recipe is supplied in this track.
        if re.search(r'\b(click|toolbar|model wizard|settings window|model builder|insert sequence)\b',text,re.I):
            excluded.append(i);continue
        if re.search(r'(^Figure \d+:.*\bmesh\b|^Finite [Ee]lement [Mm]esh$|^Mesh$)',text):
            excluded.append(i)
            if retained and not txt(retained[-1][1]) and any(x.tag.split('}')[-1]=='img' for x in retained[-1][1].iter()):excluded.append(retained.pop()[0])
            continue
        retained.append((i,n))
    if study['id']=='FEMCAD-ADV-030':
        # Original pure geometry view: retain image bytes, not the surrounding recipe.
        image_only=ET.Element('div')
        for image in all_nodes[60].iter():
            if image.tag.split('}')[-1]!='img':continue
            clone=copy.deepcopy(image);clone.tail=None;image_only.append(clone)
        assert len(image_only)>0
        retained.append((60,image_only))
    return retained,excluded


def input_text_file(name):
    if not name.endswith('.txt'):return False
    # Source scalar parameters/material laws/loads/physical expressions only.
    return any(x in name for x in ('parameters','properties','variables','_function','_disp','_Rb','_Lb','_HBFe')) or name=='piezoelectric_rate_gyroscope_geom_sequence.txt'


def main():
    rows=[json.loads(l) for l in (DATA/'advanced-tasks.jsonl').read_text().splitlines()]
    studies=json.loads((DATA/'reference-assets.json').read_text())['studies']
    old_report=json.loads((DATA/'input-packaging-report.json').read_text())
    old_status={r['id']:r for r in old_report['studies']}
    stage=OUT.with_name(OUT.name+'-staging')
    if stage.exists():shutil.rmtree(stage)
    stage.mkdir();records=[]
    for row,study in zip(rows,studies):
        sid=row['id']; assert sid==study['id']; number=int(sid[-3:])
        dst=stage/'candidate-inputs'/sid;dst.mkdir(parents=True)
        ref=json.loads((ASSISTED/'held-out'/sid/'reference.json').read_text())
        assert sha(ROOT/study['documentation_screen']['local_tutorial'])==ref['source_page']['sha256'], 'Source changed; re-audit extraction'
        keep,excluded=problem_blocks(study)
        image_index={i['url']:i for i in ref['candidate_provenance'] if i['path'].startswith('images/')}
        imagemap={};prov=[]
        for url,evidence in image_urls(study,keep).items():
            info=image_index[url];src=ASSISTED/'model-inputs'/sid/info['path']
            assert sha(src)==info['sha256']
            target=dst/info['path'];target.parent.mkdir(exist_ok=True);shutil.copy2(src,target)
            imagemap[evidence['original_src']]=info['path'];prov.append(info)
        textfiles=[]
        for src in sorted((ASSISTED/'model-inputs'/sid/'assets').glob('*')):
            if input_text_file(src.name):
                rel='specifications/'+src.name;(dst/rel).parent.mkdir(exist_ok=True)
                shutil.copy2(src,dst/rel);textfiles.append(src.name)
                origin=next(p for p in ref['candidate_provenance'] if p['path']=='assets/'+src.name)
                prov.append({**origin,'path':rel})
        body=''.join(render(n,imagemap) for _,n in keep)
        body=body.replace('Modeling Instructions','[source recipe omitted]')
        (dst/'problem.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>'+html.escape(row['title'])+'</title><style>body{max-width:1050px;margin:2em auto;font:16px/1.5 sans-serif}img{max-width:100%}td,th{border:1px solid #ccc;padding:5px}</style></head><body><h1>'+html.escape(row['title'])+'</h1>'+body+'</body></html>')
        requirements={
          'cad_source':'Editable model or complete construction code, authored from the supplied drawings/specifications.',
          'cad':'STEP geometry with explicit units, declared 2D/axisymmetric/shell/3D formulation and named physical regions.',
          'mesh':'Solver-readable mesh generated from the submitted CAD; include boundary/material groups and CAD-to-mesh mapping.',
          'solver_input':'Runnable FEM input/code using that mesh with source material laws, loads, contacts, constraints and coupling.',
          'results':'Machine-readable computed fields/curves/scalars with units, coordinates/load steps and definitions.',
          'solver_log':'Unedited solver log, solver/version and actual convergence status.',
          'provenance':'submission.json identifies artifact paths and SHA-256 hashes, mesh parent CAD hash and solver parent mesh hash. Candidate declarations require independent replay.',
        }
        manifest={'id':sid,'title':row['title'],'track':'joint-cad-plus-fem',
          'instructions':'Construct CAD from problem.html and the permitted specifications. Mesh and run FEM on YOUR submitted CAD. Return the required artifacts. Do not import the published CAD, copy published FEM answers, or invent missing dimensions/material data. Identify missing inputs explicitly. Preserve the source dimensional formulation; a 2D or shell study does not require an invented 3D solid.',
          'requested_outputs':row['outputs'],'required_artifacts':requirements,
          'reference_comparisons':'Return your computed outputs. Any comparison with a published answer mentioned in the output description is performed privately by the evaluator.',
          'submission_schema':json.loads((DATA/'joint-submission.schema.json').read_text()),
          'candidate_access':'One task only; fresh context; network disabled; no access to project files, other tasks, source tutorials or held-out data.',
          'status':'draft-not-released','scored_evaluation_ready':False,
          'files':[{'path':p.relative_to(dst).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(dst.rglob('*')) if p.is_file()]}
        save(dst/'task.json',manifest)
        blockers=list(old_status[sid]['blocking_issues'])
        blockers += ['Drawing/dimension and physics-input completeness not certified after removing construction recipes and CAD.',
                     'Independent geometry reference and geometric acceptance criteria not yet exported/validated.',
                     'Per-output numerical targets, acceptance tolerances and a trusted execution adapter are not yet validated.']
        record={'id':sid,'status':'draft-not-released','drawing_review_priority':number in DIMENSIONED,
          'geometry_sufficiency':'unverified','physics_sufficiency':'unverified',
          'review_note':SPECIAL.get(number,'Source model-definition drawings/specifications retained; CAD import dependencies and every unconstrained feature need a dimensional audit.'),
          'blockers':blockers,'input_images':len(imagemap),'input_text_files':textfiles,
          'candidate_manifest':str((OUT/'candidate-inputs'/sid/'task.json').relative_to(ROOT)),
          'private_reference_manifest':str((ASSISTED/'held-out'/sid/'reference.json').relative_to(ROOT)),
          'source_url':study['source_url'],'source_blocks':[i for i,n in keep],'additional_removed_blocks':excluded,'provenance':prov}
        records.append(record)
        # Private scoring contract deliberately contains no invented numerical thresholds.
        save(stage/'evaluator-only'/sid/'contract.json',{'task_id':sid,'release_approved':False,
          'source_reference_manifest':record['private_reference_manifest'],
          'geometry':{'reference':None,'criteria':None,'status':'not_validated'},
          'physics':{'criteria':None,'status':'not_validated'},
          'numerical':{'targets':None,'tolerances':None,'status':'not_validated'},
          'pass_rule':'CAD correctness AND physics correctness AND convergence AND numerical agreement, on the same independently replayed CAD-to-mesh-to-solver chain. No weighted score can compensate for a failed stage.',
          'blockers':blockers})
    if OUT.exists():
        backup=OUT.with_name(OUT.name+'-previous')
        if backup.exists():shutil.rmtree(backup)
        OUT.rename(backup)
    stage.rename(OUT)
    catalog={'track':'joint-cad-plus-fem','studies':50,'candidate_drafts':50,'released_for_scoring':0,
      'priority_drawing_reviews':len(DIMENSIONED),'rows':records}
    save(DATA/'joint-benchmark.json',catalog)
    for row in rows:
        row['joint_benchmark']={'manifest':str((OUT/'candidate-inputs'/row['id']/'task.json').relative_to(ROOT)),
                                'track':'joint-cad-plus-fem','scored_evaluation_ready':False}
    (DATA/'advanced-tasks.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n')
    print(json.dumps({k:v for k,v in catalog.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
