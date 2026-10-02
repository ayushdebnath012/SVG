"""Persist high-resolution mask evidence and worst-disagreement detail crops."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
import cad_precision_sections as p
from render_svg_gallery import render

def review(data,run,out):
 tasks={t['id']:t for t in json.loads((data/'tasks.json').read_text())['tasks']};tiles=[]
 for svgpath in sorted(run.glob('*/sample-*/output.svg')):
  task=tasks[svgpath.parent.parent.name];folder=svgpath.parent
  actual=p.raster(p.h.isolate(svgpath.read_text()));target=p.mask(task);metric=p.compare(actual,target)
  Image.fromarray(np.where(target,0,255).astype('uint8')).save(folder/'precision_reference.png')
  Image.fromarray(np.where(actual,0,255).astype('uint8')).save(folder/'precision_actual.png')
  overlay=np.full((*target.shape,3),255,dtype=np.uint8);overlay[target&actual]=[75,75,75];overlay[actual&~target]=[225,40,35];overlay[target&~actual]=[20,95,225]
  im=Image.fromarray(overlay);im.save(folder/'precision_overlay.png')
  d=distance_transform_edt(target);d[~(target&~actual)]=0;idx=int(np.argmax(d));best=float(d.flat[idx]);del d
  d=distance_transform_edt(~target);d[~(actual&~target)]=0
  if np.max(d)>best:idx=int(np.argmax(d))
  del d
  y,x=np.unravel_index(idx,target.shape);left=max(0,min(x-256,p.SIZE-512));top=max(0,min(y-256,p.SIZE-512));crop=im.crop((left,top,left+512,top+512));crop.save(folder/'precision_detail.png')
  metric['detail_crop_physical_mm']=[(left-p.ORIGIN)/p.SCALE,(p.ORIGIN-top)/p.SCALE,512/p.SCALE]
  (folder/'precision_review_metrics.json').write_text(json.dumps(metric,indent=2)+'\n')
  render(svgpath,folder/'drawing.png',1000)
  tile=Image.new('RGB',(1100,430),'white');draw=ImageDraw.Draw(tile);draw.text((10,5),task['id']+' / '+folder.name,fill='black')
  tile.paste(Image.open(folder/'drawing.png').convert('RGB').resize((380,380)),(0,30));tile.paste(im.resize((380,380)),(380,30));tile.paste(crop.resize((320,320)),(780,50))
  draw.text((780,375),f'16 mm detail; red extra, blue missing',fill='black');draw.text((10,410),f"Residual area {metric['residual_mismatch_mm2']:.4f} mm2; max intrusion {metric['max_intrusion_mm']:.4f} mm",fill='black');tiles.append(tile)
  print(task['id'],folder.name,metric,flush=True)
 if tiles:
  gallery=Image.new('RGB',(1100,430*len(tiles)),'white')
  for i,tile in enumerate(tiles):gallery.paste(tile,(0,430*i))
  gallery.save(out)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--data',type=Path,required=True);a.add_argument('--run',type=Path,required=True);a.add_argument('--output',type=Path,required=True);s=a.parse_args();review(s.data,s.run,s.output)
