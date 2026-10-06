import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Staircase")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Define the stair profile 2D
number_of_steps = 5
step_riser = 170.0
step_depth = 300.0
total_rise = number_of_steps * step_riser
total_run = number_of_steps * step_depth
profile_origin = (0.0, 0.0)
tread_direction = (1.0, 0.0)
rise_direction = (0.0, 1.0)

# Create a PartDesign Profile
profile = PartDesign.Profile(doc)
profile.Shape = Part.makePolygon([
    (profile_origin[0], profile_origin[1]),
    (profile_origin[0] + total_run, profile_origin[1]),
    (profile_origin[0] + total_run, profile_origin[1] + total_rise),
    (profile_origin[0], profile_origin[1] + total_rise)
])

# Create a PartDesign Extrusion
extrusion = PartDesign.Extrusion(doc)
extrusion.Profile = profile
extrusion.Direction = (0.0, 1.0, 0.0)
extrusion.Length = step_width
extrusion.Base = body

# Add the extrusion to the body
body.addObject(extrusion)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
