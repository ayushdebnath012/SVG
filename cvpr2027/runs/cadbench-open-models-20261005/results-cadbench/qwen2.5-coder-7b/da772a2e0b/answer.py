import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define key parameters
plate_thickness = 3.0
hole_center_distance = 29.0
head_outer_diameter = 7.0
hole_diameter = 3.0
shaft_width = 3.0

# Create a flat plate
plate = body.newObject("PartDesign::Pad", "Plate")
plate.Profile = doc.addObject("Part::Circle", "PlateProfile")
plate.Profile.Radius = head_outer_diameter / 2
plate.Length = plate_thickness
plate.Base = FreeCAD.Vector(0, 0, 0)

# Create the first head
head1 = body.newObject("PartDesign::Pocket", "Head1")
head1.Profile = doc.addObject("Part::Circle", "Head1Profile")
head1.Profile.Radius = head_outer_diameter / 2
head1.Length = plate_thickness
head1.Base = FreeCAD.Vector(-hole_center_distance / 2, 0, 0)

# Create the second head
head2 = body.newObject("PartDesign::Pocket", "Head2")
head2.Profile = doc.addObject("Part::Circle", "Head2Profile")
head2.Profile.Radius = head_outer_diameter / 2
head2.Length = plate_thickness
head2.Base = FreeCAD.Vector(hole_center_distance / 2, 0, 0)

# Create the shaft
shaft = body.newObject("PartDesign::Revolution", "Shaft")
shaft.Base = doc.addObject("Part::Line", "ShaftBase")
shaft.Base.Placement.Base = FreeCAD.Vector(-hole_center_distance / 2, 0, plate_thickness)
shaft.Base.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)
shaft.Profile = doc.addObject("Part::Circle", "ShaftProfile")
shaft.Profile.Radius = shaft_width / 2
shaft.Length = hole_center_distance

# Create through-holes in the heads
hole1 = body.newObject("PartDesign::Pocket", "Hole1")
hole1.Profile = doc.addObject("Part::Circle", "Hole1Profile")
hole1.Profile.Radius = hole_diameter / 2
hole1.Length = plate_thickness
hole1.Base = FreeCAD.Vector(-hole_center_distance / 2, 0, 0)

hole2 = body.newObject("PartDesign::Pocket", "Hole2")
hole2.Profile = doc.addObject("Part::Circle", "Hole2Profile")
hole2.Profile.Radius = hole_diameter / 2
hole2.Length = plate_thickness
hole2.Base = FreeCAD.Vector(hole_center_distance / 2, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
