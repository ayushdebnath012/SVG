"""Archive the five additional primary sources reviewed on 21 September."""
import concurrent.futures
import hashlib
import json
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
 ('vitruvion','Vitruvion','https://lips.cs.princeton.edu/vitruvion/',
  'Official ICLR 2022 project: primitive/constraint generation and constraint inference from geometry. Lost constraint recovery is prior art.','official_project'),
 ('cit_cad','CIT-CAD','https://arxiv.org/html/2609.07434v1',
  'Primary preprint reviewed: explicit intent tree, deterministic expected/actual constraints and localized repair. Intent verification and preserving satisfied constraints are prior art.','preprint_fulltext'),
 ('procad','ProCAD: Clarify Before You Draw','https://arxiv.org/html/2602.03045v1',
  'Primary paper reviewed: targeted clarification for underspecified or contradictory text-to-CAD prompts, followed by CadQuery generation. Asking only necessary questions is prior art.','preprint_fulltext'),
 ('depthbenchcad','DepthBenchCAD','https://github.com/HongyeYangGT/DepthBenchCAD',
  'Public repository README reviewed: counterfactual CAD edit states and audit allocation. Candidate programs, prompts and provider telemetry are not in its stated public release. Performance and publication status not independently reproduced.','public_repository'),
 ('wrong_design_intent','Wrong Design Intent Is Worse Than None','https://arxiv.org/html/2607.23191v1',
  'Primary preprint reviewed: correct/wrong/masked CAD headers, independent geometry metrics and a shuffled-header training control. Causal intent intervention alone is not novel.','preprint_fulltext'),
]


def main():
    out=ROOT/'reports/cad-foundation-source-audit-20260921';out.mkdir(exist_ok=True)
    def fetch(s):
        key,name,url,note,level=s
        row=dict(id=key,name=name,url=url,review_level=level,note=note,
                 retrieved_utc=datetime.now(timezone.utc).isoformat())
        p=out/(key+'.html')
        try:
            if not p.exists():
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:
                    p.write_bytes(r.read());row['resolved_url']=r.url
            raw=p.read_bytes()
            row.update(snapshot='downloaded',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        except Exception as e:row.update(snapshot='unavailable',error_type=type(e).__name__)
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,SOURCES))
    (out/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    p=ROOT/'data/cad_sources.json';data=json.loads(p.read_text());known={s['id'] for s in data['sources']}
    for key,name,url,note,level in SOURCES:
        if key not in known:data['sources'].append(dict(id=key,name=name,url=url,
            proposed_role='novelty_overlap',access_evidence=note,review_level=level,
            downloaded=False,training_used=False,
            license_note='Literature snapshot is not a training-data license.'))
    data['audit_date']='2026-09-21'
    data['foundation_report']='reports/PROJECT_FOUNDATION_20260921.md'
    p.write_text(json.dumps(data,indent=2)+'\n')
    print(len(data['sources']),'sources;',sum(r['snapshot']=='downloaded' for r in records),'snapshots')


if __name__=='__main__':main()
