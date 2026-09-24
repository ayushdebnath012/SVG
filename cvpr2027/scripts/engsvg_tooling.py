"""Cutting and grinding tools, with closed-form verification.

Gears and bearings are elements a drawing shows. Tools are what makes them, and they verify the same
way: their geometry and first-order mechanics are exact relations, not fitted curves. A turning
insert's theoretical roughness is f^2/(32*r), Taylor's line is V*T^n = C, and Merchant's shear angle
follows from the friction and rake angles. A drawing that claims any of these can be checked against
what it drew.

Implemented:

    turning insert   nose radius, rake and clearance, theoretical roughness, cutting power
    twist drill      point and helix geometry, thrust and torque, penetration rate
    end mill         flute geometry, chip load, material removal rate
    orthogonal cut   Merchant shear angle, chip ratio, shear plane area and force
    Taylor life      V*T^n = C, and the speed that buys a wanted life
    grinding wheel   surface speed, equivalent chip thickness, specific energy, G-ratio

Limits worth stating: Merchant assumes a thin shear plane, continuous chip and no built-up edge;
Taylor constants are material and tool specific and are inputs here, not predictions; theoretical
roughness ignores built-up edge, vibration and tool wear, so a real Ra is always worse. These check a
drawing against the mechanics it claims, not against a machining trial.

Subcommand: verify
"""
from __future__ import annotations
import argparse
import json
import math


# ----------------------------------------------------------------------------- turning
def turning_insert(nose_radius_mm, rake_deg, clearance_deg, included_angle_deg=80.0,
                   thickness_mm=4.76, inscribed_circle_mm=12.7):
    if nose_radius_mm <= 0 or not 0 < clearance_deg < 45:
        raise ValueError('implausible insert')
    return {'kind': 'turning_insert', 'nose_radius_mm': nose_radius_mm, 'rake_deg': rake_deg,
            'clearance_deg': clearance_deg, 'included_angle_deg': included_angle_deg,
            'thickness_mm': thickness_mm, 'inscribed_circle_mm': inscribed_circle_mm,
            'wedge_angle_deg': 90.0 - rake_deg - clearance_deg}


def theoretical_roughness(feed_mm_rev, nose_radius_mm):
    """Ra ~ f^2/(32r), Rz ~ f^2/(8r): the geometric trace the nose leaves, nothing more."""
    return {'ra_um': 1000.0 * feed_mm_rev ** 2 / (32.0 * nose_radius_mm),
            'rz_um': 1000.0 * feed_mm_rev ** 2 / (8.0 * nose_radius_mm),
            'excludes': ['built-up edge', 'vibration', 'tool wear', 'workpiece material effects']}


def turning_power(cutting_speed_m_min, feed_mm_rev, depth_mm, specific_force_mpa):
    """Fc = kc * A. Power is Fc*v with consistent units; kc is an input, not a prediction."""
    area = feed_mm_rev * depth_mm
    force = specific_force_mpa * area
    return {'chip_area_mm2': area, 'cutting_force_N': force,
            'cutting_power_kW': force * cutting_speed_m_min / 60.0 / 1000.0,
            'mrr_mm3_min': cutting_speed_m_min * 1000.0 * area}


# ----------------------------------------------------------------------------- drilling
def twist_drill(diameter_mm, point_angle_deg=118.0, helix_angle_deg=30.0, web_mm=None, flutes=2):
    if diameter_mm <= 0 or not 60 < point_angle_deg < 180:
        raise ValueError('implausible drill')
    web = web_mm if web_mm is not None else 0.15 * diameter_mm
    half = math.radians(point_angle_deg / 2)
    return {'kind': 'twist_drill', 'diameter_mm': diameter_mm, 'point_angle_deg': point_angle_deg,
            'helix_angle_deg': helix_angle_deg, 'web_thickness_mm': web, 'flutes': flutes,
            'point_height_mm': (diameter_mm / 2) / math.tan(half),
            'lip_length_mm': (diameter_mm / 2) / math.sin(half),
            'chisel_edge_mm': web / math.sin(half)}


def drilling(drill, feed_mm_rev, speed_rpm, specific_force_mpa):
    """Thrust and torque from the uncut area per lip; the classic first-order estimate."""
    d = drill['diameter_mm']
    per_lip = feed_mm_rev / drill['flutes']
    thrust = specific_force_mpa * d * per_lip * 0.5
    torque = specific_force_mpa * d ** 2 * per_lip / 8.0
    return {'thrust_N': thrust, 'torque_Nmm': torque,
            'power_kW': 2 * math.pi * speed_rpm * torque / 60.0 / 1e6,
            'penetration_mm_min': feed_mm_rev * speed_rpm,
            'surface_speed_m_min': math.pi * d * speed_rpm / 1000.0}


# ----------------------------------------------------------------------------- milling
def end_mill(diameter_mm, flutes, helix_angle_deg=30.0, corner_radius_mm=0.0, length_mm=50.0):
    if flutes < 1 or diameter_mm <= 0:
        raise ValueError('implausible cutter')
    return {'kind': 'end_mill', 'diameter_mm': diameter_mm, 'flutes': flutes,
            'helix_angle_deg': helix_angle_deg, 'corner_radius_mm': corner_radius_mm,
            'length_mm': length_mm}


