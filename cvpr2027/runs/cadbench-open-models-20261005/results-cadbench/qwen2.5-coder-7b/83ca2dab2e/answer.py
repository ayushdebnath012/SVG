import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("BallJoint")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical shaft
shaft_diameter = 4.0
shaft_length = 5.9
shaft = body.newObject("PartDesign::Cylinder", "Shaft")
shaft.Radius = shaft_diameter / 2
shaft.Height = shaft_length
shaft.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a spherical ball
ball_diameter = 5.0
ball = body.newObject("PartDesign::Sphere", "Ball")
ball.Radius = ball_diameter / 2
ball.Placement.Base = FreeCAD.Vector(0, 0, shaft_length / 2)

# Create an axial hole
hole_diameter = 2.0
hole_depth = 10.0
hole = body.newObject("PartDesign::Hole", "Hole")
hole.Diameter = hole_diameter
hole.Length = hole_depth
hole.Placement.Base = FreeCAD.Vector(0, 0, 0)
hole.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)

# Finalize the body
body.addFeature(shaft)
body.addFeature(ball)
body.addFeature(hole)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
