"""Snapshot additional primary sources; download no training/test corpora."""
import concurrent.futures
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
('cadengbench','CADEngBench','https://arxiv.org/html/2608.09296v1','functional edits, parametric behavior, engineering/DFM, FEA and assembly; direct overlap'),
('benchcad','BenchCAD','https://benchcad.com/','industrial parametric code and edits; released links; reserve benchmark designs'),
('vectorbench','Vector-Bench','https://github.com/yug-space/vector-edit-gym','SVG repair plus preservation; code MIT, scenic assets unresolved provenance'),
('cadworld','CADWorld','https://arxiv.org/html/2609.16251v1','FreeCAD GUI workflows including technical drawings and FEM; benchmark comparator'),
('bim_edit','BIM-Edit','https://arxiv.org/html/2606.20146v1','building edits with geometry, semantics and topology; architectural comparator'),
('cadtestbench','CADTestBench','https://github.com/dimitrismallis/CADTestBench','executable requirement tests and generation guidance; released MIT code/HF data links'),
('physics_in_loop','Physics-in-the-Loop','https://arxiv.org/abs/2605.19717','verified engineering tools in closed-loop CAD agents; release promised, not downloaded'),
('muse','MUSE','https://dong7313.github.io/muse-benchmark/','manufacturable/functional/assemblable CAD, design-intent rubric; external test'),
('itercad','IterCAD','https://arxiv.org/abs/2606.13368','drawing/text/edit CAD agent, multiview synthesis, SFT and geometry-aware RL'),
('omnimech','OmniMech','https://omnimech.dev/','dimensioned drawings/CAD/annotations, cross-view and tool tracks; download links failed in audit'),
('nist_pmi','NIST PMI/GD&T implementation testing','https://www.nist.gov/publications/testing-implementations-geometric-dimensioning-and-tolerancing-cad-software','representation versus graphical presentation correctness predates LLMs'),
('parametric_cadbench','Parametric CAD Bench v2','https://cadbench.ai/','100 FreeCAD tasks; published Astra agentic scores not comparable to unaided SVG'),
('svgeditbench_v2','SVGEditBench V2','https://arxiv.org/abs/2502.19453','instruction-based SVG edits from emoji pairs; baseline overlap'),
('cad_ag','CAD-AG','https://scholars.duke.edu/publication/1703509','rule-based geometric grading of engineering DXF drawings; verifier prior art')]

def main():
 out=ROOT/'reports/cad-overlap-source-audit-20260920';out.mkdir(exist_ok=True)
 def fetch(item):
  key,name,url,note=item;rec=dict(id=key,name=name,url=url,note=note,retrieved_utc=datetime.now(timezone.utc).isoformat())
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 CAD literature research'})
   with urllib.request.urlopen(req,timeout=35) as r:body=r.read();rec['resolved_url']=r.url
   path=out/(key+'.html');path.write_bytes(body);rec.update(status='downloaded',bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),file=path.name)
  except Exception as e:rec.update(status='unavailable',error_type=type(e).__name__)
  return rec
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,SOURCES))
 (out/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
 p=ROOT/'data/cad_sources.json';registry=json.loads(p.read_text());existing={x['id'] for x in registry['sources']}
 for key,name,url,note in SOURCES:
  if key not in existing:registry['sources'].append(dict(id=key,name=name,url=url,proposed_role='prior_art_or_external_eval',access_evidence=note,downloaded=False,training_used=False,license_note='See primary source; paper or project access is not a training-data license.'))
 registry['overlap_followup']='reports/CAD_NOVELTY_OVERLAP_20260920.md';p.write_text(json.dumps(registry,indent=2)+'\n')
 print('Sources:',len(registry['sources']),'new snapshots:',sum(r['status']=='downloaded' for r in records),'/',len(records))
if __name__=='__main__':main()
