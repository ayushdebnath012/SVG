"""Meaningful checks for bounded expansion, selected-path backup and fallback."""
from mcts_cad_search import Search

def test_tree():
    s=Search('original',.3,False)
    a=s.add(s.root,'a',.7,True);b=s.add(s.root,'b',.1,False)
    assert s.root.visits==2 and a.visits==b.visits==1
    child=s.add(a,'a1',.9,True)
    assert s.root.visits==3 and a.visits==2 and b.visits==1
    assert s.selected() is child
    assert s.trace()[3]['parent']==1
    for _ in range(3):
        p=s.expansion_parent();assert p is not None
        s.add(p,'other',.2,False)
    assert len(s.nodes)==7 and s.expansion_parent() is None
    assert all(n.depth<=2 and len(n.children)<=2 for n in s.nodes)

def test_fallback():
    s=Search('original',.8,False)
    s.add(s.root,'eligible-but-worse',.7,True)
    assert s.selected() is s.root
    s=Search('original',.3,False)
    s.add(s.root,'invalid-high-score',.99,False)
    assert s.selected() is s.root

if __name__=='__main__':
    test_tree();test_fallback();print('MCTS bounds, path backup and fallback checks passed.')
