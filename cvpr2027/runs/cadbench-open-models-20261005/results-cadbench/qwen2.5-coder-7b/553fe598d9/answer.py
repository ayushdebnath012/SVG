import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a step_profile sketch
sketch = doc.addObject("Sketcher::SketchObject", "StepProfile")
sketch.Placement.Base = FreeCAD.Vector(0, 0, 0)
sketch.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

# Add risers and treads to the sketch
for i in range(3):
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i * 300, 0, 0), FreeCAD.Vector(i * 300, 150, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(i * 300, 150, 0), FreeCAD.Vector((i + 1) * 300, 150, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector((i + 1) * 300, 150, 0), FreeCAD.Vector((i + 1) * 300, 0, 0)), False)

# Add the sketch to the body
body.addObject(sketch)

# Create an extrusion feature
extrusion = doc.addObject("PartDesign::Pad", "Extrusion")
extrusion.Profile = sketch
extrusion.Length = 1200
extrusion.BaseOffset = 0
extrusion.Midplane = False
extrusion.MidplaneOffset = 0
extrusion.Reversed = False
extrusion.Symmetric = False
extrusion.UseCustomLength = True
extrusion.LengthCustom = 1200
extrusion.BaseFeature = body

# Add the extrusion to the body
body.addObject(extrusion)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))

# Close the document
FreeCAD.closeDocument(doc.Name)
