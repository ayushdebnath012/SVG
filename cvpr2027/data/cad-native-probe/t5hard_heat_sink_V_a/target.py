import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(125.1, 69.5, 7.3)
    .faces(">Z").workplane()
    .rarray(1, 11.976, 1, 6)
    .rect(123.1, 5.6)
    .extrude(11.0)
    .faces(">Z")
    .chamfer(1.2)
    .faces("<Z").workplane()
    .pushPoints([(-51.05, -18.65), (-51.05, 18.65), (51.05, -18.65), (51.05, 18.65)])
    .hole(3.5)
)

# Export
show_object(result)