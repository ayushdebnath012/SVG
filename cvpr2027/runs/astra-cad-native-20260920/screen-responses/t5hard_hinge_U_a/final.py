import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(20.0, 30.0, 1.5)
    .faces(">Z").workplane()
    .pushPoints([[-5.0, -7.5], [-5.0, 0.0], [-5.0, 7.5]])
    .cskHole(2.5, 5.0, 82.0)
)

for y in [-9.643, -0.001, 9.641]:
    result = result.union(
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(12.5, y, 0.0), rotate=cq.Vector(-90.0, 0.0, 0.0))
        .box(5.0, 5.0, 8.57)
    )

for y in [-9.643, -0.001, 9.641]:
    result = result.cut(
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(12.5, y, 0.0), rotate=cq.Vector(-90.0, 0.0, 0.0))
        .cylinder(10.57, 1.25)
    )