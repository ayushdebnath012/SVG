"""Render retained CAD source/reference/Astra projection sheets for inspection."""
import html,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
from render_svg_gallery import render
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/cad-native-probe'
RUN=ROOT/'runs/astra-cad-native-20260920/screen-responses'

def main():
 tasks=json.loads((DATA/'tasks.json').read_text())['tasks'];tiles=[];sections=[]
 for task in tasks:
  tid=task['id'];strip=Image.new('RGB',(2100,335),'white');draw=ImageDraw.Draw(strip)
  draw.text((5,5),tid,fill='black');links=[]
  for j,(label,svg) in enumerate([('Source',DATA/tid/'source.svg'),('Reference',DATA/tid/'target.svg'),('Astra',RUN/tid/'final.svg')]):
   png=RUN/tid/(label.lower()+'.png');render(svg,png,1050)
   im=Image.open(png).convert('RGB').crop((0,0,1050,430));im.save(png)
   strip.paste(im.resize((700,287)),(j*700,40));draw.text((j*700+5,24),label,fill='black')
   rel=Path(__import__('os').path.relpath(svg,RUN));links.append(f'<div><h3>{label}</h3><a href="{rel}"><img src="{rel}" width="100%"></a></div>')
  tiles.append(strip);sections.append(f'<h2>{html.escape(tid)}</h2><p>{html.escape(task["instruction"])}</p><div class="row">'+''.join(links)+'</div>')
  print('Rendered',tid,flush=True)
 gallery=Image.new('RGB',(2100,len(tiles)*335),'white')
 for i,tile in enumerate(tiles):gallery.paste(tile,(0,i*335))
 gallery.save(RUN/'gallery.png')
 (RUN/'gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>Native CAD edit audit</title><style>body{font:16px sans-serif;margin:24px}.row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}img{border:1px solid #ddd}h2{margin-top:40px}</style><h1>Source / reference / Astra CAD drawing sheets</h1><p>Views are kernel projections, independently fit per view; SVG paths remain vectors. Click a sheet to inspect.</p>'+''.join(sections))
if __name__=='__main__':main()
