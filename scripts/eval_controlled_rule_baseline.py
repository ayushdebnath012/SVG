"""Transparent template parser baseline for the synthetic routing pilot.

Uses instruction text only, never target actions. Its template-specific rules
are a deliberately strong control for the limited language in this dataset.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
from train_controlled_editing import load_rows,score_action


def predict(text):
    low=text.lower()
    if 'hide required' in low or 'remove the required' in low:
        return {'action':'reject','reason':'missing_required_contour'}
    if 'keep the geometry but label' in low or 'without solving again' in low:
        return {'action':'reject','reason':'numerical_claim'}
    if 'hot boundary temperature' in low or 'left_temperature=' in low:
        match=re.search(r'(?:temperature to |left_temperature=)(\d+(?:\.\d+)?)',low)
        return {'action':'recompute','parameter':'left_temperature','value':float(match[1])}
    cid=re.search(r'\bc\d+\b',text)
    color=re.search(r'#[0-9a-fA-F]{6}',text)
    if color and cid:
        return {'action':'style','target':cid[0],'attribute':'stroke','value':color[0]}
    if 'stroke width' in low or 'line thickness' in low:
        width=re.search(r'(?:width of |to )(\d+(?:\.\d+)?)',low)
        return {'action':'style','target':cid[0],'attribute':'stroke-width','value':float(width[1])}
    lid=re.search(r'\bl\d+\b',text)
    if lid:
        xy=re.search(r'(?:x=|\()(\d+)(?:, y=|, )(\d+)',text)
        return {'action':'move_label','target':lid[0],'x':int(xy[1]),'y':int(xy[2])}
    raise ValueError('unsupported instruction')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='runs/cvpr2027/controlled-editing-data')
    p.add_argument('--output',default='runs/cvpr2027/rule-baseline');args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True);raw=[];summary={}
    for split in ('test','ood'):
        rows=load_rows(Path(args.data)/f'{split}.jsonl');metrics=[]
        for row in rows:
            try:text=json.dumps(predict(row['instruction']))
            except (ValueError,TypeError,IndexError,AttributeError):text='unsupported'
            score=score_action(row,text);metrics.append(score)
            raw.append({'id':row['id'],'split':split,'prediction':text,'metrics':score})
        summary[split]={'n':len(rows),**{k:sum(m[k] for m in metrics)/len(metrics)
                                       for k in ('exact_action','action_correct','unsafe_edit')}}
    (out/'results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in raw))
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
