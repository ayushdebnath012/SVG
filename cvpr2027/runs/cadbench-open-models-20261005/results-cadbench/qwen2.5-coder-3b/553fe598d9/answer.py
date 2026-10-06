import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("StepModel")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Define the step profile parameters
number_of_tiers = 3
riser = 150.0
depth = 300.0
total_rise = number_of_tiers * riser
total_run = number_of_tiers * depth
profile_origin = (0.0, 0.0)

# Create a PartDesign Sketch
sketch = PartDesign.Sketch(doc, "StepProfileSketch")
sketch.addGeometry(Part.LineSegment((0.0, 0.0), (total_run, 0.0)))
sketch.addGeometry(Part.LineSegment((total_run, 0.0), (total_run, total_rise)))
sketch.addGeometry(Part.LineSegment((total_run, total_rise), (0.0, total_rise)))
sketch.addGeometry(Part.LineSegment((0.0, total_rise), (0.0, 0.0)))
sketch.addConstraint(PartDesign.ConstraintCoincident(sketch.Vertexes[0], sketch.Vertexes[3]))
sketch.addConstraint(PartDesign.ConstraintCoincident(sketch.Vertexes[1], sketch.Vertexes[2]))
sketch.addConstraint(PartDesign.ConstraintCoincident(sketch.Vertexes[2], sketch.Vertexes[4]))
sketch.addConstraint(PartDesign.ConstraintCoincident(sketch.Vertexes[3], sketch.Vertexes[5]))
sketch.addConstraint(PartDesign.ConstraintDistanceX(sketch.Vertexes[0], sketch.Vertexes[1], total_run))
sketch.addConstraint(PartDesign.ConstraintDistanceY(sketch.Vertexes[1], sketch.Vertexes[2], total_rise))
sketch.addConstraint(PartDesign.ConstraintDistanceX(sketch.Vertexes[2], sketch.Vertexes[3], total_run))
sketch.addConstraint(PartDesign.ConstraintDistanceY(sketch.Vertexes[3], sketch.Vertexes[4], total_rise))
sketch.addConstraint(PartDesign.ConstraintDistanceX(sketch.Vertexes[4], sketch.Vertexes[5], total_run))
sketch.addConstraint(PartDesign.ConstraintDistanceY(sketch.Vertexes[5], sketch.Vertexes[0], total_rise))

# Create a PartDesign Extrusion
extrusion = PartDesign.Extrusion(doc, "StepExtrusion")
extrusion.Base = sketch
extrusion.Dir = (0.0, 0.0, 1.0)
extrusion.Length = 1200.0

# Add the extrusion to the body
body.addObject(extrusion)

# Save the document
doc.saveAs("/app/answer.FCStd")
