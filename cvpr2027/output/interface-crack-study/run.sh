#!/bin/zsh
# Independent G study for Code_Aster SSLP311 (scripts/interface_crack_g.py); levels 0-4 halve the element size per level.
cd /Users/ayushdebnath/SVG/cvpr2027
for th in 15 30 45 60; do
  for l in 0 1 2 3 4; do
    out=output/interface-crack-study/theta-$th/level-$l
    [ -f $out/result.json ] && continue
    mkdir -p $out
    tmp/fenicsx/env/bin/python scripts/interface_crack_g.py --theta $th --level $l --out $out > $out/solver.log 2>&1 && grep '^{' $out/solver.log || echo "theta $th level $l FAILED"
  done
done
echo STUDY-DONE
