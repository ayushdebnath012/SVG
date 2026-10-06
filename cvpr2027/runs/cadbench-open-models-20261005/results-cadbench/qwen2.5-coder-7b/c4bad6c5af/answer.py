import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical body
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 0.5  # pin_diameter / 2
cylinder.Height = 2.5  # pin_length

# Create a chamfer
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Base = (cylinder, ["Edge1"])
chamfer.Length1 = 0.08  # chamfer_length
chamfer.Base2 = (cylinder, ["Edge2"])
chamfer.Length2 = 0.08  # chamfer_length

# Create a slot
slot = body.newObject("PartDesign::Pocket", "Slot")
slot.Base = (cylinder, ["Edge3"])
slot.Length = 0.63  # slot_depth
slot.Base2 = (cylinder, ["Edge4"])
slot.Length2 = 0.63  # slot_depth

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
