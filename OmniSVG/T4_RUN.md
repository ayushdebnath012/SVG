# OmniSVG on a T4 GPU

Use the 4B model on T4. The 8B model is not a safe target for 16 GB VRAM.

## Setup

Use Python 3.10 with CUDA-enabled PyTorch. On Kaggle/Colab T4, verify:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no cuda")
PY
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Web Server

```bash
python server.py --host 0.0.0.0 --port 8000 --model-size 4B
```

The loader enables 4-bit NF4 automatically when GPU VRAM is below 20 GB, so a T4 uses quantized weights.

Recommended first settings:

- Max tokens: 512
- Candidates: 1
- Temperature: 0.5
- Top-p: 0.88
- Top-k: 50

Increase max tokens to 1024 only after the basic run is stable.

## CLI

```bash
python generate_svg.py "a red heart icon" --model-size 4B --max-tokens 512 --num-candidates 1 --output heart.svg
```

For batch inference:

```bash
python inference.py --task text-to-svg --input prompts.txt --output outputs --model-size 4B --max-length 1024 --num-candidates 1 --save-png
```
