import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Set the active document
FreeCAD.setActiveDocument("Flange")

# Create a new PartDesign Body
body = PartDesign.Body()

# Create a new Cylinder for the flange body
flange_body = PartDesign.Cylinder()
flange_body.Radius = doc.flange_outer_diameter / 2
flange_body.Height = doc.flange_thickness
flange_body.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
body.addObject(flange_body)

# Create a new Cylinder for the central through bore
bore = PartDesign.Cylinder()
bore.Radius = doc.bore_diameter / 2
bore.Height = doc.flange_thickness
bore.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, doc.flange_thickness / 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
body.addObject(bore)

# Create a new Hole for each bolt hole
for i in range(doc.number_of_bolt_holes):
    hole = PartDesign.Hole()
    hole.Radius = doc.bolt_hole_diameter / 2
    hole.Placement = FreeCAD.Placement(FreeCAD.Vector(doc.bolt_circle_diameter / 2 * math.cos(i * 2 * math.pi / doc.number_of_bolt_holes), doc.bolt_circle_diameter / 2 * math.sin(i * 2 * math.pi / doc.number_of_bolt_holes), doc.flange_thickness / 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
    body.addObject(hole)

# Add the body to the document
doc.addObject(body)

# Save the document
doc.saveAs(os.path.join(os.path.dirname(__file__), "answer.FCStd"))
