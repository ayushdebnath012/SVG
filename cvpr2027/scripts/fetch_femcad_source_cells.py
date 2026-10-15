"""Fetch authoritative cells where captions omit code or hide dependencies.

Default fetches abbreviated, import/material-lookup and case-selector cells.
--all-selected fetches every focused cell. Uses only allowed official hosts.
Source text stays in ignored tmp/; metadata and dependency inventory are public.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
from build_femcad_source_dataset import ROOT, OUT, allowed

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--all-selected',action='store_true');args=ap.parse_args()
    pages=json.loads((OUT/'sources.json').read_text())['pages']
    by_url={p['url']:p for p in pages}
    tasks=list(map(json.loads,(OUT/'tasks.jsonl').read_text().splitlines()))
    selected={};selectors={}
    for r in tasks:
        u=r['source']['url'];selected.setdefault(u,set()).update(r['source']['focus_cell_indices'])
        if 'source_cell_index' in r['source_case']: selectors.setdefault(u,set()).add(r['source_case']['source_cell_index'])
        geometry_url=r['source']['geometry_url']
        if geometry_url != u:
            selected.setdefault(geometry_url,set()).update(c['index'] for c in by_url[geometry_url]['cells'])
    dest=ROOT/'tmp/femcad-source-cells';dest.mkdir(exist_ok=True)
    jobs=[]
    for page in pages:
        captions=BeautifulSoup((ROOT/page['cached_html']).read_bytes(),'html.parser').select('figure.figure-input')
        for c in page['cells']:
            idx=c['index'];code=captions[idx].get_text()
            if idx in selected.get(page['url'],set()) and (args.all_selected or c['caption_is_abbreviated'] or re.search(r'Import\[|Entity\[|ThermodynamicData|MaterialData|ElementData|ChemicalData',code) or idx in selectors.get(page['url'],set())):
                jobs.append(dict(page_url=page['url'],**c))
    def fetch(c):
        u=c['url'];assert allowed(u)
        p=dest/(hashlib.sha256(u.encode()).hexdigest()+'.txt')
        r=dict(page_url=c['page_url'],index=c['index'],url=u,cache=str(p.relative_to(ROOT)))
        for attempt in range(2):
            try:
                if not p.exists():
                    req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research source catalog)'})
                    with urllib.request.urlopen(req,timeout=25) as response:
                        assert allowed(response.url),response.url
                        data=response.read()
                    if data.lstrip().lower().startswith((b'<!doctype',b'<html')):raise ValueError('HTML returned instead of source cell')
                    p.write_bytes(data)
                data=p.read_bytes();code=data.decode('utf-8')
                r.update(status='fetched',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),checked_utc=datetime.now(timezone.utc).isoformat(),
                         support_files=sorted(set(re.findall(r'"([^"\n]+\.(?:stl|wxf|wdx|mx|xls|xlsx|csv|msh))"',code,re.I))),
                         runtime_data_lookup=bool(re.search(r'Entity\[|ThermodynamicData|MaterialData|ElementData|ChemicalData',code)),
                         installation_dependency='$InstallationDirectory' in code)
                return r
            except Exception as e:
                r.update(status='error',error=f'{type(e).__name__}: {e}')
                if attempt==0:time.sleep(.5)
        return r
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for r in pool.map(fetch,jobs):
            results.append(r)
            if len(results)%25==0:print(f'{len(results)}/{len(jobs)} source cells checked',flush=True)
    results.sort(key=lambda r:(r['page_url'],r['index']))
    manifest=dict(scope='all selected cells' if args.all_selected else 'abbreviated, import/material-lookup and case-selector cells',
                  selected_cell_count=sum(map(len,selected.values())),attempted=len(results),fetched=sum(r['status']=='fetched' for r in results),cells=results)
    (OUT/'cell-fetch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    deps=[{'page_url':r['page_url'],'cell_index':r['index'],'code_url':r['url'],'support_files':r.get('support_files',[]),'runtime_data_lookup':r.get('runtime_data_lookup',False),'installation_dependency':r.get('installation_dependency',False)} for r in results if r.get('support_files') or r.get('runtime_data_lookup') or r.get('installation_dependency')]
    (OUT/'dependencies.json').write_text(json.dumps({'status':'identified, not resolved or bundled','entries':deps},indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='cells'}))
    if any(r['status']=='error' for r in results):raise SystemExit(1)
if __name__=='__main__':main()
