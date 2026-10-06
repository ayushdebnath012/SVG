import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the nut_body
nut_body = body.newObject("PartDesign::Pad", "NutBody")
nut_body.Length = 10  # nut_thickness
nut_body.Profile = doc.addObject("Part::Circle", "Circle")
nut_body.Profile.Radius = 8 / 2  # hole_diameter / 2

# Create the through_hole
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Length = 30  # hole_cut_depth
through_hole.Profile = doc.addObject("Part::Circle", "CircleHole")
through_hole.Profile.Radius = 8 / 2  # hole_diameter / 2

# Position the through_hole
through_hole.Placement.Base = FreeCAD.Vector(0, 0, 10)  # Centered on the nut_body

# Save the document
doc.saveAs("/app/answer.FCStd")
