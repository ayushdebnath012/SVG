"""Diagnose bare-list vs wrapped-object output formatting without changing edits."""
import argparse
import ast
import json
from pathlib import Path
import sys
from benchcad_online_edit_dataset import apply


def main():
    sys.setrecursionlimit(10000)
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--predictions',type=Path,required=True)
    a=p.parse_args()
    sources={r['id']:r for r in map(json.loads,(a.data/'test.jsonl').read_text().splitlines())}
    out=[]
    for r in map(json.loads,a.predictions.read_text().splitlines()):
        item=dict(r)
        item['control']='Wrap a bare JSON edit list in the required edits object; do not alter coordinates or content.'
        try:
            text=r['prediction'].strip()
            if text.startswith('```'):text='\n'.join(text.splitlines()[1:-1])
            obj=json.loads(text)
            if isinstance(obj,list):obj={'edits':obj}
            code=apply(sources[r['id']]['code'],obj)
            item.update(predicted_code=code,applicable=True,error=None,
                        ast_match=ast.dump(ast.parse(code))==ast.dump(ast.parse(r['reference_code'])))
        except Exception as e:item.update(predicted_code=None,applicable=False,ast_match=False,error=str(e)[:250])
        out.append(item)
    dest=a.predictions.with_name(a.predictions.name.replace('-predictions','-transport-control-predictions'))
    dest.write_text(''.join(json.dumps(r)+'\n' for r in out))
    print('Transport control:',sum(r['applicable'] for r in out),'applicable;',sum(r['ast_match'] for r in out),'AST matches;',len(out),'total')


if __name__=='__main__':main()
