#!/usr/bin/env python3
"""Split existing COMSOL tutorials; never synthesize FEM data or modify source binaries.

Run from any directory. Source hashes pin node-index redactions to audited documents.
The output is preparation material, not a numerically validated benchmark.
"""
import argparse
import copy
import hashlib
import html
import json
import re
import shutil
import time
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/femcad-hard-v1'
OUT = ROOT / 'tmp/femcad-evaluation'
CACHE = ROOT / 'tmp/femcad-evaluation-cache'
HELD_NAMES = {'perforated_muffler_exp_data.txt', 'sheet_metal_forming.txt',
              'composite_dome_tweeter_freq_Lp_data.txt', 'composite_dome_tweeter_freq_Z_data.txt'}
# Half-open ranges of direct XHTML document blocks. These remove reference data,
# optional solved-model shortcuts, and postprocessing outside Results headings.
REDACTIONS = {
  5: [(73,82)], 10: [(578,588)], 11: [(51,52)], 21: [(17,20)],
  26: [(78,120),(697,711)], 30: [(6,7)], 40: [(13,15)],
  43: [(65,66)], 44: [(891,918)],
}
# Only removal of exact source text; no replacement engineering claims or values.
SENTENCES = {
  33: ['With this structure, the resonant frequency of the device is 870 MHz.'],
  42: ['At the resonance frequency of 9 kHz, δv takes the value of 23.2 μm, on the same order of magnitude as the gap.'],
}
BASE_MODELS = {
  3: 'turbine_stator', 18: 'comb_drive_tuning_fork_gyroscope',
  26: 'composite_dome_tweeter_eigen (homogenized materials)',
  29: 'cohesive_zone_debonding', 30: 'sports_car (LES forcing)',
  31: 'motherboard_shock_response',
}
# Head3 sections outside Results which actually belong to postprocessing.
POST_HEADS = ('result', 'table ', 'stress intensity, maximum', 'energy evaluation',
              'new method', 'methods', 'model builder')
FILE_RE = re.compile(r'(?<![\w.-])([A-Za-z0-9][\w.-]*\.(?:mphbin|mph|txt|x_b|csv|step|stp))\b', re.I)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')


def txt(node):
    return ' '.join(''.join(node.itertext()).split())


def nodes(study):
    tree = ET.parse(ROOT / study['documentation_screen']['local_tutorial'])
    return list(max(tree.find('{*}body').findall('./{*}div'), key=lambda n:len(''.join(n.itertext()))))


def fetch(url, dest):
    if dest.exists(): return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            if 'text/html' in response.headers.get('Content-Type',''): raise ValueError('HTML instead of asset')
            temp = dest.with_suffix(dest.suffix+'.partial')
            temp.write_bytes(response.content)
            temp.replace(dest)
            return dest
        except (requests.RequestException, ValueError):
            if attempt == 2: raise
            time.sleep(attempt+1)


def selected(study):
    num = int(study['id'][-3:]); picked=[]; removed=[]; mode=False; post=False
    for i, original in enumerate(nodes(study)):
        text = txt(original); cls=original.get('class','')
        if cls.startswith('Head2'):
            mode = (text == 'Model Definition' or 'Modeling Instructions' in text or
                    'Geometry' in text and 'Instructions' in text or
                    text == 'Mapping, Multiphysics, and Acoustics')
            post=False
        elif cls.startswith('Head3') and mode:
            post = text.lower().startswith(POST_HEADS) or not text.strip()
        reason = None
        if not mode: reason='outside model-definition/setup/geometry sections'
        elif post: reason='postprocessing/results section'
        elif any(a<=i<b for a,b in REDACTIONS.get(num, [])): reason='audited reference/shortcut/postprocessing exclusion'
        # These identify source navigation rather than task content.
        elif 'Application Library path:' in text or text.startswith('Application Library path'): reason='source navigation'
        if reason:
            removed.append({'block':i,'reason':reason,'text':text});continue
        n=copy.deepcopy(original)
        for sentence in SENTENCES.get(num,[]):
            if sentence in text:
                # Source formatting may split a sentence across inline elements.
                flat=txt(n)
                n.clear();n.tag='p';n.text=flat.replace(sentence,'').strip()
                removed.append({'block':i,'reason':'published numerical outcome sentence','text':sentence})
        picked.append((i,n))
    return picked,removed


