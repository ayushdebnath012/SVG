import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SlipOnFlange")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
outer_circle_diameter = 108
flange_thickness = 12.2
total_height = 17.5
bore_diameter = 34.5
hub_diameter = 50.8
raised_face_diameter = 49.3
raised_face_thickness = 2.0
bolt_circle_diameter = 79.2
bolt_hole_diameter = 15.7
number_bolt_holes = 4

# Create the flange body
flange_body = body.newObject("PartDesign::Pad", "FlangeBody")
flange_body.Profile = Part.makeCircle(outer_circle_diameter / 2)
flange_body.Length = flange_thickness
flange_body.LengthFilletRadius = 0.0

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(bore_diameter / 2)
bore.Length = flange_thickness
bore.LengthFilletRadius = 0.0

# Create the hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = Part.makeCircle(hub_diameter / 2)
hub.Length = flange_thickness
hub.LengthFilletRadius = 0.0

# Create the raised face
raised_face = body.newObject("PartDesign::Pad", "RaisedFace")
raised_face.Profile = Part.makeCircle(raised_face_diameter / 2)
raised_face.Length = raised_face_thickness
raised_face.LengthFilletRadius = 0.0

# Create the bolt holes
bolt_circle_radius = bolt_circle_diameter / 2
bolt_hole_radius = bolt_hole_diameter / 2
bolt_hole_distance = bolt_circle_radius / (number_bolt_holes / 2)
bolt_hole_positions = [bolt_hole_distance * i for i in range(number_bolt_holes)]

for pos in bolt_hole_positions:
    bolt_hole = body.newObject("PartDesign::Pocket", f"BoltHole_{pos}")
    bolt_hole.Profile = Part.makeCircle(bolt_hole_radius)
    bolt_hole.Length = flange_thickness
    bolt_hole.LengthFilletRadius = 0.0
    bolt_hole.Placement.Base = FreeCAD.Vector(pos, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
