import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
inner_diameter = 24.0
overall_height = 36.0
flange_diameter = 45.0
flange_thickness = 6.0
hub_width = 36.0

# Create a cylindrical through hole
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = inner_diameter / 2
cylinder.Height = overall_height
cylinder.Placement.Base = FreeCAD.Vector(0, 0, overall_height / 2)

# Create a hexagonal body
hexagon = body.newObject("PartDesign::Pocket", "Hexagon")
hexagon.Base = cylinder
hexagon.Profile = Part.makePolygon([
    FreeCAD.Vector(-hub_width / 2, 0, 0),
    FreeCAD.Vector(-hub_width / 4, hub_width * 0.433, 0),
    FreeCAD.Vector(hub_width / 4, hub_width * 0.433, 0),
    FreeCAD.Vector(hub_width / 2, 0, 0),
    FreeCAD.Vector(hub_width / 4, -hub_width * 0.433, 0),
    FreeCAD.Vector(-hub_width / 4, -hub_width * 0.433, 0)
])
hexagon.Length = overall_height
hexagon.Reversed = True

# Create a flange
flange = body.newObject("PartDesign::Pocket", "Flange")
flange.Base = hexagon
flange.Profile = Part.makeCircle(flange_diameter / 2)
flange.Length = flange_thickness
flange.Reversed = True

# Save the document
doc.saveAs("/app/answer.FCStd")
