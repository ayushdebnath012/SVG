"""Local, unofficial public CADGenBench drawing reconstruction experiment.

No private targets, public submissions, or benchmark-derived training. Kernel
SVG projections are generated from the returned solid. Final geometric claims
require separately audited drawing predicates, not an LLM's self-assessment.
"""
import argparse,base64,hashlib,json,time,urllib.request,urllib.error
from pathlib import Path
import cad_native_probe as native
from render_svg_gallery import render
ROOT=native.ROOT
SOURCE=ROOT/'data/cad-released-probe/149'
SYSTEM='''Reconstruct the physical machined part in the supplied engineering drawing as a CadQuery solid. Units mm. The final result will also be exported as native vector SVG orthographic engineering views.
Use XY for the circular top view, Z for thickness, main bore centred at X=Y=0, bottom at Z=0, top at Z=25. In the top view page right is +X and page up is +Y. Follow all explicit dimensions, depths, pockets, bore patterns, chamfers and fillets. Do not replace the part with a visual approximation. Explain ambiguities rather than concealing them.
You have a CadQuery 2.8 evaluate_cad tool. It returns kernel validity, volume, envelope, and rendered kernel projections, but no target answer or correctness feedback. Use it at least once and up to four times to review and repair the part.
The restricted execution interface permits import cadquery as cq, variable assignments, numeric arithmetic, literal tuple/list for loops, and these CadQuery methods: '''+' '.join(sorted(native.METHODS))+'''. No functions, comprehensions, other imports, file access or introspection. Precompute needed trig constants numerically. Assign the final shape/workplane to result. Unsupported interface syntax is not counted as a shape failure.
Return JSON only: {"code":"complete executable CadQuery code","explanation":"construction and limitations"}.'''
TOOL=native.TOOL

