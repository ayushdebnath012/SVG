# ── PASTE THIS ENTIRE CELL INTO COLAB ──────────────────────────────────────
# Before running:
#   1. Runtime → Change runtime type → T4 GPU
#   2. Add HF_TOKEN in Colab Secrets (key icon on left sidebar), toggle ON

import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
    "transformers", "peft", "bitsandbytes", "accelerate",
    "cairosvg", "sentencepiece"], check=True)

import os, re, io, shutil, torch
from PIL import Image
from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel
from google.colab import files, userdata

# ── HF Token ──
os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")

# ── Upload adapter files ──
print("Upload all files from:  C:\\Users\\USER_HP\\Desktop\\CMU Project\\SVG\\finetuned_vlm_adapter\\")
print("Select all 5 files at once: adapter_config.json, adapter_model.safetensors,")
print("  tokenizer.json, tokenizer_config.json, chat_template.jinja")
os.makedirs("finetuned_vlm_adapter", exist_ok=True)
uploaded = files.upload()
for fname, data in uploaded.items():
    with open(f"finetuned_vlm_adapter/{fname}", "wb") as f:
        f.write(data)
print(f"Uploaded {len(uploaded)} files: {list(uploaded.keys())}")

# ── Load model + adapter ──
ADAPTER = "finetuned_vlm_adapter"
BASE    = "Qwen/Qwen2-VL-2B-Instruct"
print("Loading base model + LoRA adapter …")
tokenizer = AutoTokenizer.from_pretrained(ADAPTER, trust_remote_code=True)
quant = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
)
base  = Qwen2VLForConditionalGeneration.from_pretrained(
    BASE, quantization_config=quant, device_map={"": 0}, trust_remote_code=True)
model = PeftModel.from_pretrained(base, ADAPTER)
model.eval()
print("Model ready.")

# ── Inference ──
@torch.inference_mode()
def gen_svg(prompt, max_new_tokens=800):
    msgs = [
        {"role": "system", "content":
            "You are an SVG generation assistant. Given a text description of an icon, "
            "output clean minimal SVG code. Output ONLY the SVG, no explanation."},
        {"role": "user", "content": f"Generate an SVG icon for: {prompt}"},
    ]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp  = tokenizer(text, return_tensors="pt").to("cuda")
    out  = model.generate(**inp, max_new_tokens=max_new_tokens,
                          do_sample=True, temperature=0.7, top_p=0.9, repetition_penalty=1.1)
    resp = tokenizer.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True)
    m = re.search(r"(<svg[\s\S]*?</svg>)", resp)
    return m.group(1) if m else resp

def render_svg(svg, size=256):
    try:
        import cairosvg
        b = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
        return Image.open(io.BytesIO(b)).convert("RGB")
    except:
        return None

TEST_PROMPTS = [
    "a red apple", "a wifi symbol", "a coffee cup", "a rocket",
    "a music note", "a house with red roof", "a smiley face",
    "a lightning bolt", "a green tree", "a blue circle",
]

os.makedirs("test_out", exist_ok=True)
print("\n── Generating SVGs ──")
for p in TEST_PROMPTS:
    svg = gen_svg(p)
    img = render_svg(svg)
    status = "OK  " if img else "FAIL"
    print(f"  [{status}] {p:35s}  {len(svg):5d} chars")
    safe = p.replace(" ", "_")
    with open(f"test_out/{safe}.svg", "w") as f:
        f.write(svg)
    if img:
        img.save(f"test_out/{safe}.png")

# ── Download results ──
shutil.make_archive("test_out", "zip", "test_out")
print("\nDownloading test_out.zip …")
files.download("test_out.zip")
print("Done.")
