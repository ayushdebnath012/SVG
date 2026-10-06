import FreeCAD
import PartDesign
import Part

# Define the parameters
outer_circle_diameter = 108  # mm
flange_thickness = 12.2  # mm
total_height = 17.5  # mm
bore_diameter = 34.5  # mm
hub_diameter = 50.8  # mm
raised_face_diameter = 49.3  # mm
raised_face_thickness = 2.0  # mm
bolt_circle_diameter = 79.2  # mm
bolt_hole_diameter = 15.7  # mm
number_bolt_holes = 4

# Create a new document
doc = FreeCAD.newDocument("SlipOnFlange")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create the flange body
flange_body = PartDesign.Feature(body)
flange_body.Shape = Part.makeBox(outer_circle_diameter, outer_circle_diameter, flange_thickness)

# Create the bore
bore = PartDesign.Feature(body)
bore.Shape = Part.makeCylinder(bore_diameter / 2, total_height - flange_thickness)

# Create the hub
hub = PartDesign.Feature(body)
hub.Shape = Part.makeCylinder(hub_diameter / 2, total_height - flange_thickness)

# Create the raised face
raised_face = PartDesign.Feature(body)
raised_face.Shape = Part.makeBox(raised_face_diameter, raised_face_diameter, raised_face_thickness)

# Create the bolt holes
bolt_holes = []
for i in range(number_bolt_holes):
    angle = 360 / number_bolt_holes * i
    x = outer_circle_diameter / 2 - (bolt_circle_diameter / 2 + bolt_hole_diameter / 2) * math.cos(math.radians(angle))
    y = outer_circle_diameter / 2 - (bolt_circle_diameter / 2 + bolt_hole_diameter / 2) * math.sin(math.radians(angle))
    bolt_holes.append(PartDesign.Feature(body))
    bolt_holes[-1].Shape = Part.makeCylinder(bolt_hole_diameter / 2, total_height - flange_thickness)

# Create the final solid body
solid_body = PartDesign.Feature(body)
solid_body.Shape = flange_body.Shape.cut(bore.Shape).cut(hub.Shape).cut(raised_face.Shape).cut(*bolt_holes)

# Save the document
doc.saveAs(os.path.join(os.path.dirname(__file__), "answer.FCStd"))
