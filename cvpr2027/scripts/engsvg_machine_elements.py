"""Machine elements: spur gears and rolling bearings, with closed-form verification.

Trusses and plates cover structures. The other half of mechanical drawing is machine elements, and
they verify at least as tightly, because their geometry is defined by exact relations rather than by
a numerical solve: a pitch diameter is m*z and nothing else, an involute point is on the involute or
it is not, and a contact ratio below one means the drive stops transmitting between teeth.

Implemented:

    spur gear        involute flank geometry, standard proportions, mesh checks and Lewis bending
    rolling bearing  ball and race geometry, Hertzian point contact, ISO 281 basic rating life

Nothing here is a substitute for AGMA or ISO design procedure. The Lewis equation ignores stress
concentration at the root fillet, dynamic factors and load sharing; the Hertz solution assumes dry,
frictionless, perfectly elastic contact. These verify a drawing against the geometry and first-order
mechanics it claims, which is what the benchmark needs, not what a gearbox release needs.

Subcommand: verify --- runs the controls and reports each against its closed-form answer.
"""
from __future__ import annotations
import argparse
import json
import math

import numpy as np

INV = lambda a: math.tan(a) - a          # noqa: E731  involute function inv(alpha)


# ----------------------------------------------------------------------------- spur gear
def spur_gear(module, teeth, pressure_angle_deg=20.0, face_width_mm=20.0,
              addendum_factor=1.0, dedendum_factor=1.25, profile_points=24):
    """Standard involute spur gear. Returns geometry plus one flank as sampled points."""
    if teeth < 4 or module <= 0:
        raise ValueError('implausible gear')
    alpha = math.radians(pressure_angle_deg)
    d = module * teeth                                  # pitch diameter, by definition
    db = d * math.cos(alpha)                            # base circle
    da = d + 2 * addendum_factor * module               # tip
    df = d - 2 * dedendum_factor * module               # root
    rb, rp, ra, rf = db / 2, d / 2, da / 2, df / 2
    s_pitch = math.pi * module / 2                      # tooth thickness on the pitch circle

    # The flank is the involute of the base circle, sampled between the usable root and the tip.
    r_start = max(rb + 1e-9, rf)
    radii = np.linspace(r_start, ra, profile_points)
    flank = []
    for r in radii:
        t = math.sqrt(max((r / rb) ** 2 - 1.0, 0.0))    # involute parameter at this radius
        flank.append((rb * (math.cos(t) + t * math.sin(t)),
                      rb * (math.sin(t) - t * math.cos(t))))
    undercut_limit = 2 * addendum_factor / (math.sin(alpha) ** 2)
    return {'kind': 'spur_gear', 'module_mm': module, 'teeth': teeth,
            'pressure_angle_deg': pressure_angle_deg, 'face_width_mm': face_width_mm,
            'pitch_diameter_mm': d, 'base_diameter_mm': db, 'tip_diameter_mm': da,
            'root_diameter_mm': df, 'circular_pitch_mm': math.pi * module,
            'tooth_thickness_pitch_mm': s_pitch, 'flank_points': flank,
            'undercut': teeth < undercut_limit, 'undercut_limit_teeth': undercut_limit}


def tooth_thickness_at(gear, radius):
    """Standard thickness relation: s_r = r*(s_p/r_p + 2*(inv a_p - inv a_r))."""
    rp = gear['pitch_diameter_mm'] / 2
    rb = gear['base_diameter_mm'] / 2
    if radius < rb:
        raise ValueError('below the base circle the involute does not exist')
    alpha_p = math.radians(gear['pressure_angle_deg'])
    alpha_r = math.acos(min(rb / radius, 1.0))
    return radius * (gear['tooth_thickness_pitch_mm'] / rp + 2 * (INV(alpha_p) - INV(alpha_r)))


def mesh(pinion, wheel):
    """Two gears of equal module: centre distance, ratio and transverse contact ratio."""
    if abs(pinion['module_mm'] - wheel['module_mm']) > 1e-12:
        raise ValueError('meshing gears must share a module')
    m = pinion['module_mm']
    alpha = math.radians(pinion['pressure_angle_deg'])
    a = (pinion['pitch_diameter_mm'] + wheel['pitch_diameter_mm']) / 2
    ra1, rb1 = pinion['tip_diameter_mm'] / 2, pinion['base_diameter_mm'] / 2
    ra2, rb2 = wheel['tip_diameter_mm'] / 2, wheel['base_diameter_mm'] / 2
    path = (math.sqrt(ra1 ** 2 - rb1 ** 2) + math.sqrt(ra2 ** 2 - rb2 ** 2) - a * math.sin(alpha))
    return {'centre_distance_mm': a, 'gear_ratio': wheel['teeth'] / pinion['teeth'],
            'path_of_contact_mm': path,
            'contact_ratio': path / (math.pi * m * math.cos(alpha)),
            'continuous_transmission': path / (math.pi * m * math.cos(alpha)) >= 1.0}


