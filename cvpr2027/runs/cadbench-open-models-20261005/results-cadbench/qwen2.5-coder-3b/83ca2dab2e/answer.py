import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("BallJoint")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Create a new PartDesign Cylinder for the shaft
shaft = PartDesign.Cylinder()
shaft.Radius = doc.ParametricProperties.shaft_diameter / 2
shaft.Height = doc.ParametricProperties.shaft_length
shaft.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
body.addObject(shaft)

# Create a new PartDesign Sphere for the ball
ball = PartDesign.Sphere()
ball.Radius = doc.ParametricProperties.ball_diameter / 2
ball.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, shaft.Height / 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
body.addObject(ball)

# Create a new PartDesign Hole for the hole
hole = PartDesign.Hole()
hole.Diameter = doc.ParametricProperties.hole_diameter
hole.Depth = doc.ParametricProperties.hole_depth
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, shaft.Height / 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
body.addObject(hole)

# Add the body to the document
doc.addObject(body)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Set the active document back to the default document
FreeCAD.setActiveDocument("FreeCAD")
