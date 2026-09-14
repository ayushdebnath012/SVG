"""Fetch openly accessible surveyed PDFs; record failures without bypassing access controls."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

class Metadata(HTMLParser):
    def __init__(self): super().__init__();self.data={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('name','').startswith('citation_'):
            self.data.setdefault(a['name'],[]).append(a.get('content',''))

def fetch(entry):
    row=dict(entry);row['retrieved_utc']=datetime.now(timezone.utc).isoformat()
    def get(url):
        req=urllib.request.Request(url,headers={'User-Agent':'SVG-Research-Archive/1.0'})
        with urllib.request.urlopen(req,timeout=45) as r:return r.read()
    if entry.get('arxiv_id'):
        try:
            parser=Metadata();parser.feed(get(entry['url']).decode(errors='replace'))
            row['citation_metadata']=parser.data
        except Exception as e:row['metadata_error']=type(e).__name__
    if not entry.get('pdf_url'):
        row['status']='source_link_only';return row
    target=ROOT/'papers'/'pdf'/f"{entry['id']}.pdf"
    try:
        data=target.read_bytes() if target.exists() else get(entry['pdf_url'])
        if not data.startswith(b'%PDF-'):raise ValueError('response is not a PDF')
        import pymupdf
        doc=pymupdf.open(stream=data,filetype='pdf')
        row['pages']=len(doc);row['first_page_excerpt']=doc[0].get_text()[:1200]
        target.parent.mkdir(exist_ok=True);target.write_bytes(data)
        row.update(status='downloaded',path=str(target.relative_to(ROOT)),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    except Exception as e:
        row.update(status='download_unavailable',error=type(e).__name__)
    print(entry['id'],row['status'],flush=True)
    return row

if __name__=='__main__':
    entries=json.loads((ROOT/'papers/catalog.json').read_text())
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,entries))
    (ROOT/'papers/download_manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
