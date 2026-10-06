import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
number_teeth = 23
spline_module = 3
spline_pitch_diameter = number_teeth * spline_module
spline_height = 10
pressure_angle = math.radians(30)
fillet_radius = 1.2

# Create a new document
doc = FreeCAD.newDocument("SplineTooth")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new cylindrical spline
spline = PartDesign.Spline(body)
spline.NumberOfPoints = number_teeth
spline.PitchDiameter = spline_pitch_diameter
spline.Height = spline_height
spline.PressureAngle = pressure_angle
spline.FilletRadius = fillet_radius

# Create a new PartDesign feature to fillet the root of each tooth
fillet_feature = PartDesign.Fillet(body)
fillet_feature.FilletRadius = fillet_radius
fillet_feature.FilletEdges = spline.Edges

# Create a new Part::Feature to combine the spline and fillet
feature = PartDesign.Feature(body)
feature.Shape = spline.Shape

# Save the document
doc.saveAs("/app/answer.FCStd")
