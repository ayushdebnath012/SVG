import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Dumbbell")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the handle (cylindrical rod)
handle_length = 110.0
handle_diameter = 28.0
handle_radius = handle_diameter / 2

handle = body.newObject("PartDesign::Cylinder", "Handle")
handle.Radius = handle_radius
handle.Height = handle_length
handle.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the hexagonal prism end weights
cross_flat_width = 80.0
hex_height = 30.0
hex_radius = cross_flat_width / (2 * 2**0.5)

# Create the hexagonal prism
hex_prism = body.newObject("PartDesign::Prism", "HexPrism")
hex_prism.Base = Part.makePolygon([
    FreeCAD.Vector(-hex_radius, -hex_radius * 2**0.5, 0),
    FreeCAD.Vector(-hex_radius, hex_radius * 2**0.5, 0),
    FreeCAD.Vector(hex_radius, hex_radius * 2**0.5, 0),
    FreeCAD.Vector(hex_radius, -hex_radius * 2**0.5, 0),
    FreeCAD.Vector(-hex_radius, -hex_radius * 2**0.5, 0)
])
hex_prism.Height = hex_height
hex_prism.Placement.Base = FreeCAD.Vector(-handle_length / 2, 0, 0)

# Mirror the hexagonal prism to create the second end
mirror = body.newObject("PartDesign::Mirrored", "Mirror")
mirror.Base = hex_prism
mirror.MirrorPlane = "XZ"

# Combine the handle and the two hexagonal prisms
body.newObject("PartDesign::Fusion", "Fusion")
body.Fusion.Base = [handle, hex_prism, mirror]

# Save the document
doc.saveAs("/app/answer.FCStd")
