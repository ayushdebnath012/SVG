import json, re, urllib.request, sys

OUT  = 'd_sft_svgx.jsonl'
N    = 3000

# Both SVGX files — GEN first (GPT-4 creative), then UN for diversity
URLS = [
    ('https://huggingface.co/datasets/xingxm/SVGX-SFT-1M'
     '/resolve/main/SVGX_SFT_GEN_51k.json'),
    ('https://huggingface.co/datasets/xingxm/SVGX-SFT-1M'
     '/resolve/main/SVGX_SFT_UN_25k.json'),
]

# viewBox matches the SVGX training data (128x128)
PROMPT = (
    "You are an expert SVG artist. Generate a detailed, high-quality SVG image for: '{}'. "
    "Use a viewBox of '0 0 128 128'. Include radial or linear gradients, realistic shading, "
    "and multiple colored elements. "
    "Return only the SVG code starting with <svg and ending with </svg>."
)

def quality_ok(svg):
    has_gradient = bool(re.search(r'<(?:radial|linear)Gradient', svg, re.IGNORECASE))
    fills  = len(re.findall(r'<(?:path|rect|circle|ellipse|polygon)[^>]+fill', svg))
    colors = set(re.findall(r'fill=["\']([^"\']+)["\']', svg, re.IGNORECASE))
    colors -= {'none', 'transparent', '', 'inherit', 'white', 'black'}
    # Gradient-rich: realistic shaded SVGs (like peach, person in suit)
    if has_gradient:
        return fills >= 3 and len(colors) >= 2 and len(svg) >= 800
    # Path-rich fallback: very detailed non-gradient SVGs
    return fills >= 10 and len(colors) >= 4 and len(svg) >= 2500

pairs = []
decoder = json.JSONDecoder()

for url in URLS:
    if len(pairs) >= N:
        break
    print(f'Streaming {url} ...', flush=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            buf = ''
            while len(pairs) < N:
                chunk = resp.read(131072).decode('utf-8', errors='ignore')
                if not chunk:
                    break
                buf += chunk

                while True:
                    stripped = buf.lstrip(' \t\n\r,[')
                    if not stripped or stripped[0] == ']':
                        buf = ''
                        break
                    offset = len(buf) - len(stripped)
                    if stripped[0] != '{':
                        buf = stripped[1:]
                        continue
                    try:
                        entry, end = decoder.raw_decode(stripped)
                        buf = stripped[end:]
                    except json.JSONDecodeError:
                        buf = stripped
                        break

                    svg_raw = entry.get('output', '')
                    inp     = entry.get('input', '')
                    desc    = re.sub(r'^SVG illustration of\s*', '', inp, flags=re.IGNORECASE).strip()
                    if not desc:
                        desc = inp.strip()
                    m = re.search(r'(<svg[\s>].*?</svg>)', svg_raw, re.DOTALL | re.IGNORECASE)
                    svg = m.group(1).strip() if m else ''
                    if svg and quality_ok(svg) and desc:
                        pairs.append((desc, svg))
                        if len(pairs) % 300 == 0:
                            print(f'  {len(pairs)}/{N} collected', flush=True)
                    if len(pairs) >= N:
                        break
    except Exception as e:
        print(f'  WARNING: {e}', flush=True)

print(f'Got {len(pairs)} pairs', flush=True)
if not pairs:
    print('ERROR: 0 pairs collected — check network/URL')
    sys.exit(1)

with open(OUT, 'w', encoding='utf-8') as f:
    for desc, svg in pairs:
        row = {
            'conversations': [
                {'from': 'human', 'value': PROMPT.format(desc[:200])},
                {'from': 'gpt',   'value': svg},
            ]
        }
        f.write(json.dumps(row, ensure_ascii=False) + '\n')

print(f'Written {len(pairs)} rows -> {OUT}')
