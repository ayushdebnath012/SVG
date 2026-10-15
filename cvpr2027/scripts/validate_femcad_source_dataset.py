"""Validate provenance and case selection, without claiming a FEM solver pass."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from build_femcad_source_dataset import ROOT, OUT, allowed

def main():
    rows=[json.loads(line) for line in (OUT/'tasks.jsonl').read_text().splitlines()]
    pages={p['url']:p for p in json.loads((OUT/'sources.json').read_text())['pages']}
    source_images={};captions={}
    for u,p in pages.items():
        assert allowed(u)
        raw=(ROOT/p['cached_html']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==p['html_sha256'],u
        soup=BeautifulSoup(raw,'html.parser')
        source_images[u]={urljoin(u,e[a]) for e in soup.find_all(True) for a in ('src','data-src') if e.get(a)}
        captions[u]=[e.get_text() for e in soup.select('figure.figure-input code')]
    assert len(rows)==100 and len({r['id'] for r in rows})==100
    assert len({r['prompt'] for r in rows})==100
    split_for_family={}
    for r in rows:
        u=r['source']['url'];g=r['source']['geometry_url'];p=pages[u]
        assert r['source']['html_sha256']==p['html_sha256']
        assert r['figures']
        for f in r['figures']:
            assert allowed(f['url'])
            assert f['url'] in source_images[u]|source_images[g],(r['id'],f['url'],'image not in bound source')
            assert hashlib.sha256((ROOT/f['local']).read_bytes()).hexdigest()==f['sha256']
        family=r['geometry_family'];split=r['split_group']
        assert split_for_family.setdefault(family,split)==split
        indices=r['source']['focus_cell_indices']
        assert all(0<=i<len(p['cells']) for i in indices)
        case=r['source_case']
        if case['type']=='published_sweep_member':
            idx=case['source_cell_index'];assert idx in indices
            text=''.join(captions[u][idx].split())
            param=case['parameter']
            if param=='force':
                assert 'Range[100,1000,100]' in text
                assert case['value'] in range(100,1001,100)
            elif param=='frequency':
                assert '{f,20,1000,10}' in text
                assert case['value'] in range(20,1001,10)
            elif param=='angular_frequency':
                assert '{i,3,4.5,0.05}' in text
                assert any(abs(case['value']/10**(3+k/20)-1)<1e-12 for k in range(31))
            else: raise AssertionError(param)
        assert r['model_evaluation']['failure_established'] is False
        assert r['readiness']['solver_run'] is False
    gallery=BeautifulSoup((OUT/'index.html').read_text(),'html.parser')
    assert len(gallery.select('article'))==100
    for img in gallery.select('img'):
        assert (OUT/img['src']).resolve().is_file(),img['src']
    fetch_path=OUT/'cell-fetch.json'
    fetched=None
    if fetch_path.exists():
        fetch=json.loads(fetch_path.read_text());fetched=fetch['fetched']
        for c in fetch['cells']:
            assert allowed(c['url']) and c['status']=='fetched',c
            raw=(ROOT/c['cache']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==c['sha256']
    report={'status':'PASS: provenance, parameter-membership and structural checks; not a solver validation',
            'tasks':len(rows),'geometry_families':len(split_for_family),'split_groups':len(set(split_for_family.values())),
            'images_traced_to_bound_source_pages':len({f['url'] for r in rows for f in r['figures']}),
            'full_source_cells_verified':fetched,'browser_preview':'blocked by browser tool file-URL policy; HTML and asset paths checked statically',
            'solver_validation':'not performed','category_counts':dict(Counter(r['category'] for r in rows))}
    (OUT/'provenance-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
