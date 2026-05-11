"""
OmniSVG Web Server
==================
FastAPI backend that wraps OmniSVG text-to-SVG generation.

Run:
    python server.py                          # default: port 8000, 4B model
    python server.py --port 8080 --model-size 8B
    python server.py --model-path /local/qwen --weight-path /local/weights
"""

import os
import sys
import gc
import io
import uuid
import time
import base64
import asyncio
import argparse
import threading
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import torch
import yaml
import numpy as np
from PIL import Image

# ── FastAPI ────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ── Config ─────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
CONFIG_PATH = str(BASE_DIR / "config.yaml")
STATIC_DIR  = BASE_DIR / "static"

with open(CONFIG_PATH) as f:
    _cfg = yaml.safe_load(f)

_model_cfg    = _cfg.get("model", {})
BOS_TOKEN_ID  = _model_cfg.get("bos_token_id", 196998)
EOS_TOKEN_ID  = _model_cfg.get("eos_token_id", 196999)
PAD_TOKEN_ID  = _model_cfg.get("pad_token_id", 151643)

_colors_cfg       = _cfg.get("colors", {})
BLACK_COLOR_TOKEN = _colors_cfg.get("black_color_token",
                                    _colors_cfg.get("color_token_start", 40010) + 2)

_image_cfg         = _cfg.get("image", {})
TARGET_SIZE        = _image_cfg.get("target_size", 448)
RENDER_SIZE        = _image_cfg.get("render_size", 1024)
EMPTY_THRESH_IL    = _image_cfg.get("empty_threshold_illustration", 250)
EMPTY_THRESH_IC    = _image_cfg.get("empty_threshold_icon", 252)

TASK_DEFAULTS = {
    "icon":         {"temperature": 0.5,  "top_p": 0.88, "top_k": 50, "repetition_penalty": 1.05},
    "illustration": {"temperature": 0.6,  "top_p": 0.90, "top_k": 60, "repetition_penalty": 1.03},
}

ICON_KW = {"icon","logo","symbol","badge","button","emoji","glyph","simple",
           "arrow","triangle","circle","square","heart","star","checkmark"}
ILLUS_KW = {"illustration","scene","person","people","character","man","woman","boy","girl",
            "avatar","portrait","face","head","body","cat","dog","bird","animal","pet",
            "fox","rabbit","sitting","standing","walking","running","sleeping","holding",
            "playing","house","building","tree","garden","landscape","mountain","forest",
            "city","ocean","beach","sunset","sunrise","sky"}

SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Generate precise, valid SVG path commands that accurately represent the described scene or object. "
    "Focus on capturing key shapes, spatial relationships, and visual composition."
)

# ── Global model state ─────────────────────────────────────────────────────
_model_lock     = threading.Lock()
_infer_executor = ThreadPoolExecutor(max_workers=1)   # one generation at a time

processor      = None
decoder        = None
svg_tok        = None
model_ready    = False
model_error    = None
dtype          = None

# ── Job store (in-memory) ──────────────────────────────────────────────────
_jobs: dict[str, dict] = {}    # job_id -> {status, svg, error, created_at}
JOB_TTL = 600                  # seconds to keep finished jobs


# ── Helpers ────────────────────────────────────────────────────────────────

def _detect_subtype(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ICON_KW):
        return "icon"
    if sum(1 for k in ILLUS_KW if k in lower) >= 1 or len(text) > 50:
        return "illustration"
    return "icon"


def _render_svg(svg_str: str, size: int = RENDER_SIZE) -> Image.Image | None:
    try:
        import cairosvg
        png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=size, output_height=size)
        rgba = Image.open(io.BytesIO(png)).convert("RGBA")
        bg   = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[3])
        return bg
    except Exception as e:
        print(f"[render] {e}")
        return None


def _pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _is_valid(svg_str: str, img, subtype: str) -> tuple[bool, str]:
    if not svg_str or len(svg_str) < 20:
        return False, "too_short"
    if "<svg" not in svg_str:
        return False, "no_svg_tag"
    if img is None:
        return False, "render_failed"
    thresh = EMPTY_THRESH_IL if subtype == "illustration" else EMPTY_THRESH_IC
    if np.array(img).mean() > thresh:
        return False, "empty_image"
    return True, "ok"


