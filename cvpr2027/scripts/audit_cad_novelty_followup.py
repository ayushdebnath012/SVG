"""Additional primary-source novelty audit, including negative overlap evidence."""
import concurrent.futures,hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
('cadir','CADIR','https://arxiv.org/html/2608.00891v1','Explicit construction graph, parameter dependencies, constraints, topology references and cross-backend feature history; a dependency IR is not new.'),
('svg360','SVG360: Editable Multiview Vector Graphics from a Single SVG','https://arxiv.org/html/2511.16766v3','Cross-view SVG part identity and editable vector assets; evaluates perceptual continuity and vector/palette stability, not dimensioned engineering edit correctness.'),
('artifact_coevolution','Change-aware round-trip benchmarking of LLMs','https://www.sciencedirect.com/science/article/pii/S0164121226002475','Coupled class models and relational schemas, controlled edits and round-trip consistency. Generic cross-artifact co-evolution is not new. Online source accessed Sept 2026; issue date Nov 2026.'),
('redlinebench','RedlineBench','https://redlinebench.benfeicht.com/','Public architectural drawing-review project; issue identification, consistency and false alarms. Not a verified peer-reviewed publication.'),
('fmforme','FMforME','https://www.mdpi.com/2076-3417/16/15/7396','Runtime engineering constraint predicates, structured correction and Fusion execution; external-verifier repair is not new.'),
('mt_lapr','MT-LAPR','https://arxiv.org/abs/2410.07516','Semantics-preserving program transformations expose repair instability; readability preprocessing improves robustness. Neither metamorphic testing nor canonicalization is new.'),
('mt_llm_nlp','Metamorphic Testing of LLMs for NLP','https://arxiv.org/abs/2511.02108','191 collected metamorphic relations and 36 evaluated; general consistency testing has extensive prior art.'),
('linewise_designlab','LineWise Design Lab','https://www.linewise.io/designlab.html','Commercial benchmark proposal covers edits, locality, constraints, manufacture and expert assessment; no downloaded public training corpus.'),
('mm_svgedit','MM-SVGEdit','https://arxiv.org/html/2609.06116v1','Visual element grounding followed by function-based localized SVG modification for UI design; locator-plus-executor alone is not new.'),
('cad_associativity','Classical CAD drawing associativity','https://care.dptlab.com/Content/Help/language/drawing/OVfile/T_OV_associativity.htm','Vendor documentation: CAD drawing views and associative added geometry already update with model changes.')]

def main():
 out=ROOT/'reports/cad-novelty-source-audit-20260920';out.mkdir(exist_ok=True)
 def fetch(item):
  key,name,url,note=item;r=dict(id=key,name=name,url=url,note=note,retrieved_utc=datetime.now(timezone.utc).isoformat())
  try:
   existing=out/(key+'.html')
   if existing.exists():
    body=existing.read_bytes();r.update(status='downloaded',sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),reused_snapshot=True);return r
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=35) as response:body=response.read();r['resolved_url']=response.url
   (out/(key+'.html')).write_bytes(body);r.update(status='downloaded',sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
  except Exception as e:r.update(status='snapshot_unavailable',error_type=type(e).__name__,note=note+' Reviewed through web tool; local snapshot failed.')
  return r
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:records=list(p.map(fetch,SOURCES))
 (out/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
 p=ROOT/'data/cad_sources.json';d=json.loads(p.read_text());known={s['id'] for s in d['sources']}
 for key,name,url,note in SOURCES:
  if key not in known:d['sources'].append(dict(id=key,name=name,url=url,proposed_role='novelty_overlap',access_evidence=note,downloaded=False,training_used=False,license_note='Paper/project review; no training rights inferred.'))
 for s in d['sources']:
  if s['id']=='benchcad':s.update(downloaded=True,training_used=False,access_evidence='110 held-out edit records fetched from official Hugging Face dataset server, with source/target code and STEP. Four audited derivatives used for discovery; never training. Target inconsistencies documented.',pilot_manifest='cad-native-probe/tasks.json')
 d['novelty_followup']='reports/CAD_NATIVE_AND_NOVELTY_20260920.md';p.write_text(json.dumps(d,indent=2)+'\n')
 print(len(d['sources']),'sources;',sum(r['status']=='downloaded' for r in records),'new snapshots')
if __name__=='__main__':main()