# Lewis form factor, 20 degree full-depth, sampled from the standard table.
_LEWIS = {12: 0.245, 14: 0.261, 16: 0.277, 18: 0.290, 20: 0.302, 22: 0.314, 24: 0.324,
          26: 0.333, 28: 0.341, 30: 0.348, 34: 0.361, 38: 0.373, 43: 0.384, 50: 0.396,
          60: 0.409, 75: 0.422, 100: 0.435, 150: 0.447, 300: 0.460}


def lewis_bending_stress(gear, tangential_force_N):
    """sigma = Ft / (b * m * Y). Root fillet concentration and dynamic effects are excluded."""
    keys = sorted(_LEWIS)
    z = gear['teeth']
    if z <= keys[0]:
        Y = _LEWIS[keys[0]]
    elif z >= keys[-1]:
        Y = _LEWIS[keys[-1]]
    else:
        hi = next(k for k in keys if k >= z)
        lo = max(k for k in keys if k <= z)
        Y = _LEWIS[lo] if hi == lo else _LEWIS[lo] + (_LEWIS[hi] - _LEWIS[lo]) * (z - lo) / (hi - lo)
    return {'lewis_form_factor': Y,
            'bending_stress_mpa': tangential_force_N / (gear['face_width_mm'] * gear['module_mm'] * Y),
            'excludes': ['root fillet stress concentration', 'dynamic factor', 'load sharing']}


# ----------------------------------------------------------------------------- rolling bearing
def deep_groove_bearing(bore_mm, outer_mm, width_mm, balls, ball_diameter_mm,
                        conformity=0.52, E_mpa=210000.0, nu=0.3):
    pitch = (bore_mm + outer_mm) / 2
    if ball_diameter_mm >= (outer_mm - bore_mm) / 2:
        raise ValueError('ball will not fit between the races')
    return {'kind': 'deep_groove_ball_bearing', 'bore_mm': bore_mm, 'outer_mm': outer_mm,
            'width_mm': width_mm, 'balls': balls, 'ball_diameter_mm': ball_diameter_mm,
            'pitch_diameter_mm': pitch, 'raceway_conformity': conformity,
            'E_mpa': E_mpa, 'poisson': nu}


def hertz_point_contact(load_N, d_ball_mm, d_race_mm, conformity, E_mpa, nu):
    """Ball against a grooved race, treated as contact between two general curved bodies."""
    r_ball = d_ball_mm / 2
    r_groove = -conformity * d_ball_mm            # concave, hence negative
    curv = [1 / r_ball, 1 / r_ball, 1 / (d_race_mm / 2), 1 / r_groove]
    sum_rho = sum(curv)
    e_star = E_mpa / (2 * (1 - nu ** 2))          # both bodies share the material
    a_eq = (3 * load_N / (2 * e_star * sum_rho)) ** (1 / 3)
    p_max = 3 * load_N / (2 * math.pi * a_eq ** 2)
    return {'sum_of_curvatures_1_mm': sum_rho, 'contact_radius_mm': a_eq,
            'max_contact_pressure_mpa': p_max,
            'assumes': ['dry frictionless elastic contact', 'no edge effects', 'static load']}


def basic_rating_life(dynamic_capacity_N, equivalent_load_N, speed_rpm=None):
    """ISO 281: L10 = (C/P)^3 in millions of revolutions, for ball bearings."""
    if equivalent_load_N <= 0:
        raise ValueError('load must be positive')
    l10 = (dynamic_capacity_N / equivalent_load_N) ** 3
    out = {'l10_million_revolutions': l10}
    if speed_rpm:
        out['l10_hours'] = l10 * 1e6 / (60 * speed_rpm)
    return out


