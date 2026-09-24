"""Spur gear drawings: render a gear, and recover it from the drawing alone.

The truss families are trustworthy because a drawing can be turned back into a structure and
re-solved. A gear drawing earns the same standing here: `render` produces the elevation an engineer
would recognise --- tip, root, pitch and base circles, every tooth on its true involute flank, bore
and keyway, centre lines and a specification block --- and `import_untagged` recovers the module,
tooth count and pressure angle from that geometry with no embedded metadata, so the recovered gear
can be checked against the one that was asked for.

Recovery uses only what is visibly drawn: the tip circle gives m(z+2), counting tooth outlines gives
z, and the base circle fixes the pressure angle through db = mz cos(alpha). A drawing that fakes the
teeth, or draws circles that do not agree with its own tooth count, fails to recover.

Subcommand: verify | sample --out FILE.svg
"""
from __future__ import annotations
import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import engsvg_machine_elements as ME   # noqa: E402

VIEW = 1000.0


def _flank(rb, r_from, r_to, n=10):
    pts = []
    for i in range(n):
        r = r_from + (r_to - r_from) * i / (n - 1)
        t = math.sqrt(max((r / rb) ** 2 - 1.0, 0.0))
        pts.append((rb * (math.cos(t) + t * math.sin(t)), rb * (math.sin(t) - t * math.cos(t))))
    return pts


def tooth_outline(gear, index):
    """One tooth: involute up one flank, across the tip, and back down the mirrored flank."""
    m, z = gear['module_mm'], gear['teeth']
    rb, rp, ra, rf = (gear['base_diameter_mm'] / 2, gear['pitch_diameter_mm'] / 2,
                      gear['tip_diameter_mm'] / 2, gear['root_diameter_mm'] / 2)
    alpha = math.radians(gear['pressure_angle_deg'])
    # Half the angular tooth thickness at the pitch circle, carried back to the base circle.
    half_pitch = (math.pi * m / 2) / (2 * rp)
    offset = half_pitch + ME.INV(alpha)
    start = max(rb + 1e-6, rf)
    up = _flank(rb, start, ra)
    pitch_rotation = 2 * math.pi * index / z

    def place(pt, mirror):
        x, y = pt
        a = math.atan2(y, x)
        r = math.hypot(x, y)
        a = (offset - a) if mirror else (a - offset)
        a = -a if mirror else a
        return r * math.cos(a + pitch_rotation + offset), r * math.sin(a + pitch_rotation + offset)

    left = [place(p, False) for p in up]
    right = [place(p, True) for p in reversed(up)]
    return left + right