def _get_embed_device():
    try:
        m = decoder.transformer
        if hasattr(m, "model") and hasattr(m.model, "embed_tokens"):
            return next(m.model.embed_tokens.parameters()).device
        return next(m.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def _extra_candidate_buffer() -> int:
    """Use extra reranking candidates only on GPUs with comfortable VRAM."""
    if not torch.cuda.is_available():
        return 0
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    return 0 if vram_gb < 20 else 4


# ── Model loading ──────────────────────────────────────────────────────────

def load_model(model_size: str, model_path: str | None, weight_path: str | None):
    """Blocking model load — called once from a background thread at startup."""
    global processor, decoder, svg_tok, model_ready, model_error, dtype

    try:
        from transformers import AutoProcessor
        from decoder import SketchDecoder
        from tokenizer import SVGTokenizer
        from huggingface_hub import hf_hub_download

        models_cfg = _cfg.get("models", {}).get(model_size, {})
        hf_cfg     = models_cfg.get("huggingface", {})

        if model_path is None:
            model_path = hf_cfg.get("qwen_model", "Qwen/Qwen2.5-VL-3B-Instruct")
        if weight_path is None:
            weight_path = hf_cfg.get("omnisvg_model", "OmniSVG/OmniSVG1.1_4B")

        dtype = (torch.bfloat16
                 if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
                 else torch.float16)

        print(f"\n[server] Loading {model_size} model …")
        print(f"  backbone : {model_path}")
        print(f"  weights  : {weight_path}")
        print(f"  dtype    : {dtype}")

        # processor
        processor = AutoProcessor.from_pretrained(
            model_path, padding_side="left", trust_remote_code=True
        )
        processor.tokenizer.padding_side = "left"

        # 4-bit for low-VRAM
        use_4bit = False
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            if vram_gb < 20:
                use_4bit = True
                print(f"  Low-VRAM ({vram_gb:.1f} GB) — 4-bit NF4 quantization enabled")

        decoder = SketchDecoder(
            config_path=CONFIG_PATH,
            model_path=model_path,
            model_size=model_size,
            pix_len=2048,
            text_len=_cfg.get("text", {}).get("max_length", 200),
            torch_dtype=dtype,
            use_4bit=use_4bit,
        )

        # resolve weights
        if os.path.isdir(weight_path):
            bin_path = os.path.join(weight_path, "pytorch_model.bin")
        elif os.path.isfile(weight_path):
            bin_path = weight_path
        else:
            print(f"  Downloading weights from HF hub: {weight_path} …")
            bin_path = hf_hub_download(
                repo_id=weight_path, filename="pytorch_model.bin", resume_download=True
            )

        # Keep the checkpoint on CPU while loading. Mapping the full state dict
        # directly to a 16 GB T4 can cause a temporary VRAM spike before weights
        # are copied into the already-quantized model.
        state = torch.load(bin_path, map_location="cpu", weights_only=False)
        missing, unexpected = decoder.load_state_dict(state, strict=False)
        if missing:
            print(f"  [warn] Missing keys: {len(missing)}")
        decoder.eval()

        svg_tok     = SVGTokenizer(CONFIG_PATH, model_size=model_size)
        model_ready = True
        print(f"[server] Model ready.\n")

    except Exception as exc:
        model_error = str(exc)
        print(f"[server] Model load failed: {exc}")
        raise


# ── Core inference (runs in executor thread) ───────────────────────────────

def _run_generation(
    text: str,
    temperature: float,
    top_p: float,
    top_k: int,
    repetition_penalty: float,
    max_new_tokens: int,
    num_candidates: int,
) -> str:
    """Synchronous generation; returns SVG string or raises RuntimeError."""
    subtype = _detect_subtype(text)

    instruction = (
        f"Generate an SVG illustration for: {text}\n\n"
        "Requirements:\n"
        "- Create complete SVG path commands\n"
        "- Include proper coordinates and colors\n"
        "- Maintain visual clarity and composition"
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": [{"type": "text", "text": instruction}]},
    ]
    text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs     = processor(text=[text_input], padding=True, truncation=True, return_tensors="pt")

    dev        = _get_embed_device()
    input_ids  = inputs["input_ids"].to(dev)
    attn_mask  = inputs["attention_mask"].to(dev)

    with torch.no_grad():
        outputs = decoder.transformer.generate(
            input_ids=input_ids,
            attention_mask=attn_mask,
            max_new_tokens=max_new_tokens,
            num_return_sequences=num_candidates + _extra_candidate_buffer(),
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            top_k=int(top_k),
            repetition_penalty=repetition_penalty,
            early_stopping=True,
            eos_token_id=EOS_TOKEN_ID,
            pad_token_id=PAD_TOKEN_ID,
            bos_token_id=BOS_TOKEN_ID,
            use_cache=True,
        )
        new_ids = outputs[:, input_ids.shape[1]:]

    for i in range(new_ids.shape[0]):
        try:
            ids_cpu = new_ids[i : i + 1].cpu()
            wrapped = torch.cat([
                torch.full((1, 1), BOS_TOKEN_ID),
                ids_cpu,
                torch.full((1, 1), EOS_TOKEN_ID),
            ], dim=1)

            xy = svg_tok.process_generated_tokens(wrapped)
            if len(xy) == 0:
                continue

            svg_tensors, color_tensors = svg_tok.raster_svg(xy)
            if not svg_tensors or not svg_tensors[0]:
                continue

            num_paths = len(svg_tensors[0])
            while len(color_tensors) < num_paths:
                color_tensors.append(BLACK_COLOR_TOKEN)

            svg     = svg_tok.apply_colors_to_svg(svg_tensors[0], color_tensors)
            svg_str = svg.to_str()

            if "width=" not in svg_str:
                svg_str = svg_str.replace(
                    "<svg", f'<svg width="{TARGET_SIZE}" height="{TARGET_SIZE}"', 1
                )

            img = _render_svg(svg_str)
            ok, reason = _is_valid(svg_str, img, subtype)
            if ok:
                return svg_str

        except Exception as e:
            print(f"  [candidate {i}] {e}")
            continue

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    raise RuntimeError("No valid SVG could be generated. Try different wording or adjust settings.")


def _job_worker(job_id: str, **kwargs):
    """Called in the thread-pool executor; updates job store."""
    try:
        svg = _run_generation(**kwargs)
        img = _render_svg(svg, size=512)
        _jobs[job_id].update({
            "status":    "done",
            "svg":       svg,
            "thumbnail": _pil_to_b64(img) if img else None,
            "finished":  time.time(),
        })
    except Exception as exc:
        _jobs[job_id].update({
            "status":   "error",
            "error":    str(exc),
            "finished": time.time(),
        })
    finally:
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# ── FastAPI app ────────────────────────────────────────────────────────────

app = FastAPI(title="OmniSVG", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ── API schemas ────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt:             str   = Field(..., min_length=3, max_length=500)
    temperature:        float = Field(None, ge=0.1, le=1.5)
    top_p:              float = Field(None, ge=0.1, le=1.0)
    top_k:              int   = Field(None, ge=1,   le=200)
    repetition_penalty: float = Field(None, ge=1.0, le=1.5)
    max_new_tokens:     int   = Field(512, ge=256,  le=4096)
    num_candidates:     int   = Field(1,   ge=1,    le=8)


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status":      "ready" if model_ready else ("error" if model_error else "loading"),
        "model_error": model_error,
        "cuda":        torch.cuda.is_available(),
        "gpu":         (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None),
    }


@app.post("/api/generate")
def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    if not model_ready:
        if model_error:
            raise HTTPException(503, f"Model failed to load: {model_error}")
        raise HTTPException(503, "Model is still loading, please wait …")

    subtype  = _detect_subtype(req.prompt)
    defaults = TASK_DEFAULTS[subtype]

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "created_at": time.time()}

    kwargs = dict(
        text               = req.prompt,
        temperature        = req.temperature        or defaults["temperature"],
        top_p              = req.top_p              or defaults["top_p"],
        top_k              = req.top_k              or defaults["top_k"],
        repetition_penalty = req.repetition_penalty or defaults["repetition_penalty"],
        max_new_tokens     = req.max_new_tokens,
        num_candidates     = req.num_candidates,
    )

    _infer_executor.submit(_job_worker, job_id, **kwargs)

    return {"job_id": job_id, "subtype": subtype}


