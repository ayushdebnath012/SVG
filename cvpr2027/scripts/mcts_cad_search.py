"""Bounded CAD candidate MCTS; no reference fields are accepted by the search."""
from dataclasses import dataclass, field
import math

@dataclass(eq=False)
class Node:
    candidate: str
    value: float
    eligible: bool
    depth: int = 0
    parent: object = None
    children: list = field(default_factory=list)
    visits: int = 0
    total: float = 0.
    metadata: dict = field(default_factory=dict)

class Search:
    def __init__(self, candidate, value, eligible, width=2, depth=2, exploration=.7):
        self.root=Node(candidate,value,eligible)
        self.width,self.depth,self.exploration=width,depth,exploration
        self.nodes=[self.root];self.simulations=0

    def backup(self,node,value):
        while node is not None:
            node.visits+=1;node.total+=value;node=node.parent
        self.simulations+=1

    def uct(self,parent,child):
        if not child.visits:return float('inf')
        return child.total/child.visits+self.exploration*math.sqrt(math.log(1+parent.visits)/child.visits)

    def expansion_parent(self):
        # Terminal rollouts replay a deterministic cached proxy value. They still
        # back up only the selected path, never siblings or other ancestors.
        for _ in range(32):
            node=self.root
            while node.depth<self.depth and len(node.children)>=self.width:
                node=max(node.children,key=lambda n:self.uct(node,n))
            if node.depth<self.depth:return node
            self.backup(node,node.value)
        frontier=[n for n in self.nodes if n.depth<self.depth and len(n.children)<self.width]
        return max(frontier,key=lambda n:n.value) if frontier else None

    def add(self,parent,candidate,value,eligible,metadata=None):
        if parent.depth>=self.depth or len(parent.children)>=self.width:
            raise ValueError('Expansion exceeds the fixed search space')
        node=Node(candidate,value,eligible,parent.depth+1,parent,metadata=metadata or {})
        parent.children.append(node);self.nodes.append(node);self.backup(node,value)
        return node

    def selected(self):
        choices=[n for n in self.nodes if n.eligible]
        # Initial answer is always the fallback. Strict score improvement avoids
        # replacing it with an equal-scored or duplicate sampled candidate.
        best=max(choices,key=lambda n:n.value) if choices else self.root
        return best if best.value>self.root.value else self.root

    def trace(self):
        return [dict(node=i,parent=self.nodes.index(n.parent) if n.parent is not None else None,
                     depth=n.depth,visits=n.visits,total=n.total,value=n.value,
                     eligible=n.eligible,metadata=n.metadata) for i,n in enumerate(self.nodes)]