def image_urls(study, selected_nodes):
    result={}
    for i,n in selected_nodes:
        for im in n.iter():
            if im.tag.split('}')[-1]!='img':continue
            # Toolbar icons are not equations. Retain all other source images.
            if im.get('width')=='28' and im.get('height')=='28':continue
            url=urllib.parse.urljoin(study['source_url'],im.get('src',''))
            result[url]={'block':i,'original_src':im.get('src')}
    return result


def render(node, imgmap):
    tag=node.tag.split('}')[-1]
    if tag in {'script','style','iframe','object','embed'}:return ''
    if tag=='img':
        if node.get('width')=='28' and node.get('height')=='28':return ''
        src=imgmap.get(node.get('src'))
        if not src:return ''
        return '<img src="'+html.escape(src,quote=True)+'" alt="Original source figure or equation" />'
    cls=node.get('class','')
    if cls.startswith('Head2'): tag='h2'
    elif cls.startswith('Head3'): tag='h3'
    elif cls.startswith('Head4'): tag='h4'
    elif tag not in {'p','div','span','table','thead','tbody','tr','td','th','sub','sup','b','i','em','strong','br','ul','li'}:tag='span'
    attrs=''
    for key in ('colspan','rowspan'):
        if node.get(key):attrs+=' '+key+'="'+html.escape(node.get(key),quote=True)+'"'
    content=html.escape(node.text or '')
    for c in node:content+=render(c,imgmap)+html.escape(c.tail or '')
    # Source URLs are held out even if written as plain text.
    content=re.sub(r'https?://[^\s<>]+','[source link withheld]',content)
    return '<'+tag+attrs+'>'+content+'</'+tag+'>'


def safe_file(file):
    name=file['name']
    if name in HELD_NAMES:return False
    if name=='loudspeaker_driver_materials.mph':return True
    return file['role']=='geometry_or_mesh_model' or (
        file['role']=='supporting_file' and Path(name).suffix.lower() in {'.txt','.mphbin','.x_b','.step','.stp','.csv'})


def binary_check(path):
    if path.suffix=='.mph':
        with zipfile.ZipFile(path) as z:
            bad=[n for n in z.namelist() if re.search(r'(^|/)(solution|plot|table)\w*\.(mphbin|xml)$',n,re.I)]
        if bad:raise ValueError(f'Potential answer entries in {path.name}: {bad}')


