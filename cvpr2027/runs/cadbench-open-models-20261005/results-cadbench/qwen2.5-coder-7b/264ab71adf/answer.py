import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Define the parameters
outside_diameter = 8.0  # mm
inner_diameter = 4.2  # mm
overall_height = 0.6  # mm
thickness_with_bearing_flat = 0.4  # mm
cone_height = 0.2  # mm

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cone
cone = body.newObject("PartDesign::Cylinder", "Cylinder")
cone.Radius1 = inner_diameter / 2
cone.Radius2 = outside_diameter / 2
cone.Height = overall_height
cone.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a plane for the bearing flat
plane = body.newObject("PartDesign::Plane", "Plane")
plane.Support = [(cone, "Face1")]
plane.SupportOffset = cone.Height - thickness_with_bearing_flat

# Create a revolved shape to create the bearing flat
revolved = body.newObject("PartDesign::Revolution", "Revolution")
revolved.Base = cone
revolved.Axis = plane.Support[0][1]
revolved.Placement.Base = FreeCAD.Vector(0, 0, cone.Height - thickness_with_bearing_flat)

# Create a plane for the other bearing flat
plane2 = body.newObject("PartDesign::Plane", "Plane2")
plane2.Support = [(cone, "Face1")]
plane2.SupportOffset = cone.Height

# Create a revolved shape to create the other bearing flat
revolved2 = body.newObject("PartDesign::Revolution", "Revolution2")
revolved2.Base = cone
revolved2.Axis = plane2.Support[0][1]
revolved2.Placement.Base = FreeCAD.Vector(0, 0, cone.Height)

# Finalize the body
body.finish()

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
