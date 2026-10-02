"""Separately frozen 24-net routing fixture, with a constructive feasibility proof."""
import argparse,json,random
from pathlib import Path
import cad_trace_routing as r
DATA=r.ROOT/'data/cad-large-routing';BASE_DRAW=r.drawing

def drawing(t,routes=None):
    original=r.COLORS;r.COLORS=original*4
    try:svg=BASE_DRAW(t,routes)
    finally:r.COLORS=original
    svg=svg.replace('width="760" height="760" viewBox="0 0 760 760"','width="1600" height="1370" viewBox="0 0 1600 1370"')
    for old,new in [(635,1250),(658,1275),(686,1305)]:svg=svg.replace(f'y="{old}"',f'y="{new}"')
    return svg

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen')
    for seed in range(3000,4000):
        rng=random.Random(seed);w,h=41,31;points=[(x,y) for x in range(w) for y in range(h)]
        obstacles=rng.sample(points,240);used=set(obstacles);nets=[]
        for i in range(24):
            free=[p for p in points if p not in used]
            for attempt in range(250):
                a,b=rng.sample(free,2)
                if abs(a[0]-b[0])+abs(a[1]-b[1])<12:continue
                path=r.bfs(a,b,used,w,h)
                if path is not None:
                    nets.append({'start':list(a),'end':list(b),'path':path});used.update(map(tuple,path));break
            else:break
        if len(nets)!=24:continue
        rng.shuffle(nets);reference={}
        for i,n in enumerate(nets):n['id']=chr(65+i);reference[n['id']]=r.compress(n.pop('path'))
        t={'id':'twenty_four_net_board','width':w,'height':h,'blocked':[list(p) for p in obstacles],'nets':nets}
        success=0
        for _ in range(150):
            order=list(range(24));rng.shuffle(order)
            if r.sequential(t,order) is not None:success+=1
        if success:continue
        assert r.grade(t,reference)['pass'];t.update(reference_routes=reference,generation_seed=seed)
        r.write(DATA/'tasks.json',{'version':'large-pcb-grid-v1','tasks':[t],'selection':'First seeded constructively feasible 24-net board with zero successes among 150 shuffled sequential BFS orders, chosen before model testing. Reference paths certify feasibility; this is not an infeasibility claim.','preflight':{'reference_grade':r.grade(t,reference),'successful_sequential_orders':success,'tested_orders':150},'admission':'Three fresh-context completed geometry failures under high effort and four checker calls. Truncation and interface or operational errors excluded. No router or general code executor exposed; configuration-specific only.'})
        (DATA/'source.svg').write_text(drawing(t));(DATA/'reference.svg').write_text(drawing(t,reference));r.render(DATA/'source.svg',DATA/'source.png',1650);r.render(DATA/'reference.svg',DATA/'reference.png',1650)
        print('Frozen',seed,'baseline',success,'/150',flush=True);return
    raise RuntimeError('No certified candidate found')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:r.DATA=DATA;r.drawing=drawing;r.run(a.output,a.sample)
