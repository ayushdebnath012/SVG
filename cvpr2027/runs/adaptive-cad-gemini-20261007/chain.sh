#!/bin/zsh
# Gemini (free tier) end to end: single answers (retry passes) -> score -> full pipeline -> score. Resumable.
cd /Users/ayushdebnath/SVG/cvpr2027
G=(--out runs/adaptive-cad-gemini-20261007 --backend gemini --model gemini-3.7-flash --rpm 10)
for pass in 1 2 3; do
  python3 -u scripts/run_adaptive_cad_benchmark.py single $G --lanes 8
  n=$(ls -d runs/adaptive-cad-gemini-20261007/single/*/ 2>/dev/null | grep -v -- -rejected- | wc -l | tr -d ' ')
  echo "SINGLE-PASS $pass answered $n/124"
  [ "$n" = "124" ] && break
done
[ "$n" = "124" ] || { echo "STOP single answers incomplete ($n/124)"; exit 1; }
python3 -u scripts/run_adaptive_cad_benchmark.py score-single $G || exit 1
python3 -u scripts/run_adaptive_cad_benchmark.py run $G --lanes 8 --seconds 3600
python3 -u scripts/run_adaptive_cad_benchmark.py score $G
echo CHAIN-END
