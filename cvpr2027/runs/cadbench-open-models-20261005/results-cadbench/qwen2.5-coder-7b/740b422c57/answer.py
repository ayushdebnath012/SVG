import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical base
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 0.4  # outer_diameter / 2
cylinder.Height = 4.0  # pin_length

# Create a cylindrical hole
hole = body.newObject("PartDesign::Cylinder", "Hole")
hole.Radius = 0.4  # inner_diameter / 2
hole.Height = 4.0  # pin_length
hole.Placement.Base = FreeCAD.Vector(0, 0, 0.35)  # chamfer_length

# Create a chamfer
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Base = [cylinder, hole]
chamfer.Length1 = 0.35  # chamfer_length
chamfer.Length2 = 0.35  # chamfer_length

# Create a slot
slot = body.newObject("PartDesign::Pocket", "Slot")
slot.Base = [cylinder]
slot.Length = 0.5  # slot_length
slot.Angle = 15  # slot_angle
slot.Placement.Base = FreeCAD.Vector(0, 0, 2)  # Center of the slot

# Finalize the body
body.addFeature(chamfer)
body.addFeature(slot)

# Save the document
doc.saveAs("/app/answer.FCStd")
