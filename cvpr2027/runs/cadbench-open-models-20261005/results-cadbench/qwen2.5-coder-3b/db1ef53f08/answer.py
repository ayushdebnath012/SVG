import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Set the active document
FreeCAD.setActiveDocument("Flange")

# Create a new PartDesign Body
body = PartDesign.Body()

# Create a new PartDesign Flange
flange = PartDesign.Flange()

# Set the parameters for the flange
flange.OuterDiameter = 69.454
flange.FlangeThickness = 26.194
flange.InnerDiameter = 34.925

# Add the flange to the body
body.addObject(flange)

# Create a new PartDesign Hole
hole = PartDesign.Hole()

# Set the parameters for the hole
hole.Diameter = 6.747
hole.Number = 4

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Bolt Circle
bolt_circle = PartDesign.BoltCircle()

# Set the parameters for the bolt circle
bolt_circle.Diameter = 57.547
bolt_circle.Number = 4

# Add the bolt circle to the body
body.addObject(bolt_circle)

# Create a new PartDesign Bolt
bolt = PartDesign.Bolt()

# Set the parameters for the bolt
bolt.Diameter = 6.747
bolt.Number = 4

# Add the bolt to the body
body.addObject(bolt)

# Save the document
doc.saveAs("/app/answer.FCStd")
