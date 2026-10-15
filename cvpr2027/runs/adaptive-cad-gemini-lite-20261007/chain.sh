#!/bin/zsh
# Gemini 3.5 Flash-Lite (Google free tier) end to end: single answers -> score -> full pipeline -> score. Resumable.
cd /Users/ayushdebnath/SVG/cvpr2027
G=(--out runs/adaptive-cad-gemini-lite-20261007 --backend gemini --model gemini-3.5-flash-lite --rpm 15)
python3 -u scripts/run_adaptive_cad_benchmark.py prepare $G
for pass in 1 2 3; do
  python3 -u scripts/run_adaptive_cad_benchmark.py single $G --lanes 6
  n=$(ls runs/adaptive-cad-gemini-lite-20261007/single/*/response.txt 2>/dev/null | wc -l | tr -d ' ')
  echo "SINGLE-PASS $pass answered $n/124"
  [ "$n" = "124" ] && break
done
[ "$n" = "124" ] || { echo "STOP single answers incomplete ($n/124)"; exit 1; }
python3 -u scripts/run_adaptive_cad_benchmark.py score-single $G || exit 1
python3 -u scripts/run_adaptive_cad_benchmark.py run $G --lanes 4 --seconds 2400
python3 -u scripts/run_adaptive_cad_benchmark.py score $G
echo CHAIN-END
