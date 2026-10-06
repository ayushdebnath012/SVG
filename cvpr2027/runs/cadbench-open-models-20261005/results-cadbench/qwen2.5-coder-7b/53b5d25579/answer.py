import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SocketWeldFlange")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
outer_circle_diameter = 130
flange_thickness = 17.5
total_height = 22.0
bore_diameter = 41
neck_diameter = 65
neck_height = 2.5
socket_diameter = 49.5
socket_depth = 16.0
raised_face_diameter = 73
raised_face_thickness = 2
bolt_circle_diameter = 98.5
bolt_hole_diameter = 16
number_bolt_holes = 4

# Create the flange body
flange_body = body.newObject("PartDesign::Pad", "FlangeBody")
flange_body.Profile = Part.makeCircle(outer_circle_diameter / 2)
flange_body.Length = total_height
flange_body.LengthFilletRadius = flange_thickness / 2

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(bore_diameter / 2)
bore.Length = total_height
bore.LengthFilletRadius = flange_thickness / 2

# Create the neck
neck = body.newObject("PartDesign::Pocket", "Neck")
neck.Profile = Part.makeCircle(neck_diameter / 2)
neck.Length = neck_height
neck.LengthFilletRadius = flange_thickness / 2

# Create the socket
socket = body.newObject("PartDesign::Pocket", "Socket")
socket.Profile = Part.makeCircle(socket_diameter / 2)
socket.Length = socket_depth
socket.LengthFilletRadius = flange_thickness / 2

# Create the raised face
raised_face = body.newObject("PartDesign::Pad", "RaisedFace")
raised_face.Profile = Part.makeCircle(raised_face_diameter / 2)
raised_face.Length = raised_face_thickness
raised_face.LengthFilletRadius = flange_thickness / 2

# Create the bolt holes
bolt_circle_radius = bolt_circle_diameter / 2
bolt_hole_radius = bolt_hole_diameter / 2
bolt_hole_distance = bolt_circle_radius - bolt_hole_radius
bolt_hole_angle = 360 / number_bolt_holes
bolt_holes = []
for i in range(number_bolt_holes):
    angle = i * bolt_hole_angle
    x = bolt_circle_radius * FreeCAD.sin(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Angle))
    y = bolt_circle_radius * FreeCAD.cos(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Angle))
    bolt_hole = body.newObject("PartDesign::Pocket", f"BoltHole{i}")
    bolt_hole.Profile = Part.makeCircle(bolt_hole_radius)
    bolt_hole.Length = flange_thickness
    bolt_hole.LengthFilletRadius = flange_thickness / 2
    bolt_hole.Placement.Base = FreeCAD.Vector(x, y, 0)
    bolt_holes.append(bolt_hole)

# Save the document
doc.saveAs("/app/answer.FCStd")
