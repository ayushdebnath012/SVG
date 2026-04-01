import vtracer, re, io
from PIL import Image

img = Image.open(r"F:\SVG-20260310T151742Z-1-001\SVG\diffusvg_output_all (1)\dataset\images\00000.png")
img = img.convert("RGBA").resize((512, 512), Image.LANCZOS)

# Convert to PNG bytes in memory
buf = io.BytesIO()
img.save(buf, format="PNG")
png_bytes = buf.getvalue()

svg = vtracer.convert_raw_image_to_svg(
    png_bytes,
    img_format="png",
    colormode="color",
    hierarchical="stacked",
    mode="spline",
    filter_speckle=4,
    color_precision=6,
    corner_threshold=60,
    length_threshold=4.0,
    max_iterations=10,
    splice_threshold=45,
    path_precision=3,
)

with open("test_vtracer_output.svg", "w") as f:
    f.write(svg)

fills = set(re.findall(r'fill="([^"]+)"', svg))
paths = len(re.findall(r'<path', svg))
print(f"Paths: {paths}")
print(f"Unique fill colours: {len(fills)}")
print(f"Sample colours: {list(fills)[:10]}")
print(f"SVG length: {len(svg)} chars")
print("SUCCESS!")