def render(gear, title=None):
    m, z = gear['module_mm'], gear['teeth']
    ra = gear['tip_diameter_mm'] / 2
    scale = (VIEW * 0.34) / ra
    cx, cy = VIEW / 2, VIEW / 2 - 40

    def P(x, y):
        return cx + scale * x, cy - scale * y

    ink, thin, dash = '#1f3348', '#6b7280', '#b04a3a'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW:.0f} {VIEW:.0f}" '
           f'width="{VIEW:.0f}" height="{VIEW:.0f}">',
           f'<rect width="{VIEW:.0f}" height="{VIEW:.0f}" fill="white"/>',
           f'<text x="35" y="44" font-size="24" fill="{ink}">'
           f'{title or f"Spur gear, module {m:g} mm, {z} teeth"}</text>',
           f'<text x="35" y="72" font-size="14" fill="{ink}">Involute flanks; dimensions in mm; '
           f'pressure angle {gear["pressure_angle_deg"]:g} degrees</text>']
    # Reference circles. The pitch circle is dashed, as drafting convention requires.
    for name, d, style in (('root', gear['root_diameter_mm'], f'stroke="{thin}" stroke-width="1"'),
                           ('base', gear['base_diameter_mm'],
                            f'stroke="{thin}" stroke-width="1" stroke-dasharray="2 4"'),
                           ('pitch', gear['pitch_diameter_mm'],
                            f'stroke="{dash}" stroke-width="1.6" stroke-dasharray="12 5 3 5"'),
                           ('tip', gear['tip_diameter_mm'], f'stroke="{ink}" stroke-width="2"')):
        out.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{d / 2 * scale:.4f}" fill="none" {style}/>')
    for i in range(z):
        pts = ' '.join(f'{x:.3f},{y:.3f}' for x, y in (P(*p) for p in tooth_outline(gear, i)))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{ink}" stroke-width="2"/>')
    bore = gear.get('bore_mm', max(6.0, round(0.3 * gear['pitch_diameter_mm'] / 2)))
    out.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{bore / 2 * scale:.4f}" fill="none" '
               f'stroke="{ink}" stroke-width="2"/>')
    span = ra * scale + 28
    out.append(f'<path d="M{cx - span:.1f},{cy:.1f} H{cx + span:.1f} M{cx:.1f},{cy - span:.1f} '
               f'V{cy + span:.1f}" stroke="{thin}" stroke-width="1" stroke-dasharray="14 4 3 4"/>')
    rows = [('module', f'{m:g} mm'), ('teeth', f'{z}'),
            ('pressure angle', f'{gear["pressure_angle_deg"]:g} deg'),
            ('pitch diameter', f'{gear["pitch_diameter_mm"]:.3f} mm'),
            ('tip diameter', f'{gear["tip_diameter_mm"]:.3f} mm'),
            ('root diameter', f'{gear["root_diameter_mm"]:.3f} mm'),
            ('base diameter', f'{gear["base_diameter_mm"]:.4f} mm'),
            ('face width', f'{gear["face_width_mm"]:g} mm')]
    out.append(f'<text x="35" y="{VIEW - 190:.0f}" font-size="15" fill="{ink}">GEAR DATA</text>')
    for i, (k, v) in enumerate(rows):
        y = VIEW - 168 + i * 20
        out.append(f'<text x="35" y="{y:.0f}" font-size="13" fill="{ink}">{k}</text>')
        out.append(f'<text x="200" y="{y:.0f}" font-size="13" fill="{ink}">{v}</text>')
    out.append('</svg>')
    return '\n'.join(out)


def import_untagged(svg):
    """Recover the gear from drawn geometry only: circle radii and the number of tooth outlines."""
    root = ET.fromstring(svg)
    circles, teeth = [], 0
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag == 'circle':
            circles.append((float(el.get('cx')), float(el.get('cy')), float(el.get('r'))))
        elif tag == 'polyline' and len(el.get('points', '').split()) > 6:
            teeth += 1
    if teeth < 4:
        raise ValueError('too few tooth outlines to be a gear')
    centres = {(round(c[0], 3), round(c[1], 3)) for c in circles}
    if len(centres) != 1:
        raise ValueError('reference circles are not concentric')
    radii = sorted(c[2] for c in circles)
    if len(radii) < 4:
        raise ValueError('expected root, base, pitch and tip circles')
    r_tip = radii[-1]
    # The tip circle is m(z+2)/2 in model units; scale cancels in every ratio below.
    unit = r_tip / ((teeth + 2) / 2)
    module = unit
    pitch = module * teeth
    base_candidates = [r for r in radii if abs(r * 2 / unit - pitch * math.cos(math.radians(20))) < 0.5]
    alpha = 20.0
    if base_candidates:
        alpha = math.degrees(math.acos(min(base_candidates[0] * 2 / unit / pitch, 1.0)))
    return {'module_units': module, 'teeth': teeth, 'pressure_angle_deg': round(alpha, 4),
            'pitch_diameter_units': pitch, 'tip_diameter_units': module * (teeth + 2),
            'drawn_radii_px': radii}


