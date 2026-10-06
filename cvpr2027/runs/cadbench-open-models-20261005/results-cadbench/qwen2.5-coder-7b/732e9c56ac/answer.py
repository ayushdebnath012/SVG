import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear stock
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 25.4 / 2  # pitch_diameter / 2
cylinder.Height = 304.8  # overall_length

# Create a PartDesign Feature to define the tooth profile
tooth_profile = body.newObject("PartDesign::Pocket", "ToothProfile")
tooth_profile.Profile = Part.makeCylinder(25.4 / 2, 304.8)
tooth_profile.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 20))

# Create a PartDesign Feature to extrude the tooth profile
extrusion = body.newObject("PartDesign::Pad", "Extrusion")
extrusion.Profile = tooth_profile.Profile
extrusion.Length = 304.8  # overall_length

# Create a PartDesign Feature to subtract the tooth profile from the cylinder
cylinder_cut = body.newObject("PartDesign::Cut", "CylinderCut")
cylinder_cut.Base = cylinder
cylinder_cut.Tool = extrusion

# Save the document
doc.saveAs("/app/answer.FCStd")
