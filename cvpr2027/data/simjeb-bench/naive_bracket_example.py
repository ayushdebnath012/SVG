# A deliberately simple GE bracket: a flat bolt plate and two upright clevis lugs (hand-written harness test / naive baseline).
import math
import cadquery as cq

BOLTS = [(0.0, 0.0), (52.0472, 1.5805), (0.0, -148.1248), (38.0833, -146.9684)]
BOLT_D, PLATE_T = 10.3124, 7.85
PIN = (-20.9236, -74.6978, 44.7246)
AX = (-0.030352, 0.999539)                      # pin axis in the xy-plane
ANG = math.degrees(math.atan2(-AX[0], AX[1]))   # rotation of the lugs about z
PIN_D, LUG_T, LUG_IN = 19.1008, 6.35, 11.112    # bore, lug thickness, half gap

plate = (cq.Workplane("XY").polyline([(-38, 12), (62, 12), (62, -158), (-38, -158)]).close().extrude(PLATE_T))
for x, y in BOLTS:
    plate = plate.cut(cq.Workplane("XY").center(x, y).circle(BOLT_D / 2).extrude(PLATE_T))

lugs = None
for side in (+1, -1):
    y0 = LUG_IN if side > 0 else -LUG_IN - LUG_T   # local axial start of the lug
    lug = (cq.Workplane("XZ", origin=(0, 0, 0)).center(PIN[0], 0)
           .polyline([(-18, 0), (18, 0), (18, PIN[2]), (0, PIN[2] + 18), (-18, PIN[2])]).close().extrude(-LUG_T)
           .translate((0, y0, 0)))
    lug = lug.cut(cq.Workplane("XZ").center(PIN[0], PIN[2]).circle(PIN_D / 2).extrude(-LUG_T).translate((0, y0, 0)))
    lug = lug.rotate((PIN[0], 0, 0), (PIN[0], 0, 1), ANG).translate((0, PIN[1] - 0.0, 0))
    lugs = lug if lugs is None else lugs.union(lug)

result = plate.union(lugs)
