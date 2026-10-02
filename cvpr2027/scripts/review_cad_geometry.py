"""Render source/answer/material-error evidence, without modifying generated SVGs."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import cad_hard_geometry as h
import cad_torus_sections as t
from render_svg_gallery import render

def review(data,run,out):
 tasks={v['id']:v for v in json.loads((data/'tasks.json').read_text())['tasks']};tiles=[]
 for path in sorted(run.glob('*/sample-*/output.svg')):
  task=tasks[path.parent.parent.name];svg=path.read_text()
  try:actual=h.raster(h.isolate(svg))
  except Exception as e:print(path,type(e).__name__);continue
  ref=t.mask(task) if task['kind']=='torus_section' else h.reference_mask(task)
  overlay=np.full((*ref.shape,3),255,dtype=np.uint8);overlay[ref&actual]=[80,80,80];overlay[actual&~ref]=[220,50,35];overlay[ref&~actual]=[25,100,220]
  Image.fromarray(overlay).save(path.parent/'geometry_overlay.png')
  Image.fromarray(np.where(ref,0,255).astype('uint8')).save(path.parent/'reference_material.png')
  Image.fromarray(np.where(actual,0,255).astype('uint8')).save(path.parent/'actual_material.png')
  render(path,path.parent/'drawing.png',1000)
  refsvg=path.parent/'reference.svg';refsvg.write_text(t.oracle(task) if task['kind']=='torus_section' else h.oracle_svg(task));render(refsvg,path.parent/'reference.png',1000)
  strip=Image.new('RGB',(1080,385),'white');draw=ImageDraw.Draw(strip);draw.text((8,5),task['id']+' / '+path.parent.name,fill='black')
  for i,name in enumerate(['reference.png','drawing.png','geometry_overlay.png']):strip.paste(Image.open(path.parent/name).convert('RGB').resize((360,360)),(i*360,25))
  tiles.append(strip);print('Reviewed artifacts',task['id'],path.parent.name,flush=True)
 if tiles:
  gallery=Image.new('RGB',(1080,len(tiles)*385),'white')
  for i,tile in enumerate(tiles):gallery.paste(tile,(0,i*385))
  out.parent.mkdir(parents=True,exist_ok=True);gallery.save(out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();review(a.data,a.run,a.output)