def img(path):return {'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'detail':'high'}

def run(out,sample,case='149',resume=False):
    out.mkdir(parents=True,exist_ok=True)
    previous=None
    if (out/'result.json').exists():
        if not resume:raise ValueError('Existing run; do not overwrite')
        previous=json.loads((out/'result.json').read_text())
        if previous['status'] not in {'api_error','operational_error'}:raise ValueError('Resume only interrupted requests, not completed trials')
    source=SOURCE.parent/case
    system=SYSTEM
    if case=='131':
        system=system.replace('Use XY for the circular top view, Z for thickness, main bore centred at X=Y=0, bottom at Z=0, top at Z=25. In the top view page right is +X and page up is +Y.', 'Use XY for the large principal view at lower left, with page right = +X and page up = +Y. Use Z for part depth along the main bore axis. Put minimum X, Y, Z at zero. The marked overall dimensions are 145.32 by 198.85 by 50 mm; keep the orientation consistent with the drawing views.')
    paths=[source/(x+'.png') for x in ['input','top','detail','side']]
    protocol={'model':'gpt-6-astra','effort':'high','max_output_tokens':24000,'max_tool_calls':4,'sample':sample,'system':system,'tool':TOOL,
      'source':'https://huggingface.co/datasets/HuggingAI4Engineering/cadgenbench-data/tree/main/'+case,
      'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
      'scope':'Unofficial local reconstruction. No private target access. All inputs are evaluation-only.',
      'necessary_checks_frozen_before_screen':['One valid solid','Axial thickness 25 mm','Outer diameter 150 mm before four workholding flats','Main through bore diameter 95 mm except explicit internal tabs','Four diameter 10 through holes','Four diameter 9 through holes with diameter 15 counterbores depth 8.6 mm','Eight diameter 5 blind holes depth 12 mm','Outer pockets leave 13 mm base thickness'],
      'grading':'Check explicit public drawing features only; do not count unobserved private geometry or legal alternatives as failures. A pass of partial checks is not a full benchmark pass.'}
    if case=='131':protocol['necessary_checks_frozen_before_screen']=['One valid connected solid','Marked overall dimensions 145.32 by 198.85 by 50 mm','Main bore includes diameter 80 through region and diameter 90 counterbored opening per section A-A','Two diameter 10 mounting holes shown in principal view','Two diameter 6 bottom mounting holes','Section E-E lower recess leaves 5 mm wall','Section B-B recesses have 8 mm lower wall and 15 mm upper walls','Openings in both tall inclined ribs as shown by principal/section/isometric views']
    if (out/'protocol.json').exists() and json.loads((out/'protocol.json').read_text())!=protocol:raise ValueError('Protocol changed')
    native.write(out/'protocol.json',protocol)
    messages=[{'role':'system','content':system},{'role':'user','content':[{'type':'input_text','text':f'Reproduce CADGenBench public drawing {case}. The first image is the original; the others are enlarged crops from the same drawing.'}]+[img(p) for p in paths]}]
    key=native.api_key();record={'status':'started','sample':sample,'usage':[]};calls=0;start=time.perf_counter();start_turn=0;elapsed=0
    if previous:
        n=len(list(out.glob('interruption-*.json')))
        native.write(out/f'interruption-{n}.json',previous)
        start_turn=max(int(p.stem.split('-')[-1]) for p in out.glob('request-*.json'))
        if (out/f'response-{start_turn}.json').exists():raise ValueError('Interrupted after response; manual resume audit required')
        messages=json.loads((out/f'request-{start_turn}.json').read_text())['input']
        record['usage']=previous['usage'];record['resumed_after_interruptions']=n+1
        calls=previous['tool_calls'];elapsed=previous['wall_seconds']
    try:
        for turn in range(start_turn,5):
            payload={'model':'gpt-6-astra','input':messages,'reasoning':{'effort':'high'},'max_output_tokens':24000,'store':False,'include':['reasoning.encrypted_content']}
            if calls<4:payload.update(tools=[TOOL],tool_choice='required' if turn==0 else 'auto',parallel_tool_calls=False)
            native.write(out/f'request-{turn}.json',payload)
            req=urllib.request.Request(native.ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
            with urllib.request.urlopen(req,timeout=900) as r:raw=json.load(r)
            native.write(out/f'response-{turn}.json',raw);record['usage'].append(raw.get('usage',{}))
            if raw['status']!='completed':record['status']='budget_or_incomplete';break
            messages.extend(raw['output']);tc=[v for v in raw['output'] if v['type']=='function_call']
            if tc:
                for c in tc:
                    folder=out/f'tool-{calls}';code=json.loads(c['arguments'])['code']
                    result=native.execute(code,folder,svg=str(folder/'views.svg'),title='Candidate kernel views')
                    messages.append({'type':'function_call_output','call_id':c['call_id'],'output':json.dumps(result)})
                    if result['status']=='completed':
                        render(folder/'views.svg',folder/'views.png',1100)
                        messages.append({'role':'user','content':[{'type':'input_text','text':'Kernel projections of your candidate. Review against the original drawing.'},img(folder/'views.png')]})
                    calls+=1;print('TOOL',sample,calls,result['status'],result.get('error',''),flush=True)
            else:
                text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text')
                (out/'final.txt').write_text(text)
                if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
                obj=json.loads(text);(out/'final.py').write_text(obj['code'])
                record['execution']=native.execute(obj['code'],out/'execution',svg=str(out/'final.svg'),step=str(out/'final.step'),title=f'CADGenBench {case} / Astra reconstruction')
                record['explanation']=obj.get('explanation');record['status']='completed';break
        if record['status']=='started':record['status']='no_final'
    except urllib.error.HTTPError as e:record.update(status='api_error',error=e.read().decode().replace(key,'[REDACTED]')[:1000])
    except Exception as e:record.update(status='operational_error',error=str(e).replace(key,'[REDACTED]')[:1000])
    record.update(tool_calls=calls,wall_seconds=elapsed+time.perf_counter()-start);native.write(out/'result.json',record)
    print('END',sample,record['status'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--sample',type=int,default=0);p.add_argument('--case',choices=['149','131'],default='149');p.add_argument('--resume',action='store_true');a=p.parse_args();run(a.output,a.sample,a.case,a.resume)
