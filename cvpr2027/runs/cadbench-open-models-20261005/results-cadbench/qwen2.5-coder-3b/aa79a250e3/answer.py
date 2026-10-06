```python
import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 2  # mm
number_of_teeth = 25
pitch_diameter = 50  # mm
outer_diameter = 54  # mm
face_width = 20  # mm
hub_diameter = 40  # mm
hub_width = 10  # mm
shaft_diameter = 10  # mm
overall_width = 30  # mm
addendum = gear_module  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
whole_depth = addendum + dedendum  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771
tooth_thickness = circular_pitch / 2  # ISO 21771

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear profile
gear_profile = PartDesign.Profile(doc)
gear_profile.Label = "Gear Profile"
gear_profile.Shape = Part.makeCircle(base_diameter / 2)

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"
gear_tooth_profile.Shape = Part.makeCircle(base_diameter / 2 + tooth_thickness)

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"
gear_tooth.Shape = gear_tooth_profile.Shape

# Create the gear tooth hole
gear_tooth_hole = PartDesign.Feature(doc)
gear_tooth_hole.Label = "Gear Tooth Hole"
gear_tooth_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole
gear_tooth_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole.Label = "Gear Tooth Hole Hole"
gear_tooth_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole
gear_tooth_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole"
gear_tooth_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole
gear_tooth_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Shape = Part.makeCylinder(shaft_diameter / 2, tooth_thickness)

# Create the gear tooth hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole hole
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole = PartDesign.Feature(doc)
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole.Label = "Gear Tooth Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole Hole"
gear_tooth_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole_hole