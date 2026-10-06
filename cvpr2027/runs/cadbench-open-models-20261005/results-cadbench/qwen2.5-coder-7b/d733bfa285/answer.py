import FreeCAD
import Part
import PartDesign

# Set up the document
doc = FreeCAD.newDocument("answer")

# Define parameters
number_teeth = 23
spline_module = 3.0  # in mm
spline_pitch_diameter = number_teeth * spline_module  # in mm
spline_height = 10.0  # in mm
pressure_angle = 30.0  # in degrees
fillet_radius = 1.2  # in mm

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a spline sketch
sketch = doc.addObject("Sketcher::SketchObject", "SplineSketch")
body.addObject(sketch)
sketch.Placement.Base = FreeCAD.Vector(0, 0, 0)
sketch.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

# Add circular arcs for the spline profile
for i in range(number_teeth):
    angle = 2 * i * 3.14159 / number_teeth
    x = spline_pitch_diameter / 2 * (1 - 2 * (i % 2))
    y = spline_height / 2 * (1 - 2 * (i // 2))
    sketch.addGeometry(Part.Circle(FreeCAD.Vector(x, y, 0), FreeCAD.Vector(0, 0, 1), spline_module / 2), False)
    if i > 0:
        sketch.addConstraint(Sketcher.Constraint('Coincident', 0, 2, 1, 1))
    sketch.addConstraint(Sketcher.Constraint('Coincident', 1, 2, 2, 1))
    sketch.addConstraint(Sketcher.Constraint('Equal', 0, 1))
    sketch.addConstraint(Sketcher.Constraint('Symmetric', 0, 1, 0, 2, 0, 0))
    sketch.addConstraint(Sketcher.Constraint('Symmetric', 1, 2, 1, 0, 0, 0))

# Create a PartDesign Extrusion
extrusion = doc.addObject("PartDesign::Pad", "Extrusion")
body.addObject(extrusion)
extrusion.Profile = sketch
extrusion.Length = spline_pitch_diameter / 2
extrusion.LengthFwd = spline_pitch_diameter / 2
extrusion.LengthRev = 0

# Apply fillets at the root of each tooth
for i in range(number_teeth):
    fillet = doc.addObject("PartDesign::Fillet", "Fillet")
    body.addObject(fillet)
    fillet.Base = extrusion
    fillet.Radius = fillet_radius
    fillet.Edges = [extrusion.Shape.Edges[i * 2]]

# Save the document
doc.saveAs("/app/answer.FCStd")
FreeCAD.closeDocument(doc.Name)
