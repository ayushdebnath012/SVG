import FreeCAD
import PartDesign
import Part

# Define the parameters
overall_height = 21.0  # mm
flange_diameter = 28.0  # mm
flange_thickness = 4.0  # mm
hub_width = 22.0  # mm
inner_diameter = 14.0  # mm
hex_head_angle = 30.0  # degrees
hex_width_across_flats = hub_width  # DIN 6331
hex_width_across_corners = hex_width_across_flats / (2.0 * 3.141592653589793 / 60)  # ISO 4032 / DIN 934

# Create a new document
doc = FreeCAD.newDocument("HexFlangeNut")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create a hexagonal hub
hub = PartDesign.Hub(doc, "Hub")
hub.HubWidth = hub_width
hub.HexWidthAcrossFlats = hex_width_across_flats
hub.HexWidthAcrossCorners = hex_width_across_corners
hub.HexHeadAngle = hex_head_angle
hub.Height = overall_height / 2.0
hub.HubThickness = 0.0  # No hub thickness for a hex flange nut
hub.Plane = doc.ActiveView.ActiveObject  # Use the active view plane

# Create a circular flange
flange = PartDesign.Flange(doc, "Flange")
flange.Diameter = flange_diameter
flange.Thickness = flange_thickness
flange.Plane = doc.ActiveView.ActiveObject  # Use the active view plane
flange.Base = hub

# Create a plain through hole
hole = PartDesign.Hole(doc, "Hole")
hole.Diameter = inner_diameter
hole.Depth = overall_height
hole.Plane = doc.ActiveView.ActiveObject  # Use the active view plane
hole.Base = hub

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")
doc.Body.addObject(body)

# Save the document
output_path = __file__.replace(".py", ".FCStd")
doc.saveAs(output_path)

# Close the document
FreeCAD.closeDocument(doc.Name)
