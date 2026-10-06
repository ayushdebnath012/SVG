import FreeCAD
import PartDesign
import Part

# Define the parameters
outer_diameter = 69.453
flange_thickness = 13.097
pitch_circle_diameter = 57.944
bolt_hole_diameter = 6.747
number_bolt_holes = 4
bore_diameter = 34.925

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new circular flange body
flange_body = PartDesign.CircularFlange(doc, body, outer_diameter, flange_thickness)

# Create a new central through bore
bore = PartDesign.Bore(doc, body, bore_diameter)

# Create a new bolt circle
bolt_circle = PartDesign.BoltCircle(doc, body, pitch_circle_diameter, number_bolt_holes)

# Create a new bolt hole array
bolt_hole_array = PartDesign.BoltHoleArray(doc, body, bolt_circle, bolt_hole_diameter)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
