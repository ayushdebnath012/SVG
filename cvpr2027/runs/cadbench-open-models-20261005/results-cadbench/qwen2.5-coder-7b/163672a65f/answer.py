import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the rounded end
rounded_end = body.newObject("PartDesign::Pocket", "RoundedEnd")
rounded_end.Profile = doc.addObject("Part::Circle", "Circle")
rounded_end.Profile.Radius = 0.03  # Radius of the rounded end
rounded_end.Length = 0.08  # Length of the rounded end
rounded_end.Base = FreeCAD.Vector(0, 0, 0)
rounded_end.Direction = FreeCAD.Vector(0, 0, 1)

# Create a PartDesign Feature for the cylindrical section
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 0.03  # Radius of the cylinder
cylinder.Height = 3.92  # Height of the cylinder (overall length - rounded end height)

# Create a PartDesign Feature for the taper section
taper = body.newObject("PartDesign::Revolution", "Taper")
taper.Base = rounded_end
taper.Profile = doc.addObject("Part::Circle", "TaperProfile")
taper.Profile.Radius = 0.03  # Radius of the taper profile
taper.Profile.Placement.Base = FreeCAD.Vector(0, 0, 3.92)
taper.Profile.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 1.5708)  # 90 degrees in radians
taper.Profile.Placement.Rotation.Axis = FreeCAD.Vector(0, 0, 1)
taper.Profile.Placement.Rotation.Angle = 1.5708  # 90 degrees in radians

# Create a PartDesign Feature for the final rounded end
final_rounded_end = body.newObject("PartDesign::Pocket", "FinalRoundedEnd")
final_rounded_end.Profile = doc.addObject("Part::Circle", "FinalCircle")
final_rounded_end.Profile.Radius = 0.03  # Radius of the final rounded end
final_rounded_end.Length = 0.08  # Length of the final rounded end
final_rounded_end.Base = FreeCAD.Vector(0, 0, 4.0)
final_rounded_end.Direction = FreeCAD.Vector(0, 0, 1)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument("answer")