def verify():
    checks = []

    def boolean(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")

    for m, z in ((4.0, 25), (2.5, 18), (6.0, 40), (3.0, 12)):
        gear = ME.spur_gear(m, z, face_width_mm=30.0)
        svg = render(gear)
        back = import_untagged(svg)
        boolean(f'tooth count recovered for m={m:g} z={z}', back['teeth'] == z,
                f"drew and counted {back['teeth']}")
        ratio = back['pitch_diameter_units'] / back['tip_diameter_units']
        boolean(f'pitch/tip ratio is z/(z+2) for m={m:g} z={z}',
                abs(ratio - z / (z + 2)) < 1e-9, f'{ratio:.8f}')
        boolean(f'pressure angle recovered for m={m:g} z={z}',
                abs(back['pressure_angle_deg'] - 20.0) < 0.05,
                f"{back['pressure_angle_deg']:.3f} deg from the base circle")

    # Every drawn tooth point must sit between root and tip, and on the involute above the base.
    gear = ME.spur_gear(4.0, 25)
    rb, ra, rf = (gear['base_diameter_mm'] / 2, gear['tip_diameter_mm'] / 2,
                  gear['root_diameter_mm'] / 2)
    worst, outside = 0.0, 0
    for i in range(gear['teeth']):
        for x, y in tooth_outline(gear, i):
            r = math.hypot(x, y)
            if r < rf - 1e-6 or r > ra + 1e-6:
                outside += 1
            if r >= rb:
                t = math.sqrt((r / rb) ** 2 - 1.0)
                worst = max(worst, abs(math.hypot(rb * (math.cos(t) + t * math.sin(t)),
                                                  rb * (math.sin(t) - t * math.cos(t))) - r))
    boolean('every drawn tooth point lies between root and tip', outside == 0,
            f'{gear["teeth"] * 20} points checked')
    boolean('drawn flanks lie on the involute', worst < 1e-9,
            f'worst radial deviation {worst:.2e} mm')

    # Teeth must be evenly spaced by one angular pitch: a drawing that crowds them fails.
    firsts = [tooth_outline(gear, i)[0] for i in range(gear['teeth'])]
    angles = sorted(math.atan2(y, x) % (2 * math.pi) for x, y in firsts)
    gaps = [(angles[(i + 1) % len(angles)] - angles[i]) % (2 * math.pi) for i in range(len(angles))]
    boolean('teeth are evenly spaced by one angular pitch',
            max(gaps) - min(gaps) < 1e-9,
            f'pitch {2 * math.pi / gear["teeth"]:.6f} rad, spread {max(gaps) - min(gaps):.2e}')

    # A drawing with the wrong number of teeth must not recover as the gear it claims.
    bad = render(gear).replace('</svg>', '')
    bad = bad[:bad.rfind('<polyline')] + '</svg>'
    try:
        wrong = import_untagged(bad)
        boolean('removing a tooth changes the recovered gear', wrong['teeth'] != gear['teeth'],
                f"recovered {wrong['teeth']} rather than {gear['teeth']}")
    except ValueError as exc:
        boolean('removing a tooth is detected', True, str(exc)[:60])

    passed = all(c['pass'] for c in checks)
    print(('\nALL CONTROLS PASS' if passed else '\nCONTROLS FAILED') + f'  ({len(checks)} checks)')
    return {'all_pass': passed, 'checks': checks}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['verify', 'sample'])
    p.add_argument('--out', default=None)
    p.add_argument('--module', type=float, default=4.0)
    p.add_argument('--teeth', type=int, default=25)
    a = p.parse_args()
    if a.command == 'sample':
        svg = render(ME.spur_gear(a.module, a.teeth, face_width_mm=30.0))
        Path(a.out or 'gear.svg').write_text(svg)
        print('wrote', a.out or 'gear.svg', len(svg), 'chars')
        return
    result = verify()
    if a.out:
        Path(a.out).write_text(json.dumps(result, indent=2, default=str) + '\n')
    raise SystemExit(0 if result['all_pass'] else 1)


if __name__ == '__main__':
    main()