def milling(cutter, speed_rpm, feed_mm_min, axial_mm, radial_mm):
    chip = feed_mm_min / (speed_rpm * cutter['flutes'])
    return {'feed_per_tooth_mm': chip, 'surface_speed_m_min':
            math.pi * cutter['diameter_mm'] * speed_rpm / 1000.0,
            'mrr_mm3_min': axial_mm * radial_mm * feed_mm_min,
            'radial_engagement_fraction': radial_mm / cutter['diameter_mm']}


# ----------------------------------------------------------------------------- cutting mechanics
def merchant(rake_deg, friction_angle_deg, chip_thickness_ratio=None, uncut_mm=None, width_mm=None,
             shear_strength_mpa=None):
    """Merchant: 2*phi + beta - alpha = 90. A thin shear plane and a continuous chip are assumed."""
    alpha = math.radians(rake_deg)
    beta = math.radians(friction_angle_deg)
    phi = math.pi / 4 - (beta - alpha) / 2
    out = {'shear_angle_deg': math.degrees(phi), 'friction_angle_deg': friction_angle_deg,
           'rake_deg': rake_deg,
           'chip_thickness_ratio': math.sin(phi) / math.cos(phi - alpha),
           'assumes': ['thin shear plane', 'continuous chip', 'no built-up edge']}
    if chip_thickness_ratio is not None:
        r = chip_thickness_ratio
        out['shear_angle_from_ratio_deg'] = math.degrees(
            math.atan(r * math.cos(alpha) / (1 - r * math.sin(alpha))))
    if None not in (uncut_mm, width_mm, shear_strength_mpa):
        area = uncut_mm * width_mm / math.sin(phi)
        out['shear_plane_area_mm2'] = area
        out['shear_force_N'] = shear_strength_mpa * area
        out['cutting_force_N'] = (shear_strength_mpa * area
                                  * math.cos(beta - alpha) / math.cos(phi + beta - alpha))
    return out


def taylor_life(speed_m_min=None, life_min=None, n=0.25, C=250.0):
    """V*T^n = C. One of speed or life is given; the other follows. n and C are inputs."""
    if (speed_m_min is None) == (life_min is None):
        raise ValueError('give exactly one of speed or life')
    if life_min is None:
        return {'life_min': (C / speed_m_min) ** (1 / n), 'n': n, 'C': C,
                'speed_m_min': speed_m_min}
    return {'speed_m_min': C / life_min ** n, 'n': n, 'C': C, 'life_min': life_min}


# ----------------------------------------------------------------------------- grinding
def grinding_wheel(diameter_mm, width_mm, bore_mm, grit=60, grade='K', structure=6,
                   bond='vitrified'):
    if diameter_mm <= bore_mm:
        raise ValueError('bore cannot exceed the wheel')
    return {'kind': 'grinding_wheel', 'diameter_mm': diameter_mm, 'width_mm': width_mm,
            'bore_mm': bore_mm, 'grit': grit, 'grade': grade, 'structure': structure, 'bond': bond}


def grinding(wheel, wheel_rpm, work_speed_m_min, depth_mm, width_mm=None,
             specific_energy_J_mm3=None):
    """Surface grinding. h_eq = v_w*a_e/v_s is the standard severity measure."""
    vs = math.pi * wheel['diameter_mm'] * wheel_rpm / 1000.0 / 60.0      # m/s
    vw = work_speed_m_min / 60.0                                          # m/s
    b = width_mm if width_mm is not None else wheel['width_mm']
    h_eq = vw * depth_mm / vs
    mrr = work_speed_m_min * 1000.0 / 60.0 * depth_mm * b                 # mm^3/s
    out = {'wheel_surface_speed_m_s': vs, 'work_speed_m_s': vw,
           'equivalent_chip_thickness_mm': h_eq, 'speed_ratio': vs / vw,
           'mrr_mm3_s': mrr, 'specific_mrr_mm3_mm_s': mrr / b,
           'contact_length_mm': math.sqrt(depth_mm * wheel['diameter_mm'] / 2)}
    if specific_energy_J_mm3:
        out['grinding_power_W'] = specific_energy_J_mm3 * mrr
    return out


def grinding_ratio(volume_removed_mm3, wheel_wear_mm3):
    if wheel_wear_mm3 <= 0:
        raise ValueError('wear must be positive')
    return {'g_ratio': volume_removed_mm3 / wheel_wear_mm3}


