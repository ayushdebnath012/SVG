import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the elbow pipe
elbow_pipe = body.newObject("PartDesign::Cylinder", "ElbowPipe")
elbow_pipe.Radius = 50  # elbow_pipe_diameter / 2
elbow_pipe.Height = 300  # elbow_flange_length
elbow_pipe.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the elbow
elbow = body.newObject("PartDesign::Revolution", "Elbow")
elbow.Base = elbow_pipe
elbow.Axis = FreeCAD.Vector(0, 0, 1)
elbow.Profile = body.newObject("PartDesign::Circle", "ElbowProfile")
elbow.Profile.Radius = 100  # elbow_radius
elbow.Profile.Placement.Base = FreeCAD.Vector(0, 0, 0)
elbow.Profile.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)  # elbow_angle

# Create the flanges
flange_outer_diameter = 200
flange_thickness = 5
flange_length = 300

flange1 = body.newObject("PartDesign::Pad", "Flange1")
flange1.Base = elbow
flange1.Length = flange_length
flange1.BaseOffset = flange_length
flange1.Profile = body.newObject("PartDesign::Circle", "FlangeProfile1")
flange1.Profile.Radius = flange_outer_diameter / 2
flange1.Profile.Placement.Base = FreeCAD.Vector(0, 0, 0)

flange2 = body.newObject("PartDesign::Pad", "Flange2")
flange2.Base = elbow
flange2.Length = flange_length
flange2.BaseOffset = -flange_length
flange2.Profile = body.newObject("PartDesign::Circle", "FlangeProfile2")
flange2.Profile.Radius = flange_outer_diameter / 2
flange2.Profile.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the bolt holes
bolt_circle_radius = 72.5
bolt_hole_diameter = 16.0
number_bolt_holes = 8

bolt_holes = []
for i in range(number_bolt_holes):
    angle = 360 * i / number_bolt_holes
    x = bolt_circle_radius * FreeCAD.sin(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Degree))
    y = bolt_circle_radius * FreeCAD.cos(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Degree))
    hole = body.newObject("PartDesign::Pocket", f"BoltHole{i}")
    hole.Base = flange1
    hole.Length = bolt_hole_diameter / 2
    hole.BaseOffset = flange_length
    hole.Profile = body.newObject("PartDesign::Circle", f"BoltHoleProfile{i}")
    hole.Profile.Radius = bolt_hole_diameter / 2
    hole.Profile.Placement.Base = FreeCAD.Vector(x, y, 0)
    bolt_holes.append(hole)

    hole = body.newObject("PartDesign::Pocket", f"BoltHole{i}_2")
    hole.Base = flange2
    hole.Length = bolt_hole_diameter / 2
    hole.BaseOffset = -flange_length
    hole.Profile = body.newObject("PartDesign::Circle", f"BoltHoleProfile{i}_2")
    hole.Profile.Radius = bolt_hole_diameter / 2
    hole.Profile.Placement.Base = FreeCAD.Vector(x, y, 0)
    bolt_holes.append(hole)

# Save the document
doc.saveAs("/app/answer.FCStd")
