#!/bin/zsh
# Qwen3.5-35B-A3B-FP8 (self-hosted vLLM on the H100, free) end to end: single answers -> score -> full pipeline -> score.
cd /Users/ayushdebnath/SVG/cvpr2027
Q=(--out runs/adaptive-cad-open-20261007 --backend open --model Qwen/Qwen3.5-35B-A3B-FP8 --endpoint http://localhost:8011/v1/chat/completions)
for pass in 1 2 3; do
  python3 -u scripts/run_adaptive_cad_benchmark.py single $Q --lanes 12
  n=$(ls runs/adaptive-cad-open-20261007/single/*/response.txt 2>/dev/null | wc -l | tr -d ' ')
  echo "SINGLE-PASS $pass answered $n/124"
  [ "$n" = "124" ] && break
done
[ "$n" = "124" ] || { echo "STOP single answers incomplete ($n/124)"; exit 1; }
python3 -u scripts/run_adaptive_cad_benchmark.py score-single $Q || exit 1
python3 -u scripts/run_adaptive_cad_benchmark.py run $Q --lanes 6 --seconds 2400
python3 -u scripts/run_adaptive_cad_benchmark.py score $Q
echo CHAIN-END
