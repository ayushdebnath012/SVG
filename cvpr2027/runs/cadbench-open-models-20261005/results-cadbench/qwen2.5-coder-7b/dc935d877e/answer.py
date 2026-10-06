import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Define parameters
length = 500.0
width = 300.0
height = 150.0
left_lower_front_corner = FreeCAD.Vector(0.0, 0.0, 0.0)
wall_thickness = 20.0

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the outer body
outer_body = body.newObject("PartDesign::Box", "OuterBody")
outer_body.Length = length
outer_body.Width = width
outer_body.Height = height
outer_body.Placement.Base = left_lower_front_corner

# Create the wall shell cavity
wall_shell_cavity = body.newObject("PartDesign::Pocket", "WallShellCavity")
wall_shell_cavity.Base = outer_body.Shape
wall_shell_cavity.Length = wall_thickness
wall_shell_cavity.Width = wall_thickness
wall_shell_cavity.Height = height
wall_shell_cavity.Placement.Base = FreeCAD.Vector(wall_thickness / 2, wall_thickness / 2, 0)

# Create the bottom shell cavity
bottom_shell_cavity = body.newObject("PartDesign::Pocket", "BottomShellCavity")
bottom_shell_cavity.Base = outer_body.Shape
bottom_shell_cavity.Length = length
bottom_shell_cavity.Width = wall_thickness
bottom_shell_cavity.Height = wall_thickness
bottom_shell_cavity.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
