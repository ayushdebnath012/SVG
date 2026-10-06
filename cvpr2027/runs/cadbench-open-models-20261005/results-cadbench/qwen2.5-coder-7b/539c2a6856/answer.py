import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define key parameters
inner_diameter = 30.0
overall_height = 45.0
flange_diameter = 58.0
flange_thickness = 8.0
hub_width = 46.0

# Create a hexagonal hub
hub = body.newObject("PartDesign::Pad", "Hub")
hub.Profile = doc.addObject("Part::Circle", "HubProfile")
hub.Profile.Radius = hub_width / 2
hub.Length = overall_height
hub.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a circular flange
flange = body.newObject("PartDesign::Pocket", "Flange")
flange.Profile = doc.addObject("Part::Circle", "FlangeProfile")
flange.Profile.Radius = flange_diameter / 2
flange.Length = flange_thickness
flange.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, overall_height - flange_thickness), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a through hole
hole = body.newObject("PartDesign::Pocket", "Hole")
hole.Profile = doc.addObject("Part::Circle", "HoleProfile")
hole.Profile.Radius = inner_diameter / 2
hole.Length = overall_height
hole.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Save the document
doc.saveAs("/app/answer.FCStd")