def build():
    source=json.loads((DATA/'advanced-source-studies.json').read_text())
    assets=json.loads((DATA/'reference-assets.json').read_text())
    rows=[json.loads(x) for x in (DATA/'advanced-tasks.jsonl').read_text().splitlines()]
    studies=assets['studies']; pages={p['url']:p for p in source['pages']}
    known={}
    for row in rows:
        for f in row['figures']:
            assert sha(ROOT/f['local']) == f['sha256']
            known[f['url']]=ROOT/f['local']
    selections={}; jobs={}; exceptions={}
    for s in studies:
        page=pages[s['source_url']]
        assert sha(ROOT/page['local'])==page['sha256'], 'Source changed; review redaction indices'
        keep,rem=selected(s); selections[s['id']]=(keep,rem)
        for url in image_urls(s,list(enumerate(nodes(s)))):
            if url not in known:
                dest=CACHE/'images'/(hashlib.sha256(url.encode()).hexdigest()+'.png');jobs[url]=dest
        for f in s['files']:
            if safe_file(f) and not f.get('local'):
                jobs[f['url']]=CACHE/'files'/s['id']/f['name']
    print(f'Fetching {len(jobs)} original images/dependencies',flush=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(fetch,url,dest):url for url,dest in jobs.items()}
        for future in as_completed(futures):
            url=futures[future]
            try:known[url]=future.result()
            except Exception as e:exceptions[url]=str(e)
    # All content is built in a new staging directory; old packages stay intact on failure.
    stage=OUT.with_name(OUT.name+'-staging')
    if stage.exists():shutil.rmtree(stage)
    stage.mkdir(parents=True)
    report=[]; inputs=[]
    for s,row in zip(studies,rows):
        assert s['id']==row['id']; sid=s['id'];num=int(sid[-3:])
        target=stage/'model-inputs'/sid;held=stage/'held-out'/sid
        target.mkdir(parents=True);held.mkdir(parents=True)
        keep,removed=selections[sid]; issues=[];provenance=[];imgmap={}
        for url,im in image_urls(s,keep).items():
            src=known.get(url)
            if not src:issues.append('Missing source image: '+im['original_src']);continue
            rel='images/'+hashlib.sha256(url.encode()).hexdigest()[:16]+'.png'
            (target/rel).parent.mkdir(exist_ok=True);shutil.copy2(src,target/rel)
            imgmap[im['original_src']]=rel
            provenance.append({'path':rel,'url':url,'sha256':sha(src),'source_block':im['block']})
        files=list(s['files'])
        if num==40:
            files += [f for f in studies[38]['files'] if f['name']=='loudspeaker_driver_materials.mph']
        support=[]
        for f in files:
            if not safe_file(f):continue
            src=ROOT/f['local'] if f.get('local') else known.get(f['url'])
            if src is None or not src.exists():issues.append('Missing dependency: '+f['name']);continue
            if f.get('sha256'):assert sha(src)==f['sha256']
            try:binary_check(src)
            except ValueError as e:issues.append(str(e));continue
            rel='assets/'+f['name'];(target/rel).parent.mkdir(exist_ok=True)
            shutil.copy2(src,target/rel);support.append(f['name'])
            provenance.append({'path':rel,'url':f['url'],'sha256':sha(src),'source_version':f.get('version')})
        if num in BASE_MODELS:issues.append('Required companion model not supplied as an answer-free input: '+BASE_MODELS[num])
        if num==2:issues.append('Source voltage ambiguity: model definition and published result caption use different voltages; evaluation condition needs adjudication')
        if num==17:issues.append('Source initial void fraction is inconsistent: model-definition table has 0.4; material setup table has 0.6. Requires source-model adjudication.')
        body='\n'.join(render(n,imgmap) for _,n in keep)
        (target/'problem.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>'+html.escape(row['title'])+'</title><style>body{max-width:1100px;margin:2em auto;font:16px/1.5 sans-serif}img{max-width:100%;height:auto}td,th{padding:5px;border:1px solid #bbb}table{border-collapse:collapse}h2,h3{margin-top:1.5em}</style></head><body><h1>'+html.escape(row['title'])+'</h1>'+body+'</body></html>')
        text='\n'.join(txt(n) for _,n in keep)
        refs=sorted(set(FILE_RE.findall(text)))
        missing=[n for n in refs if n not in support and n not in {'aluminum_extrusion_fsi_geom_sequence.mph'}]
        for name in missing:issues.append('Referenced file not in candidate assets: '+name)
        # Copy source material only into the private reference package.
        shutil.copy2(ROOT/s['documentation_screen']['local_tutorial'],held/'original-tutorial.html')
        refmap={}; ref_image_provenance=[]
        for url,im in image_urls(s,list(enumerate(nodes(s)))).items():
            src=known.get(url)
            if src is None:continue
            rel='images/'+hashlib.sha256(url.encode()).hexdigest()[:16]+'.png'
            (held/rel).parent.mkdir(exist_ok=True);shutil.copy2(src,held/rel)
            refmap[im['original_src']]=rel
            ref_image_provenance.append({'path':rel,'url':url,'sha256':sha(src)})
        (held/'reference.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>Held-out source reference</title></head><body>'+''.join(render(n,refmap) for n in nodes(s))+'</body></html>')
        local_refs=[]
        for f in s['files']:
            if safe_file(f) or not f.get('local'):continue
            src=ROOT/f['local'];rel='assets/'+f['name'];(held/rel).parent.mkdir(exist_ok=True)
            shutil.copy2(src,held/rel);local_refs.append(rel)
        for j,fig in enumerate(row['figures']):
            src=ROOT/fig['local'];rel=f'catalog-figures/{j+1:02d}'+src.suffix
            (held/rel).parent.mkdir(exist_ok=True);shutil.copy2(src,held/rel)
        save(held/'reference.json',{'source_row':row,'source_page':pages[s['source_url']],
            'original_tutorial':'original-tutorial.html','offline_reference':'reference.html',
            'reference_image_provenance':ref_image_provenance,'local_reference_files':local_refs,
            'candidate_provenance':provenance,'removed_source_blocks':removed,
            'included_source_blocks':[i for i,n in keep],
            'limitations':['Most solved MPH models are remote references, not offline numerical arrays.','No numerical tolerance or convergence certification has been invented.']})
        manifest={'id':sid,'title':row['title'],'track':'source-assisted FEM reproduction with published setup and supplied geometry',
            'problem':'problem.html','asset_directory':'assets','image_directory':'images',
            'requested_outputs':row['outputs'],
            'instructions':'Use problem.html and the supplied files to implement the source-described geometry and FEM analysis. Supplied geometry may be imported. Return reproducible model/code and computed outputs with solver logs. Report any unavailable prerequisite; do not substitute invented values. Files named by the tutorial are under assets/.',
            'input_packaging_status':'blocked' if issues else 'packaged',
            'blocking_issues':issues,'numerical_evaluation_ready':False,
            'semantic_review':'Source sections and specific answer passages filtered; independent final review required before a scored release.',
            'runtime_requirements':'Matching COMSOL '+s.get('tutorial_version','')+' installation, relevant licensed physics modules, material libraries and part libraries; not bundled.',
            'isolation':'Supply this task directory only, in a fresh context with no network or access to sibling tasks, catalogs or held-out files. Some task inputs are outputs of another task.',
            'protocol_limits':'Published solver settings, geometry and prescribed sampling locations are supplied. This is source-assisted reproduction, not unaided geometry or solver-method discovery.',
            'files':[{'path':p.relative_to(target).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(target.rglob('*')) if p.is_file()]}
        save(target/'task.json',manifest); inputs.append({'id':sid,'directory':sid,'status':manifest['input_packaging_status']})
        report.append({'id':sid,'input_packaging_status':manifest['input_packaging_status'],'blocking_issues':issues,
            'source_blocks_included':len(keep),'source_blocks_withheld':len(removed),
            'source_images':len(imgmap),'supporting_files':support,'referenced_input_filenames':refs})
    save(stage/'model-inputs/manifest.json',{'scope':'50 candidate preparation packages; consult each task status. No held-out answers are included.','tasks':inputs})
    summary={'studies':len(report),'packaged_without_known_dependency_blockers':sum(not r['blocking_issues'] for r in report),
             'blocked':sum(bool(r['blocking_issues']) for r in report),'input_images':sum(r['source_images'] for r in report),
             'input_file_copies':sum(len(r['supporting_files']) for r in report),'numerically_gradeable':0}
    save(stage/'packaging-report.json',{'counts':summary,'studies':report,'download_failures':exceptions})
    save(stage/'held-out/source-catalog.json',assets)
    if OUT.exists():
        backup=OUT.with_name(OUT.name+'-previous')
        if backup.exists():shutil.rmtree(backup)
        OUT.rename(backup)
    stage.rename(OUT)
    save(DATA/'input-packaging-report.json',{'counts':summary,'artifact_root':OUT.relative_to(ROOT).as_posix(),'studies':report,'download_failures':exceptions})
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':build()
