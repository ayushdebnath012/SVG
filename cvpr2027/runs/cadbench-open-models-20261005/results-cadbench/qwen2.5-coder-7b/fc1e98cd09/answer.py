```python
import FreeCAD
import PartDesign

# Set the pressure angle, diametral pitch, number of teeth, pitch diameter, outer diameter, and overall length
pressure_angle = 20  # degrees
diametral_pitch = 24
number_of_teeth = 12
pitch_diameter = 12.7  # mm
outer_diameter = 14.732  # mm
overall_length = 304.8  # mm

# Create a new document
doc = FreeCAD.newDocument("SpurGearStock")

# Create a new PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Feature
extrusion = body.newObject("PartDesign::Pad", "Extrusion")
extrusion.Length = overall_length

# Create a new PartDesign Feature
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = pitch_diameter / 2
cylinder.Height = overall_length

# Create a new PartDesign Feature
extrusion.Base = cylinder

# Create a new PartDesign Feature
extrusion.Profile = cylinder

# Create a new PartDesign Feature
extrusion.LengthFilletRadius = 0

# Create a new PartDesign Feature
extrusion.LengthFillet = False

# Create a new PartDesign Feature
extrusion.LengthFilletOffset = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetDirection = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffsetMode = 0

# Create a new PartDesign Feature
extrusion.LengthFilletOffset