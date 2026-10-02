"""Dense exact-length meander routing; original constructive reference is audited."""
import argparse,json,random
from pathlib import Path
import cad_timed_routing as timed
r=timed.r;DATA=r.ROOT/'data/cad-serpentine-routing'

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen')
    t=json.loads((timed.DATA/'tasks.json').read_text())['tasks'][0]
    paths={k:r.expand(v) for k,v in t['reference_routes'].items()};occupied={p for ps in paths.values() for p in ps};blocked=set(map(tuple,t['blocked']));rng=random.Random(8401);added={k:0 for k in paths}
    # Replace an edge by a three-edge detour, preserving endpoints and avoiding
    # every previously occupied/blocked site. Each insertion adds exactly 4 mm.
    for _ in range(500):
        candidates=[]
        for ident,ps in paths.items():
            if ident in t['locked_routes']:continue
            for i,(a,b) in enumerate(zip(ps,ps[1:])):
                dx=b[0]-a[0];dy=b[1]-a[1]
                for sign in (-1,1):
                    u=(a[0]-sign*dy,a[1]+sign*dx);v=(b[0]-sign*dy,b[1]+sign*dx)
                    if all(0<=p[0]<t['width'] and 0<=p[1]<t['height'] and p not in occupied and p not in blocked for p in (u,v)):
                        candidates.append((ident,i,u,v))
        if not candidates:break
        # Balance extra path length across nets before random tie breaking.
        smallest=min(added[c[0]] for c in candidates);ident,i,u,v=rng.choice([c for c in candidates if added[c[0]]==smallest])
        paths[ident][i+1:i+1]=[u,v];occupied.update((u,v));added[ident]+=4
    t['id']='dense_serpentine_length_edit';t['reference_routes']={k:r.compress([list(p) for p in ps]) for k,ps in paths.items()};t['length_targets_mm']={k:2*(len(ps)-1) for k,ps in sorted(paths.items())}
    reference=timed.grade(t,t['reference_routes']);assert reference['pass']
    r.write(DATA/'tasks.json',{'version':'serpentine-routing-v1','tasks':[t],'selection':'Before model testing, insert feasible disjoint two-cell detours into the existing reference until no insertion remains, balancing additions across unlocked nets. Seed 8401. This supplies a constructive feasible reference, not an optimal or preferred routing target. Shared board and five locked traces: paired constraint variant, not a new family.','preflight':{'reference_grade':reference,'occupied_sites':len(occupied),'available_sites':t['width']*t['height']-len(blocked),'extra_length_mm_by_net':added},'admission':'Three fresh-context completed geometric failures with high effort, 32000 output tokens per turn and four checker calls. Exclude incomplete/truncated/interface/operational errors. Exact configuration only.'})
    (DATA/'source.svg').write_text(timed.drawing(t,t['locked_routes']));(DATA/'reference.svg').write_text(timed.drawing(t,t['reference_routes']));r.render(DATA/'source.svg',DATA/'source.png',1650);r.render(DATA/'reference.svg',DATA/'reference.png',1650)
    audit=timed.audit(t,DATA/'reference.svg');assert audit['pass'];r.write(DATA/'reference-audit.json',audit)
    print('Reference sites',len(occupied),'of',t['width']*t['height']-len(blocked),'max length',max(t['length_targets_mm'].values()),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:
        r.DATA=DATA;r.grade=timed.grade;r.drawing=timed.drawing
        r.SYSTEM+=' Additional mandatory constraints: every net must have the exact geometric centerline length in length_targets_mm. The lengths require serpentine paths; retracing, repeated grid sites, self-contact and loops are forbidden. Five locked_routes are existing copper: include them unchanged, allowing reversed traversal and equivalent collinear segmentation. Complete the other routes around them. All targets are feasible jointly. These are geometric length budgets, not electrical timing or impedance claims. The checker reports length and locked-route errors as well as collisions. Use it incrementally when useful; partial candidate checks are allowed. Final JSON must contain every net.'
        r.TOOL['description']+=' Also checks exact specified lengths, self-contact and locked copper.'
        r.run(a.output,a.sample,32000)
