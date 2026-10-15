"""Reference-free adaptive graph exploration and versioned experience retrieval."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib, json, math, re, time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def edit_context(code, candidate):
    """Original lines touched by a JSON patch, so a retrieved experience shows what it edited."""
    try:
        lines = code.splitlines()
        rows = sorted({k for e in json.loads(candidate)['edits']
                       for k in range(int(e['start']), min(len(lines), int(e['start']) + max(1, int(e['delete']))))})
        return [f'{k}: {lines[k]}' for k in rows][:12]
    except Exception:
        return []


def task_input(raw):
    # Never forward corpus reference geometry, labels, scores or arbitrary extras.
    required = ('id', 'code', 'instruction')
    if any(not isinstance(raw.get(k), str) or not raw[k] for k in required):
        raise ValueError('Task requires nonempty string id, code and instruction')
    task = {k: raw[k] for k in required}
    for k, default in [('candidate', '{"edits":[]}'), ('component', raw['id']),
                       ('split', 'heldout'), ('constraints', []), ('semantics', {}),
                       ('fem', None), ('robustness', None), ('instruction_values', False),
                       ('required', ['geometry', 'constraints', 'semantics', 'fem', 'robustness'])]:
        task[k] = raw.get(k, default)
    if not set(task['required']) <= {'geometry','constraints','semantics','fem','robustness'}:
        raise ValueError('Unknown required verification stage')
    if not {'geometry','constraints','semantics'} <= set(task['required']):
        raise ValueError('Geometry, constraints and semantics are mandatory')
    return task


class Memory:
    """Load once: a run sees a frozen snapshot; heldout outcomes are quarantined."""
    def __init__(self, path, mode='frozen'):
        if mode not in ('frozen', 'online'): raise ValueError('Unknown memory mode')
        self.path, self.mode = Path(path), mode
        self.rows = [json.loads(s) for s in self.path.read_text().splitlines()] if self.path.exists() else []
        self.version = digest(self.rows)

    def retrieve(self, task, k=3, diagnosis=None):
        tokens = set(re.findall(r'\w+', task['instruction'].lower() + ' ' + str(diagnosis or '')))
        eligible = [r for r in self.rows if r.get('status') == 'PASS' and
                    r.get('task_id') != task['id'] and r.get('component') != task['component'] and
                    (r.get('split') in ('train','development') or self.mode == 'online')]
        def score(r):
            other = set(re.findall(r'\w+', r['instruction'].lower() + ' ' + ' '.join(r.get('strategies', []))))
            return len(tokens & other) / max(1, len(tokens | other))
        ranked = sorted(eligible, key=lambda r: (-score(r), r['task_id']))
        return [{k: r[k] for k in ('task_id','instruction','candidate','strategies','context') if k in r}
                for r in ranked[:k] if score(r) > 0]

    def store(self, task, node, events):
        row = dict(task_id=task['id'], component=task['component'], split=task['split'],
                   instruction=task['instruction'], candidate=node.candidate, context=edit_context(task['code'], node.candidate), status='PASS',
                   verification=node.final, strategies=sorted({e.get('strategy','')+': '+e.get('hypothesis','') for e in events if e.get('strategy')}),
                   trajectory=events, memory_parent=self.version, created=time.time())
        # Heldout records are saved for auditing but cannot enter frozen retrieval.
        destination = self.path if self.mode == 'online' or task['split'] in ('train','development') else self.path.with_suffix('.quarantine.jsonl')
        destination.parent.mkdir(parents=True, exist_ok=True)
        existing = destination.read_text().splitlines() if destination.exists() else []
        if not any(json.loads(s).get('task_id') == task['id'] and json.loads(s).get('candidate') == node.candidate for s in existing):
            with destination.open('a') as f: f.write(json.dumps(row) + '\n')
        return str(destination)


@dataclass
class Config:
    algorithm: str = 'mcts'
    max_expansions: int = 12
    max_depth: int = 4
    width: int = 2
    max_width: int = 4
    exploration: float = .7
    seconds: float = 1800

    def __post_init__(self):
        if self.algorithm not in ('mcts','best-first'): raise ValueError('Unknown search algorithm')
        if min(self.max_expansions,self.max_depth,self.width) < 1 or self.max_width < self.width or self.seconds <= 0:
            raise ValueError('Invalid search limits')


@dataclass
class Node:
    id: int
    candidate: str
    depth: int
    verdict: dict
    attempts: int = 0
    visits: int = 0
    final: dict | None = None
    edges: list = field(default_factory=list)


@dataclass
class Edge:
    parent: int
    child: int
    visits: int = 0
    total: float = 0.


def pareto(nodes):
    """All objective coordinates are maximized (costs are negated by verifier)."""
    def dominates(a,b):
        x,y=a.verdict['objectives'],b.verdict['objectives']
        return all(u>=v for u,v in zip(x,y)) and any(u>v for u,v in zip(x,y))
    return [n for n in nodes if not any(dominates(m,n) for m in nodes if m is not n)]


class Engine:
    def __init__(self, planner, verifier, memory, config=None):
        self.planner,self.verifier,self.memory=planner,verifier,memory
        self.config=config or Config(); self.nodes=[];self.edges=[];self.events=[];self.keys={}

    def emit(self, kind, **data): self.events.append(dict(event=kind, **data))

    def add(self, candidate, depth, verdict):
        # Exact candidate bytes and depth define policy state; no geometry-only merge.
        key=digest([candidate,depth])
        if key in self.keys:return self.nodes[self.keys[key]],True
        n=Node(len(self.nodes),candidate,depth,verdict);self.nodes.append(n);self.keys[key]=n.id
        return n,False

    def room(self,n):
        width=min(self.config.max_width,self.config.width+n.visits//2)
        return n.depth<self.config.max_depth and n.attempts<width

    def available(self,n):
        return self.room(n) or any(self.available(self.nodes[self.edges[e].child]) for e in n.edges)

    def path(self):
        if self.config.algorithm=='best-first':
            paths={0:[]}
            for n in self.nodes:
                if n.id not in paths:continue
                for e in n.edges:paths.setdefault(self.edges[e].child,paths[n.id]+[e])
            options=[n for n in self.nodes if self.room(n)]
            if not options:return None,None
            n=max(options,key=lambda n:(n.verdict['score']+.05/(1+n.attempts),-n.depth,-n.id))
            return n,paths[n.id]
        n=self.nodes[0];path=[]
        while not self.room(n):
            options=[self.edges[e] for e in n.edges if self.available(self.nodes[self.edges[e].child])]
            if not options:return None,None
            def uct(e):
                return float('inf') if not e.visits else e.total/e.visits+self.config.exploration*math.sqrt(math.log(1+n.visits)/e.visits)
            edge=max(options,key=uct);idx=self.edges.index(edge);path.append(idx);n=self.nodes[edge.child]
        return n,path

    def backup(self,path,value):
        seen={0};self.nodes[0].visits+=1
        for index in path:
            edge=self.edges[index];edge.visits+=1;edge.total+=value
            if edge.child not in seen:self.nodes[edge.child].visits+=1;seen.add(edge.child)

    def finalize(self,task,node):
        if node.verdict['status']=='PASS' and node.final is None:
            node.final=self.verifier(task,node.candidate,phase='final')
            self.emit('final_verification',node=node.id,status=node.final['status'])
            if node.final['status']!='PASS':
                self.emit('return_to_graph',node=node.id,diagnosis=node.final.get('diagnosis',[]))

    def run(self,raw):
        task=task_input(raw);start=time.monotonic();self.verifier.deadline=start+self.config.seconds
        self.planner.deadline=self.verifier.deadline
        experiences=self.memory.retrieve(task)
        planning_error=False
        try:
            plan=self.planner.decompose(task,experiences)
        except StopIteration:
            plan={'steps':[task['instruction']],'source':'local fallback: planner budget exhausted'}
        except Exception as error:
            planning_error=True
            plan={'steps':[],'source':'planner error','error_type':type(error).__name__}
        self.emit('decompose',plan=plan,memory_version=self.memory.version,retrieved=experiences)
        # Explicitly validate the unedited initial source as well as its saved patch.
        initial=self.verifier(task,'{"edits":[]}',phase='initial')
        self.emit('initial_state',verdict=initial)
        root,_=self.add(task['candidate'],0,self.verifier(task,task['candidate']))
        self.finalize(task,root)
        stop='planner_error' if planning_error else 'expansion_limit'
        for step in range(0 if planning_error else self.config.max_expansions):
            if time.monotonic()-start>=self.config.seconds:stop='time_limit';break
            parent,path=self.path()
            if parent is None:stop='frontier_exhausted';break
            diagnosis=(parent.final or parent.verdict).get('diagnosis',[])
            repairs=self.memory.retrieve(task,diagnosis=diagnosis)
            strategy='repair' if (parent.final or parent.verdict)['status']!='PASS' else 'diversify'
            if path and self.events and self.events[-1].get('parent')!=parent.id:
                self.emit('backtrack',to_node=parent.id)
            parent.attempts+=1
            try:
                candidate=self.planner.generate(task,plan,parent.candidate,parent.verdict,experiences,repairs,
                    [self.nodes[self.edges[e].child].candidate for e in parent.edges],strategy,diagnosis)
            except StopIteration:
                stop='planner_or_api_budget_exhausted';break
            except Exception as error:
                self.emit('generation_error',parent=parent.id,error_type=type(error).__name__)
                stop='provider_error';break
            verdict=self.verifier(task,candidate)
            child,merged=self.add(candidate,parent.depth+1,verdict)
            idx=next((e for e in parent.edges if self.edges[e].child==child.id),None)
            if idx is None:
                idx=len(self.edges);self.edges.append(Edge(parent.id,child.id));parent.edges.append(idx)
            self.backup(path+[idx],verdict['score'])
            self.emit('expand',parent=parent.id,node=child.id,merged=merged,strategy=strategy,
                      diagnosis=diagnosis,retrieved_repairs=repairs,path=path+[idx],status=verdict['status'],
                      hypothesis=getattr(self.planner,'last_hypothesis','recorded candidate'))
            self.finalize(task,child)
        bank=[n for n in self.nodes if n.verdict['status']=='PASS' and n.final and n.final['status']=='PASS']
        frontier=pareto(bank)
        chosen=max(frontier,key=lambda n:(n.verdict['score'],-n.depth,-n.id)) if frontier else None
        stored=self.memory.store(task,chosen,self.events) if chosen else None
        return dict(task_id=task['id'],status='PASS' if chosen else 'UNVERIFIED',
            prediction=chosen.candidate if chosen else task['candidate'],selected_node=chosen.id if chosen else None,
            bank=[n.id for n in bank],pareto=[n.id for n in frontier],stop=stop,
            nodes=[asdict(n) for n in self.nodes],edges=[asdict(e) for e in self.edges],events=self.events,
            config=asdict(self.config),memory_version=self.memory.version,stored=stored,
            seconds=time.monotonic()-start,api=getattr(self.planner,'accounting',{}))
