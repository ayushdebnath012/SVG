"""Rasterise saved SVG drawings with headless Chrome and tile them into a gallery figure.

Cairo is not required. Chrome is used only as a renderer; nothing is uploaded.
The gallery shows the drawings as produced, so labels, legends and layout are
visible, unlike the evaluator overlays, which plot only the sampled contours.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'chromium', 'chromium-browser']


def chrome():
    for candidate in CHROME:
        path = candidate if Path(candidate).exists() else shutil.which(candidate)
        if path:
            return path
    raise SystemExit('No Chrome/Chromium found; install one or render the SVGs another way')


def render(svg, png, size=1000):
    subprocess.run([chrome(), '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={size},{size}',
                    f'--screenshot={png}', svg.resolve().as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=ROOT / 'runs/astra-hard-20260918')
    parser.add_argument('--output', type=Path, default=ROOT / 'paper/figures/astra_hard_gallery.png')
    parser.add_argument('--columns', type=int, default=3)
    parser.add_argument('--tile', type=int, default=560)
    args = parser.parse_args()
    from PIL import Image, ImageDraw, ImageFont
    summary = json.loads((args.run / 'summary.json').read_text())
    rows = summary['rows']
    tiles = []
    work = args.run / 'rendered'
    work.mkdir(exist_ok=True)
    for row in rows:
        svg = args.run / row['id'] / 'output.svg'
        if not svg.exists():
            continue
        png = work / f"{row['id']}.png"
        render(svg, png)
        image = Image.open(png).convert('RGB').resize((args.tile, args.tile), Image.LANCZOS)
        verdict = row['outcome'].upper()
        if row['outcome'] in ('pass', 'fail'):
            verdict += f"  mean {row['mean_error_pp']:.2f} / max {row['max_error_pp']:.2f} pp"
        tiles.append((row['id'], verdict, row['outcome'], image))
        print('rendered', row['id'], flush=True)
    columns = args.columns
    n_rows = (len(tiles) + columns - 1) // columns
    header = 44
    sheet = Image.new('RGB', (columns * (args.tile + 12) + 12, n_rows * (args.tile + header + 12) + 12), 'white')
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 17)
        small = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 15)
    except OSError:
        font = small = ImageFont.load_default()
    colors = {'pass': (34, 139, 34), 'disclosed': (34, 139, 34), 'fail': (190, 30, 30)}
    for k, (tid, verdict, outcome, image) in enumerate(tiles):
        x = 12 + (k % columns) * (args.tile + 12)
        y = 12 + (k // columns) * (args.tile + header + 12)
        draw.text((x, y), tid, fill=(20, 20, 20), font=font)
        draw.text((x, y + 21), verdict, fill=colors.get(outcome, (90, 90, 90)), font=small)
        sheet.paste(image, (x, y + header))
        draw.rectangle([x - 1, y + header - 1, x + args.tile, y + header + args.tile], outline=(200, 200, 200))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    print('wrote', args.output, sheet.size)


if __name__ == '__main__':
    main()