# ----------------------------------------------------------------------------- controls
def verify():
    checks = []

    def check(name, got, want, tol=1e-12, detail='', atol=None):
        if want == 0.0 or atol is not None:
            err = abs(got - want); ok = err <= (atol if atol is not None else 1e-9)
        else:
            err = abs(got - want) / abs(want); ok = err <= tol
        checks.append({'check': name, 'pass': bool(ok), 'got': got, 'expected': want,
                       'error': err, 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {got:.8g} vs {want:.8g}  err {err:.1e}  {detail}")

    def boolean(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")

    ins = turning_insert(0.8, rake_deg=6.0, clearance_deg=7.0)
    check('insert wedge angle is 90 - rake - clearance', ins['wedge_angle_deg'], 77.0)
    r = theoretical_roughness(0.2, 0.8)
    check('theoretical Ra is f^2/(32r)', r['ra_um'], 1000 * 0.04 / 25.6)
    check('Rz is four times Ra', r['rz_um'] / r['ra_um'], 4.0)
    boolean('doubling the nose radius halves Ra',
            abs(theoretical_roughness(0.2, 1.6)['ra_um'] / r['ra_um'] - 0.5) < 1e-12,
            f"{r['ra_um']:.3f} um at r=0.8 mm, f=0.2 mm/rev")

    tp = turning_power(200.0, 0.25, 2.0, 2000.0)
    check('cutting force is kc times chip area', tp['cutting_force_N'], 2000.0 * 0.5)
    check('material removal rate is v*f*ap', tp['mrr_mm3_min'], 200.0 * 1000 * 0.5)

    d = twist_drill(10.0, point_angle_deg=118.0)
    check('drill point height is (D/2)/tan(half angle)', d['point_height_mm'],
          5.0 / math.tan(math.radians(59.0)))
    check('lip length is (D/2)/sin(half angle)', d['lip_length_mm'],
          5.0 / math.sin(math.radians(59.0)))
    dr = drilling(d, 0.2, 1000, 2000.0)
    check('penetration rate is feed times speed', dr['penetration_mm_min'], 200.0)
    check('drill surface speed is pi*D*N/1000', dr['surface_speed_m_min'],
          math.pi * 10.0 * 1000 / 1000.0)

    em = end_mill(12.0, flutes=4)
    ml = milling(em, 3000, 1200.0, axial_mm=5.0, radial_mm=3.0)
    check('feed per tooth is F/(N*z)', ml['feed_per_tooth_mm'], 1200.0 / (3000 * 4))
    check('milling MRR is ap*ae*F', ml['mrr_mm3_min'], 5.0 * 3.0 * 1200.0)
    check('radial engagement fraction', ml['radial_engagement_fraction'], 0.25)

    me = merchant(10.0, 30.0, uncut_mm=0.2, width_mm=3.0, shear_strength_mpa=400.0)
    check('Merchant shear angle is 45 - (beta - alpha)/2', me['shear_angle_deg'], 45.0 - 10.0)
    boolean('the relation 2*phi + beta - alpha = 90 holds',
            abs(2 * me['shear_angle_deg'] + 30.0 - 10.0 - 90.0) < 1e-12,
            f"phi = {me['shear_angle_deg']:.2f} deg")
    check('shear plane area is t*w/sin(phi)', me['shear_plane_area_mm2'],
          0.2 * 3.0 / math.sin(math.radians(35.0)))
    inv = merchant(10.0, 30.0, chip_thickness_ratio=me['chip_thickness_ratio'])
    check('shear angle recovered from the chip ratio', inv['shear_angle_from_ratio_deg'],
          me['shear_angle_deg'], 1e-10, 'round trip through r = sin(phi)/cos(phi-alpha)')

    t = taylor_life(speed_m_min=250.0, n=0.25, C=250.0)
    check('at V = C the tool life is one minute', t['life_min'], 1.0)
    t2 = taylor_life(life_min=16.0, n=0.25, C=250.0)
    check('halving speed from C gives 16 minutes', t2['speed_m_min'], 125.0)
    boolean('the Taylor round trip is consistent',
            abs(taylor_life(speed_m_min=t2['speed_m_min'], n=0.25, C=250.0)['life_min'] - 16.0) < 1e-9,
            'V*T^n = C in both directions')

    w = grinding_wheel(350.0, 40.0, 127.0, grit=60)
    g = grinding(w, wheel_rpm=1900, work_speed_m_min=15.0, depth_mm=0.02,
                 specific_energy_J_mm3=35.0)
    check('wheel surface speed is pi*D*N/60000', g['wheel_surface_speed_m_s'],
          math.pi * 350.0 * 1900 / 1000.0 / 60.0)
    check('equivalent chip thickness is vw*ae/vs', g['equivalent_chip_thickness_mm'],
          (15.0 / 60.0) * 0.02 / g['wheel_surface_speed_m_s'])
    check('contact length is sqrt(ae*D/2)', g['contact_length_mm'], math.sqrt(0.02 * 175.0))
    check('grinding power is specific energy times MRR', g['grinding_power_W'],
          35.0 * g['mrr_mm3_s'])
    boolean('equivalent chip thickness is far below a milling chip load',
            g['equivalent_chip_thickness_mm'] < ml['feed_per_tooth_mm'] / 100,
            f"{g['equivalent_chip_thickness_mm']:.3e} mm grinding vs "
            f"{ml['feed_per_tooth_mm']:.3f} mm per milling tooth")
    check('G-ratio is removed over worn', grinding_ratio(12000.0, 150.0)['g_ratio'], 80.0)

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
