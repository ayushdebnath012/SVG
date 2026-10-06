import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a 2D profile for the stair
profile = doc.addObject("PartDesign::Pad", "StairProfile")
profile.Profile = Part.makeBox(1, 1, 1)  # Dummy box, will be replaced
profile.Length = 1500  # total_run
profile.LengthFwd = 1500  # total_run
profile.LengthRev = 0
profile.Midplane = False
profile.UseCustomLength = True
profile.LengthCustom = 1500  # total_run

# Create a 2D sketch for the stair profile
sketch = doc.addObject("Sketcher::SketchObject", "StairSketch")
sketch.Placement.Base = FreeCAD.Vector(0, 0, 0)
sketch.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1500, 0, 0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(1500, 0, 0), FreeCAD.Vector(1500, 850, 0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(1500, 850, 0), FreeCAD.Vector(0, 850, 0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0, 850, 0), FreeCAD.Vector(0, 0, 0)))
sketch.addConstraint(Sketcher.Constraint('Coincident', 0, 2, 1, 1))
sketch.addConstraint(Sketcher.Constraint('Coincident', 1, 2, 2, 1))
sketch.addConstraint(Sketcher.Constraint('Coincident', 2, 2, 3, 1))
sketch.addConstraint(Sketcher.Constraint('Coincident', 3, 2, 0, 1))
sketch.addConstraint(Sketcher.Constraint('Horizontal', 0))
sketch.addConstraint(Sketcher.Constraint('Horizontal', 2))
sketch.addConstraint(Sketcher.Constraint('Vertical', 1))
sketch.addConstraint(Sketcher.Constraint('Vertical', 3))
sketch.addConstraint(Sketcher.Constraint('DistanceX', 0, 1, 1500))
sketch.addConstraint(Sketcher.Constraint('DistanceY', 1, 2, 850))
sketch.addConstraint(Sketcher.Constraint('DistanceY', 2, 3, 850))
sketch.addConstraint(Sketcher.Constraint('DistanceY', 3, 0, 850))
profile.Profile = sketch

# Create an extrusion for the stair
extrusion = doc.addObject("PartDesign::Extrude", "StairExtrusion")
extrusion.Base = profile
extrusion.Length = 1200  # step_width
extrusion.LengthFwd = 1200  # step_width
extrusion.LengthRev = 0
extrusion.Midplane = False
extrusion.UseCustomLength = True
extrusion.LengthCustom = 1200  # step_width

# Add the extrusion to the body
body.addObject(extrusion)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
