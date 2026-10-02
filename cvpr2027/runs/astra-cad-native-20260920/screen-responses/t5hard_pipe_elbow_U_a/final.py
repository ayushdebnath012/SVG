import cadquery as cq

result = (
    cq.Workplane("XY")
    .rect(21.3, 21.3)
    .sweep(
        cq.Workplane("XZ").moveTo(0.0, 0.0).lineTo(0.0, 25.0).radiusArc((19.1, 44.1), 19.1).lineTo(44.1, 44.1),
        isFrenet=True
    )
    .cut(
        cq.Workplane("XY")
        .rect(15.76, 15.76)
        .sweep(
            cq.Workplane("XZ").moveTo(0.0, 0.0).lineTo(0.0, 25.0).radiusArc((19.1, 44.1), 19.1).lineTo(44.1, 44.1),
            isFrenet=True
        )
    )
    .union(cq.Workplane("XY").transformed(offset=cq.Vector(0, 0, -2.117), rotate=cq.Vector(0, 0, 0)).cylinder(6.365, 13.3))
    .union(cq.Workplane("XY").transformed(offset=cq.Vector(0, 0, -6.917), rotate=cq.Vector(0, 0, 0)).cylinder(4.3, 21.3))
    .union(cq.Workplane("XY").transformed(offset=cq.Vector(46.75, 0, 44.1), rotate=cq.Vector(0, 90, 0)).cylinder(6.365, 13.3))
    .union(cq.Workplane("XY").transformed(offset=cq.Vector(51.55, 0, 44.1), rotate=cq.Vector(0, 90, 0)).cylinder(4.3, 21.3))
    .cut(cq.Workplane("XY").transformed(offset=cq.Vector(0, 0, -10.6), rotate=cq.Vector(0, 0, 0)).cylinder(36.6, 7.88))
    .cut(cq.Workplane("XY").transformed(offset=cq.Vector(43.1, 0, 44.1), rotate=cq.Vector(0, 90, 0)).cylinder(36.6, 7.88))
)

# Original inlet flange bolt holes.
for x, y in [(17.3, 0.0), (8.65, 14.982), (-8.65, 14.982), (-17.3, 0.0), (-8.65, -14.982), (8.65, -14.982)]:
    result = result.cut(
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(x, y, -10.1), rotate=cq.Vector(0, 0, 0))
        .cylinder(5.3, 1.3)
    )

# Original outlet flange bolt holes.
for y, z in [(17.3, 44.1), (8.65, 59.082), (-8.65, 59.082), (-17.3, 44.1), (-8.65, 29.118), (8.65, 29.118)]:
    result = result.cut(
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(53.2, y, z), rotate=cq.Vector(0, 90, 0))
        .cylinder(5.3, 1.3)
    )