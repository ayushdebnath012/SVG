import cadquery as cq

result = (
    cq.Workplane("XY")
    .union(cq.Workplane("XY").cylinder(28.0, 14.0))
    .union(cq.Workplane("XY").transformed(offset=cq.Vector(0.0, 0.0, 18.0)).cylinder(18.0, 62.5))
    .cut(cq.Workplane("XY").cylinder(32.0, 5.5))
    .cut(cq.Workplane("XY").transformed(offset=cq.Vector(0.0, 0.0, 18.0)).cylinder(22.0, 47.5))
)

for angle in [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]:
    spoke = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(0.0, 0.0, 0.0), rotate=cq.Vector(0.0, 0.0, angle))
        .transformed(offset=cq.Vector(0.0, 0.0, 0.0), rotate=cq.Vector(90.0, 0.0, 0.0))
        .polyline([[12.0, -12.0], [12.0, 12.0], [49.5, 25.0], [49.5, 11.0]])
        .close()
        .extrude(3.5, both=True)
    )
    result = result.union(spoke)

result = (
    result.edges(">Z").chamfer(1.8)
    .union(cq.Workplane("XY").transformed(offset=cq.Vector(55.0, 0.0, 31.0)).cylinder(8.0, 6.0))
    .union(cq.Workplane("XY").transformed(offset=cq.Vector(55.0, 0.0, 63.5)).cylinder(57.0, 9.6))
    .edges(">Z").chamfer(3.2)
)