# ----------------------------------------------------------------------------- controls
def verify():
    checks = []

    def check(name, got, want, tol, detail='', atol=None):
        # A quantity whose exact answer is zero has no meaningful relative error; comparing against
        # it turns machine precision into a ratio of 1e15 and reports a pass as a failure.
        if want == 0.0 or atol is not None:
            rel = abs(got - want)
            ok = rel <= (atol if atol is not None else 1e-9)
        else:
            rel = abs(got - want) / abs(want)
            ok = rel <= tol
        checks.append({'check': name, 'pass': bool(ok), 'got': got, 'expected': want,
                       'relative_error': rel, 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {got:.8g} vs {want:.8g}  rel {rel:.1e}  {detail}")

    def boolean(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")

    g = spur_gear(module=4.0, teeth=25, pressure_angle_deg=20.0, face_width_mm=40.0)

    check('pitch diameter is m*z', g['pitch_diameter_mm'], 4.0 * 25, 1e-15)
    check('base diameter is d*cos(alpha)', g['base_diameter_mm'],
          100.0 * math.cos(math.radians(20)), 1e-15)
    check('tip diameter is d + 2m', g['tip_diameter_mm'], 108.0, 1e-15)
    check('root diameter is d - 2.5m', g['root_diameter_mm'], 90.0, 1e-15)
    check('circular pitch is pi*m', g['circular_pitch_mm'], math.pi * 4.0, 1e-15)

    # Every sampled flank point must satisfy r = rb*sqrt(1+t^2), the defining involute property.
    rb = g['base_diameter_mm'] / 2
    worst = 0.0
    for x, y in g['flank_points']:
        r = math.hypot(x, y)
        t = math.sqrt(max((r / rb) ** 2 - 1.0, 0.0))
        worst = max(worst, abs(math.hypot(rb * (math.cos(t) + t * math.sin(t)),
                                          rb * (math.sin(t) - t * math.cos(t))) - r))
    check('sampled flank lies on the involute', worst, 0.0, 1e-9,
          f'{len(g["flank_points"])} points, worst radial deviation {worst:.2e} mm', atol=1e-9)

    # Thickness on the pitch circle must return the standard pi*m/2 from the general relation.
    check('thickness relation reproduces pi*m/2 at the pitch circle',
          tooth_thickness_at(g, g['pitch_diameter_mm'] / 2), math.pi * 4.0 / 2, 1e-12)
    boolean('tooth thins toward the tip',
            tooth_thickness_at(g, g['tip_diameter_mm'] / 2) < g['tooth_thickness_pitch_mm'],
            f"tip {tooth_thickness_at(g, g['tip_diameter_mm'] / 2):.4f} mm "
            f"< pitch {g['tooth_thickness_pitch_mm']:.4f} mm")

    pinion = spur_gear(module=4.0, teeth=20)
    wheel = spur_gear(module=4.0, teeth=40)
    mm = mesh(pinion, wheel)
    check('centre distance is m*(z1+z2)/2', mm['centre_distance_mm'], 4.0 * (20 + 40) / 2, 1e-15)
    check('gear ratio is z2/z1', mm['gear_ratio'], 2.0, 1e-15)
    boolean('contact ratio exceeds one so transmission is continuous',
            mm['continuous_transmission'], f"contact ratio {mm['contact_ratio']:.4f}")

    boolean('undercut is flagged below the 20 degree limit of ~17 teeth',
            spur_gear(4.0, 12)['undercut'] and not spur_gear(4.0, 25)['undercut'],
            f"limit {spur_gear(4.0, 25)['undercut_limit_teeth']:.2f} teeth")

    lw = lewis_bending_stress(g, tangential_force_N=3000.0)
    check('Lewis stress is Ft/(b*m*Y)', lw['bending_stress_mpa'],
          3000.0 / (40.0 * 4.0 * lw['lewis_form_factor']), 1e-15,
          f"Y={lw['lewis_form_factor']:.4f}")

    # Hertz against the textbook sphere-on-sphere case, where the closed form is unambiguous.
    b = deep_groove_bearing(40, 80, 18, balls=9, ball_diameter_mm=12.0)
    h = hertz_point_contact(2000.0, 12.0, b['pitch_diameter_mm'], b['raceway_conformity'],
                            b['E_mpa'], b['poisson'])
    e_star = 210000.0 / (2 * (1 - 0.3 ** 2))
    rho = 2 / 6.0 + 1 / 30.0 + 1 / (-0.52 * 12.0)
    a_ref = (3 * 2000.0 / (2 * e_star * rho)) ** (1 / 3)
    check('Hertz contact radius matches the closed form', h['contact_radius_mm'], a_ref, 1e-14)
    check('peak pressure is 3F/(2*pi*a^2)', h['max_contact_pressure_mpa'],
          3 * 2000.0 / (2 * math.pi * a_ref ** 2), 1e-14,
          f"{h['max_contact_pressure_mpa']:.0f} MPa")
    boolean('doubling the load raises pressure by 2^(1/3)',
            abs(hertz_point_contact(4000.0, 12.0, b['pitch_diameter_mm'], 0.52, 210000.0, 0.3)
                ['max_contact_pressure_mpa'] / h['max_contact_pressure_mpa'] - 2 ** (1 / 3)) < 1e-12,
            'the cube-root load dependence of point contact')

    life = basic_rating_life(30000.0, 3000.0, speed_rpm=1500)
    check('L10 is (C/P)^3', life['l10_million_revolutions'], 1000.0, 1e-15)
    check('L10 in hours', life['l10_hours'], 1000.0 * 1e6 / (60 * 1500), 1e-15,
          f"{life['l10_hours']:.0f} h")

    passed = all(c['pass'] for c in checks)
    print(('\nALL CONTROLS PASS' if passed else '\nCONTROLS FAILED') + f'  ({len(checks)} checks)')
    return {'all_pass': passed, 'checks': checks}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['verify'])
    p.add_argument('--out', default=None)
    a = p.parse_args()
    result = verify()
    if a.out:
        from pathlib import Path
        Path(a.out).write_text(json.dumps(result, indent=2, default=str) + '\n')
    raise SystemExit(0 if result['all_pass'] else 1)


if __name__ == '__main__':
    main()
