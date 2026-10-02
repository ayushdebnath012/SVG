"""Export released held-out source/reference edits for the paper (not predictions)."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import cadquery as cq
from verify_mechanical_cad_edits import execute, white_background

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])


def main():
    data = ROOT/'data/benchcad-online-edit-v1'
    rows = [json.loads(x) for x in (data/'test.jsonl').read_text().splitlines()]
    selected = [next(r for r in rows if r['source_record_id']==rid) for rid in
                ('twisted_bracket_rect_a_f130_compute', 'topup_stepped_shaft_top_slot')]
    figures = ROOT/'paper/network/figures'
    artifacts = ROOT/'runs/benchcad-reference-figures-20261002'
    artifacts.mkdir(exist_ok=True)
    root = ET.Element(NS+'svg', width='1200', height='690', viewBox='0 0 1200 690')
    ET.SubElement(root,NS+'rect',width='1200',height='690',fill='white')
    def text(x,y,s,size=19):
        n=ET.SubElement(root,NS+'text',x=str(x),y=str(y),fill='#173044',**{'font-family':'Arial','font-size':str(size)})
        n.text=s
    text(25,30,'Published BenchCAD source / reference edit pairs',24)
    for i,r in enumerate(selected):
        y=55+i*300
        name = 'Remove the second flange; retain the twisted web and first-flange holes.' if i==0 else 'Add a centered blind obround slot to the upper shaft face.'
        text(25,y+15,r['family'].replace('_',' ')+' | '+name,19)
        text(25,y+45,'SOURCE',16)
        text(625,y+45,'RELEASED TARGET',16)
        source=execute(r['code'])
        target=cq.importers.importStep(str(data/r['reference_step'])).val()
        for col,solid in enumerate((source,target)):
            path=artifacts/(r['source_record_id']+('-source.svg' if col==0 else '-target.svg'))
            cq.exporters.export(solid,str(path),opt={'projectionDir':(1,-1,1),'showHidden':False,'width':550,'height':210,'marginLeft':10,'marginTop':10})
            white_background(path)
            svg=ET.fromstring(path.read_text())
            svg.attrib.update(x=str(25+col*600),y=str(y+55),width='550',height='210',viewBox='0 0 550 210')
            root.append(svg)
        ET.SubElement(root,NS+'path',d=f'M 570 {y+150} L 620 {y+150} l -12 -8 m 12 8 l -12 8',fill='none',stroke='#24709a',**{'stroke-width':'3'})
    text(25,674,'Reference illustrations only. No stress or FEM result is inferred from these shapes. BenchCAD, CC-BY-4.0.',16)
    ET.ElementTree(root).write(figures/'benchcad-reference-pairs.svg',encoding='unicode')
    (artifacts/'manifest.json').write_text(json.dumps([dict(id=r['id'],source_record_id=r['source_record_id'],instruction=r['instruction'],reference_step_sha256=r['reference_step_sha256'],role='released_reference_not_model_prediction') for r in selected],indent=2)+'\n')
    print(figures/'benchcad-reference-pairs.svg')


if __name__=='__main__':
    main()
