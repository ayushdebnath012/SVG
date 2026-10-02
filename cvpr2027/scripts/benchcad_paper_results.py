"""Generate manuscript table macros from completed, pinned evaluation artifacts."""
import argparse
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    def read(name):return json.loads((a.run/name).read_text())
    m=read('run_manifest.json')
    if m['status']!='completed':raise ValueError('Training and final evaluation must complete first')
    trained=read('trained-metrics.json');base=read('base-metrics.json')
    geom={key:read(name+'-predictions-geometry.json') for key,name in
          [('base','base'),('control','base-transport-control'),('trained','trained')]}
    n=trained['n']
    assert n==m['counts']['test']==base['n']
    for g in geom.values():assert g['n']==n
    control=[json.loads(x) for x in (a.run/'base-transport-control-predictions.jsonl').read_text().splitlines()]
    valid=geom['base']['reference_valid']
    lines=['% Generated from completed local BenchCAD artifacts. Do not edit numeric results manually.']
    def macro(name,value):lines.append('\\newcommand{\\'+name+'}{'+str(value)+'}')
    for name,key in [('onlineTrain','train'),('onlineValid','validation'),('onlineTest','test')]:macro(name,m['counts'][key])
    macro('onlineReferenceValid',valid)
    rows=[]
    values=[('Base, strict interface',base['applicable'],base['ast_match'],geom['base']),
            ('Base, bare-list transport control',sum(r['applicable'] for r in control),sum(r['ast_match'] for r in control),geom['control']),
            ('Fresh online-pair QLoRA',trained['applicable'],trained['ast_match'],geom['trained'])]
    for name,app,ast,g in values:rows.append(f"{name} & {app} & {ast} & {g['match_95']} & {g['match_strict']} \\\\")
    macro('onlineMainRows','\n'.join(rows))
    category=[]
    for c,stats in sorted(trained['categories'].items()):
        category.append(f"{c} & {stats['n']} & {stats['ast_match']} & {geom['trained']['categories'][c]['match_strict']} \\\\")
    macro('onlineCategoryRows','\n'.join(category))
    g=geom['trained']
    discussion=(f"The trained model produces {trained['applicable']}/{n} applicable patches and "
                f"{trained['ast_match']}/{n} exact target ASTs. Of {valid} independently valid STEP references, "
                f"{g['executable']} predictions build valid solids, {g['match_95']} reach IoU $\\geq0.95$, "
                f"and {g['match_strict']} reach strict IoU $\\geq0.99999$ "
                f"({100*g['match_strict']/valid:.1f}\\,\\%). The bare-list base control builds "
                f"{geom['control']['executable']} solids, with {geom['control']['match_95']} broad and "
                f"{geom['control']['match_strict']} strict matches. Thus the experiment exposes a substantial "
                "remaining gap: most held-out edits fail to produce the reference geometry, particularly beyond literal-parameter changes.")
    macro('onlineResultsDiscussion',discussion)
    counts=g['statuses']
    op=(f"Independent reference readback finds {valid}/{n} valid target solids. One released rivet reference "
        "is invalid and is excluded from the geometric success denominator, while all task outputs remain reported. "
        f"For the trained run, {counts.get('scored',0)} cases are geometrically scored, "
        f"{counts.get('execution_error',0)} have execution errors and {counts.get('invalid_patch',0)} have invalid patches; "
        f"there are {counts.get('timeout',0)} timeouts and {counts.get('comparison_error',0)} Boolean-comparison errors. "
        "The observed code failures include invalid feature operations and damaged source coordinates; they are distinct from valid solids with low IoU.")
    macro('onlineOperationalDiscussion',op)
    a.output.write_text('\n'.join(lines)+'\n')
    print(a.output)


if __name__=='__main__':main()