@app.get("/api/job/{job_id}")
def get_job(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    # expire old done jobs
    now = time.time()
    for jid in list(_jobs.keys()):
        j = _jobs[jid]
        if j.get("finished") and now - j["finished"] > JOB_TTL:
            del _jobs[jid]

    return job


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "Frontend not found")
    return HTMLResponse(index.read_text(encoding="utf-8"))


# Serve static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── CLI entry-point ────────────────────────────────────────────────────────

def _parse_args():
    p = argparse.ArgumentParser(description="OmniSVG Web Server")
    p.add_argument("--host",        default="0.0.0.0")
    p.add_argument("--port",        type=int, default=8000)
    p.add_argument("--model-size",  default="4B", choices=["4B", "8B"])
    p.add_argument("--model-path",  default=None,
                   help="Local path or HF repo for Qwen backbone")
    p.add_argument("--weight-path", default=None,
                   help="Local path or HF repo for OmniSVG weights")
    p.add_argument("--reload",      action="store_true",
                   help="Hot-reload (dev mode, CPU only)")
    return p.parse_args()


def main():
    args = _parse_args()

    # Load model in a daemon thread so the HTTP server starts immediately
    # (health endpoint returns "loading" until it's ready)
    t = threading.Thread(
        target=load_model,
        args=(args.model_size, args.model_path, args.weight_path),
        daemon=True,
    )
    t.start()

    print(f"\n[server] Starting OmniSVG web server at http://{args.host}:{args.port}")
    print(f"[server] Open http://localhost:{args.port} in your browser\n")

    # Pass the app object directly (not a string) so uvicorn shares this
    # module's globals — including model_ready — with the background thread.
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
