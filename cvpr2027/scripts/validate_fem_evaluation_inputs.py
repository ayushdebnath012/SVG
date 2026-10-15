#!/usr/bin/env python3
"""Structural/integrity checks for prepared FEM inputs; not a physics evaluator."""
import argparse
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from package_fem_evaluation_inputs import OUT, DATA, ROOT, HELD_NAMES, binary_check, sha


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.elements=[]; self.text=[]; self.headings=[]; self.heading=None
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag,dict(attrs)))
        if tag in {'h2','h3'}:self.heading=[]

    def handle_endtag(self, tag):
        if tag in {'h2','h3'} and self.heading is not None:
            self.headings.append(''.join(self.heading));self.heading=None

    def handle_data(self, data):
        self.text.append(data)
        if self.heading is not None:self.heading.append(data)


def validate_task(directory):
    manifest=json.loads((directory/'task.json').read_text())
    expected={f['path']:f for f in manifest['files']}
    actual={p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    assert actual==set(expected)|{'task.json'}, 'Unlisted/missing files'
    for rel,record in expected.items():
        path=directory/rel
        assert not path.is_symlink(), 'Symlink forbidden'
        assert path.resolve().is_relative_to(directory.resolve()), 'File escapes task directory'
        assert sha(path)==record['sha256'], 'Hash mismatch: '+rel
        assert path.stat().st_size==record['bytes'], 'Size mismatch: '+rel
        assert path.name not in HELD_NAMES, 'Held-out numeric answer in input'
        if path.suffix=='.mph':binary_check(path)
    doc=Document(directory/'problem.html')
    for tag,attrs in doc.elements:
        assert tag not in {'script','iframe','object','embed'}, 'Active/external content'
        assert not attrs.get('href'), 'Candidate hyperlink'
        if tag=='img':
            src=attrs.get('src'); assert src in expected, 'Missing image: '+str(src)
            assert src.startswith('images/'), 'Nonlocal image'
    for heading in doc.headings:
        assert not heading.lower().startswith(('results','result templates')), 'Result section leaked'
    text=' '.join(doc.text)
    assert not re.search(r'https?://',text), 'External source URL in prompt'
    assert not any(name in text for name in HELD_NAMES), 'Reference-table instruction leaked'
    return manifest


def validate_all():
    dirs=sorted((OUT/'model-inputs').glob('FEMCAD-ADV-*'))
    assert len(dirs)==50
    checks=0
    for directory in dirs:
        m=validate_task(directory); checks+=len(m['files'])
        ref=json.loads((OUT/'held-out'/m['id']/'reference.json').read_text())
        # Every candidate figure/dependency is identical to a captured source asset.
        inputs={x['path']:x for x in m['files']}
        for item in ref['candidate_provenance']:
            assert item['sha256']==inputs[item['path']]['sha256']
        assert sha(OUT/'held-out'/m['id']/'original-tutorial.html')==ref['source_page']['sha256']
        for item in ref['reference_image_provenance']:
            assert sha(OUT/'held-out'/m['id']/item['path'])==item['sha256']
        assert (OUT/'held-out'/m['id']/'reference.html').exists()
    # Known subtle leaks outside the main results sections.
    for sid,patterns in {
      5:['TL_exp','perforated_muffler_exp_data'],
      10:['0.778 X 0.778 Y 0.298 Z'],
      11:['hyperelastic_seal.mph'],
      21:['19.6–21.0','53.4–55.8','sheet_metal_forming.txt'],
      26:['Interpolation Function: Lp Data','Interpolation Function: Z Data'],
      30:['highest magnitude is in the area around the side mirror'],
      33:['resonant frequency of the device is 870 MHz'],
      40:['displacements of the structure at 1400 Hz'],
      42:['At the resonance frequency of 9 kHz'],
      43:['helmholtz_renoator_with_flow.mph'],
    }.items():
        text=' '.join(Document(OUT/'model-inputs'/f'FEMCAD-ADV-{sid:03d}'/'problem.html').text)
        for pattern in patterns: assert pattern not in text,(sid,pattern)
    # Required safe assets and cross-study material dependency are present.
    for sid,name in [(6,'golf_ball_impact.mphbin'),(12,'snap_hook_disp.txt'),
                     (30,'sports_car_fsi_geom_sequence.mph'),(40,'loudspeaker_driver_materials.mph'),
                     (41,'electric_motor_noise_pmsm_geom_sequence.mph'),(44,'gearbox_vibration_noise.mphbin')]:
        assert (OUT/'model-inputs'/f'FEMCAD-ADV-{sid:03d}'/'assets'/name).exists()
    # All four numerical tables stay private.
    for name in HELD_NAMES:assert list((OUT/'held-out').glob('*/assets/'+name))
    result={'status':'passed','task_packages':50,'candidate_files_verified':checks,
            'checks':['inventory and SHA-256','source provenance','local image resolution',
                      'no hyperlinks or active HTML','no known reference tables or solved MPH entries',
                      'targeted answer-leak regressions','required geometry/material dependencies'],
            'limits':['Does not certify all semantic leakage absent.','Does not verify source physics, solver compatibility, complete study instructions, or numerical scoring.']}
    (DATA/'input-packaging-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':validate_all()
