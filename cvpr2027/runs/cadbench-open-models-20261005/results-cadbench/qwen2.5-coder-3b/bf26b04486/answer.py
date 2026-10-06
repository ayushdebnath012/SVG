import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HexFlangeNut")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a PartDesign Body
body = PartDesign.Body()

# Create a PartDesign Flange
flange = PartDesign.Flange()
flange.Base = body
flange.Diameter = doc.addObject("PartDesign::Feature", "Flange")
flange.Diameter.Value = doc.flange_diameter
flange.Thickness = doc.addObject("PartDesign::Feature", "FlangeThickness")
flange.Thickness.Value = doc.flange_thickness
flange.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a PartDesign Hex
hex_hub = PartDesign.Hex()
hex_hub.Base = body
hex_hub.Width = doc.addObject("PartDesign::Feature", "HubWidth")
hex_hub.Width.Value = doc.hub_width
hex_hub.HeadWidthAcrossFlats = doc.addObject("PartDesign::Feature", "HeadWidthAcrossFlats")
hex_hub.HeadWidthAcrossFlats.Value = doc.hex_head_width_across_flats
hex_hub.HeadWidthAcrossCorners = doc.addObject("PartDesign::Feature", "HeadWidthAcrossCorners")
hex_hub.HeadWidthAcrossCorners.Value = doc.hex_head_width_across_corners
hex_hub.HeadAngle = doc.addObject("PartDesign::Feature", "HeadAngle")
hex_hub.HeadAngle.Value = doc.hex_head_angle
hex_hub.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, doc.flange_thickness), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a PartDesign Hole
through_hole = PartDesign.Hole()
through_hole.Base = body
through_hole.Diameter = doc.addObject("PartDesign::Feature", "ThroughHoleDiameter")
through_hole.Diameter.Value = doc.through_hole_diameter
through_hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, doc.flange_thickness + doc.hex_height_above_flange), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a PartDesign Stack
stack = PartDesign.Stack()
stack.Base = body
stack.Components = [flange, hex_hub, through_hole]
stack.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a PartDesign Body from the stack
body_from_stack = PartDesign.Body()
body_from_stack.addComponents(stack.Components)

# Set the active object to the body
FreeCAD.ActiveDocument.setActiveObject(body_from_stack.Name)

# Save the document
doc.saveAs("/app/answer.FCStd")
