#!/usr/bin/env python3
"""Correct FreeCAD 1.1 FEM CLOAD unit bug (1000x under-applied force).

Root cause: femmesh/meshtools.py builds the nodal load table with
    force_quantity = FreeCAD.Units.Quantity(frc_obj.Force.getValueAs("N"))
Quantity(float) is dimensionless in FreeCAD, so the per-node loads end up
1000x too small (0.2 N applied for a 200 N setting — verified by summing the
*CLOAD components). Direction distribution is correct; only magnitude is off.

Usage: fix_cload_units.py DiskPLA.inp DiskPLA_fixed.inp
Checks: prints applied-force totals before/after (after must equal setting).
Linear statics: scaling all CLOADs by k scales stresses/displacements by k.
"""
import math
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
out, in_cload, n = [], False, 0
before, after = [0, 0, 0, 0], [0, 0, 0, 0]
for line in open(src):
    s = line.strip()
    if s.startswith("*CLOAD"):
        in_cload = True
        out.append(line)
        continue
    if s.startswith("*") and not s.startswith("**") and in_cload:
        in_cload = False
        out.append(line)
        continue
    m = re.match(r"^(\d+),([123]),(.+)$", s)
    if in_cload and m:
        v = float(m.group(3))
        before[int(m.group(2))] += v
        after[int(m.group(2))] += v * 1000.0
        n += 1
        out.append(f"{m.group(1)},{m.group(2)},{v * 1000.0:.13G}\n")
    else:
        out.append(line)
open(dst, "w").writelines(out)
b = math.hypot(*before[1:])
a = math.hypot(*after[1:])
print(f"scaled {n} CLOAD lines: |F| before={b:.4f} N -> after={a:.3f} N")
