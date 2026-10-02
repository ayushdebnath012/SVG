"""Larger, separately frozen routing task; same four-call checker protocol."""
import argparse,itertools,json,random
from pathlib import Path
import cad_trace_routing as r
DATA=r.ROOT/'data/cad-dense-routing'

def drawing(t,routes=None):
    # Reuse the stipulated physical rendering; enlarge the sheet for this board.
    original=r.COLORS
    r.COLORS=['#bd303e','#1869ad','#247942','#985aba','#c17619','#13878c','#733c3c','#324491','#596d23','#a13e78','#925d18','#285951']
    try:svg=BASE_DRAW(t,routes)
    finally:r.COLORS=original
    svg=svg.replace('width="760" height="760" viewBox="0 0 760 760"','width="1250" height="1050" viewBox="0 0 1250 1050"')
    for old,new in [(635,925),(658,950),(686,980)]:svg=svg.replace(f'y="{old}"',f'y="{new}"')
    return svg
BASE_DRAW=r.drawing

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen task exists')
    for seed in range(2000,10000):
        rng=random.Random(seed);w,h=31,21;points=[(x,y) for x in range(w) for y in range(h)]
        obstacles=rng.sample(points,95);used=set(obstacles);nets=[]
        for i in range(12):
            free=[p for p in points if p not in used]
            for attempt in range(100):
                a,b=rng.sample(free,2)
                if abs(a[0]-b[0])+abs(a[1]-b[1])<10:continue
                path=r.bfs(a,b,used,w,h)
                if path is not None:
                    nets.append({'start':list(a),'end':list(b)});used.update(map(tuple,path));break
            else:break
        if len(nets)!=12:continue
        rng.shuffle(nets)
        for i,n in enumerate(nets):n['id']=chr(65+i)
        t={'id':'dense_twelve_net_board','width':w,'height':h,'blocked':[list(p) for p in obstacles],'nets':nets}
        solutions=[]
        for _ in range(150):
            order=list(range(12));rng.shuffle(order);route=r.sequential(t,order)
            if route is not None:solutions.append((order,route))
        if not 1<=len(solutions)<=3:continue
        order,route=solutions[0];route={k:r.compress(v) for k,v in route.items()};assert r.grade(t,route)['pass']
        t.update(reference_routes=route,generation_seed=seed)
        r.write(DATA/'tasks.json',{'version':'dense-pcb-grid-v1','tasks':[t],'selection':'Before Astra testing: construct feasible disjoint paths, shuffle net identities, retain first seeded 12-net board with 1 to 3 successes among 150 shuffled sequential BFS routing orders. Each pair Manhattan distance at least 10. Earlier random-pair generator found no certified feasible board; no model calls were made on those candidates.','preflight':{'reference_grade':r.grade(t,route),'successful_sequential_orders':len(solutions),'tested_orders':150,'reference_order':order},'admission':'Three independent completed geometric failures under high effort and four checker calls. Exclude truncation, interface and operational errors. Configuration-specific result; no claim of inability with a routing program.'})
        (DATA/'source.svg').write_text(drawing(t));(DATA/'reference.svg').write_text(drawing(t,route))
        r.render(DATA/'source.svg',DATA/'source.png',1300);r.render(DATA/'reference.svg',DATA/'reference.png',1300)
        print('Frozen',seed,'successes',len(solutions),'/150',flush=True);return
    raise RuntimeError('No feasible case found')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:
        r.DATA=DATA;r.drawing=drawing;r.run(a.output,a.sample)
