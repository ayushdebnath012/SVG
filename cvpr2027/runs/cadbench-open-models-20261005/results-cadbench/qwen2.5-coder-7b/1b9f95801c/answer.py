import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the cup body
cup_body = body.newObject("PartDesign::Cylinder", "CupBody")
cup_body.Radius = 40.0  # cup_diameter / 2
cup_body.Height = 120.0
cup_body.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the hollowed-out interior
hollow_body = body.newObject("PartDesign::Cylinder", "HollowBody")
hollow_body.Radius = 38.0  # cup_diameter / 2 - cup_thickness
hollow_body.Height = 116.0  # cup_height - 2 * cup_thickness
hollow_body.Placement.Base = FreeCAD.Vector(0, 0, 2.0)  # Adjusted to account for thickness

# Create a PartDesign Feature for the final solid body
solid_body = body.newObject("PartDesign::Pocket", "SolidBody")
solid_body.Base = cup_body.Shape
solid_body.Profile = hollow_body.Shape
solid_body.Length = 116.0  # cup_height - 2 * cup_thickness
solid_body.LengthFuzz = 0.0
solid_body.Reversed = False
solid_body.TaperAngle = 0.0
solid_body.BaseOffset = 0.0
solid_body.LengthOffset = 0.0
solid_body.BaseTaperAngle = 0.0
solid_body.LengthTaperAngle = 0.0

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument("answer")
