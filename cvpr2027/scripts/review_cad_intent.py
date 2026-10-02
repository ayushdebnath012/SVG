"""Render the frozen panel probe for human review; no new API calls."""
import hashlib
import html
import json
import os
from pathlib import Path
from PIL import Image,ImageDraw
from render_svg_gallery import render

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/cad-intent-probe'
RUN=ROOT/'runs/astra-cad-intent-20260921'


def main():
    tasks=json.loads((DATA/'tasks.json').read_text())['tasks']
    rows=[];sections=[]
    for t in tasks:
        tid=t['id'];row=Image.new('RGB',(2550,580),'white');draw=ImageDraw.Draw(row)
        draw.text((10,5),tid,fill='black');cells=[]
        for j,(label,svg) in enumerate([
            ('Source',DATA/tid/'source.svg'),('Reference',DATA/tid/'target.svg'),
            ('Astra',RUN/'screen'/tid/'output.svg')]):
            png=RUN/'screen'/tid/(label.lower()+'.png');render(svg,png,850)
            im=Image.open(png).convert('RGB').crop((0,0,850,540));im.save(png)
            row.paste(im,(j*850,40));draw.text((j*850+10,23),label,fill='black')
            rel=os.path.relpath(svg,RUN)
            cells.append(f'<div><h3>{label}</h3><a href="{rel}"><img src="{rel}"></a></div>')
        rows.append(row)
        sections.append(f'<h2>{html.escape(tid)}</h2><div class="row">'+''.join(cells)+'</div>')
        print('Rendered',tid,flush=True)
    gallery=Image.new('RGB',(2550,580*len(rows)),'white')
    for i,row in enumerate(rows):gallery.paste(row,(0,580*i))
    gallery.save(RUN/'gallery.png')
    (RUN/'gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>Engineering drawing intent probe</title><style>body{font:16px sans-serif;margin:24px}.row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}img{width:100%;border:1px solid #ddd}</style><h1>One panel, two dimensional intentions, two coordinate encodings</h1><p>Source / independently authored reference / Astra final edit. All four conditions passed. Click a drawing for full SVG. These are controls, not confirmed failures.</p>'+''.join(sections))
    files=[DATA/'tasks.json',ROOT/'scripts/cad_intent_probe.py',ROOT/'scripts/cad_intent_rule_baseline.py',ROOT/'scripts/cad_query_evidence.py',ROOT/'scripts/review_cad_intent.py',ROOT/'configs/cad-foundation-protocol.json',ROOT/'tests/test_cad_intent_probe.py',ROOT/'tests/test_cad_query_evidence.py']
    files+=list((RUN/'screen').rglob('*.json'))
    files+=list((RUN/'rule-baseline').rglob('*.json'))
    files+=[RUN/name for name in ['query-evidence.json','hard_selection.json','visual_review.json'] if (RUN/name).exists()]
    (RUN/'evidence_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2)+'\n')


if __name__=='__main__':main()
