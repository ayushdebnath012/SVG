#!/usr/bin/env python3
"""Export exactly one input package. Never traverses held-out or another task."""
import argparse
import json
import zipfile
from pathlib import Path
from package_fem_evaluation_inputs import OUT, sha
from validate_fem_evaluation_inputs import validate_task


def export(task,output):
    if not task.startswith('FEMCAD-ADV-') or task not in {f'FEMCAD-ADV-{n:03d}' for n in range(1,51)}:
        raise SystemExit('Invalid task ID')
    directory=OUT/'model-inputs'/task
    manifest=validate_task(directory)
    if manifest['input_packaging_status']!='packaged':
        raise SystemExit('Blocked task; no bundle exported: '+'; '.join(manifest['blocking_issues']))
    output=Path(output)
    if output.exists():raise SystemExit('Output already exists; choose a new path')
    output.parent.mkdir(parents=True,exist_ok=True)
    names=['task.json']+[f['path'] for f in manifest['files']]
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:z.write(directory/name,name)
    with zipfile.ZipFile(output) as z:assert set(z.namelist())==set(names)
    return {'task':task,'path':str(output),'sha256':sha(output),'files':len(names),
            'purpose':'Isolated qualitative preparation; not a scored release',
            'isolation':'Use a fresh candidate context with only this archive extracted; no network, other tasks, source catalogs, or held-out access.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task');parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(export(args.task,args.output),indent=2))
