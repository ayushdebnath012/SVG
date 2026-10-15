import os
import FreeCAD
import Part
import PartDesign

# Output paths derived from __file__
script_dir = os.path.dirname(os.path.abspath(__file__))
doc_path = os.path.join(script_dir, "answer.FCStd")

doc = FreeCAD.newDocument("FlangedWheelHubMotor")
body = doc.addObject("PartDesign::Body", "Body")

# Create base sketch for Revolution (XZ plane: X=radius, Z=axial)
sketch = doc.addObject("Sketcher::SketchObject", "RevolutionSketch")
body.addObject(sketch)

# Map sketch to XZ_Plane
sketch.MapMode = "FlatFace"
# We can construct a simple closed profile on XZ plane representing the main hub cross-section
# X is radius (horizontal), Z is axial (vertical)
# Axis of revolution is Z axis (X=0)

# Points defining the right-half cross-section polygon:
# 1. Z = -11.75, X = 0 (bottom tip on axis)
# 2. Z = -11.75, X = 6.0 (shaft radius)
# 3. Z = 28.25, X = 6.0
# 4. Z = 28.25, X = 10.0 (shaft shoulder)
# 5. Z = 30.75, X = 26.58 (collar base)
# 6. Z = 34.25, X = 27.08 (collar lip)
# 7. Z = 35.25, X = 36.15 (collar outer)
# 8. Z = 46.75, X = 47.85 (taper end)
# 9. Z = 54.75, X = 57.0 (housing neck / flange inner face start)
# 10. Z = 54.75, X = 69.5 (flange outer radius)
# 11. Z = 107.75, X = 69.5 (right flange outer face)
# 12. Z = 115.75, X = 57.0 (right neck)
# 13. Z = 118.75, X = 20.0 (right land start)
# 14. Z = 127.75, X = 17.0 (right bearing shoulder)
# 15. Z = 155.75, X = 17.0
# 16. Z = 155.75, X = 6.0
# 17. Z = 188.25, X = 6.0
# 18. Z = 188.25, X = 0 (top tip on axis)

points = [
    (0, -11.75),
    (6.0, -11.75),
    (6.0, 28.25),
    (10.0, 28.25),
    (26.58, 30.75),
    (27.08, 34.25),
    (36.15, 35.25),
    (47.85, 46.75),
    (57.0, 54.75),
    (69.5, 54.75),
    (69.5, 107.75),
    (57.0, 115.75),
    (20.0, 118.75),
    (17.0, 127.75),
    (17.0, 155.75),
    (6.0, 155.75),
    (6.0, 188.25),
    (0, 188.25),
]

for i in range(len(points)):
    p1 = points[i]
    p2 = points[(i + 1) % len(points)]
    sketch.addGeometry(
        Part.LineSegment(
            FreeCAD.Vector(p1[0], p1[1], 0), FreeCAD.Vector(p2[0], p2[1], 0)
        ),
        False,
    )

doc.recompute()

# Revolution feature around the Z-axis (Line index 0 or vertical axis)
rev = doc.addObject("PartDesign::Revolution", "Revolution")
rev.Profile = sketch
# Reference Z axis as the revolution axis
rev.ReferenceAxis = (sketch, ["Line1"])
rev.Angle = 360.0
body.addObject(rev)

doc.recompute()

# Save document
doc.saveAs(doc_path)
print("Model successfully saved to", doc_path)
