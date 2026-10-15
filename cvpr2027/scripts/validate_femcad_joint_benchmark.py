#!/usr/bin/env python3
"""Validate the stricter joint CAD+FEM candidate boundary."""
import json
from pathlib import Path
from build_femcad_joint_benchmark import OUT,DATA,sha,input_text_file
from validate_fem_evaluation_inputs import Document


def main():
    catalog=json.loads((DATA/'joint-benchmark.json').read_text());count=0;images=0;texts=0
    assert len(catalog['rows'])==50
    for row in catalog['rows']:
        root=OUT/'candidate-inputs'/row['id'];m=json.loads((root/'task.json').read_text())
        assert m['track']=='joint-cad-plus-fem' and not m['scored_evaluation_ready']
        expected={f['path']:f for f in m['files']}
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        assert actual==set(expected)|{'task.json'}
        for rel,f in expected.items():
            p=root/rel;assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve())
            assert sha(p)==f['sha256'];assert p.suffix.lower() in {'.html','.txt','.png'}
            if p.suffix=='.txt':assert input_text_file(p.name);texts+=1
            if p.suffix=='.png':images+=1
            count+=1
        doc=Document(root/'problem.html');text=' '.join(doc.text).lower()
        for forbidden in ['modeling instructions','geometry instructions','click','toolbar','settings window','insert sequence','http://','https://']:
            assert forbidden not in text,(row['id'],forbidden)
        for tag,attrs in doc.elements:
            assert tag not in {'script','iframe','object','embed'}
            assert 'href' not in attrs
            if tag=='img':assert attrs['src'] in expected
        for heading in doc.headings:assert not heading.lower().startswith(('results','result templates'))
        for provenance in row['provenance']:assert expected[provenance['path']]['sha256']==provenance['sha256']
        contract=json.loads((OUT/'evaluator-only'/row['id']/'contract.json').read_text())
        assert contract['release_approved'] is False and contract['numerical']['tolerances'] is None
    result={'status':'passed','joint_task_drafts':50,'candidate_files_verified':count,'source_images':images,'source_specification_files':texts,
      'checks':['No CAD/model/mesh binary in candidate files','No construction/UI recipe text','Local original images and equations','SHA-256 source provenance','Private contracts separate','No unvalidated score or tolerance'],
      'released_for_scoring':0,'limitations':'Input completeness, source semantics, reference exports, solver replay and correctness scoring remain unvalidated.'}
    (DATA/'joint-benchmark-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
