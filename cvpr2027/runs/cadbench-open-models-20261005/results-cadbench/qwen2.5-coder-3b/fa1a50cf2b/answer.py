import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 32
pitch_diameter = 32  # mm
outer_diameter = 34  # mm
face_width = 10  # mm
hub_diameter = 26  # mm
hub_width = 10  # mm
shaft_diameter = 8  # mm
overall_width = 20  # mm
addendum = pitch_diameter / number_of_teeth  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
whole_depth = addendum + dedendum  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create the gear body
gear_body = PartDesign.Cylinder(doc, "GearBody", outer_diameter / 2, whole_depth, pitch_diameter / 2)
gear_body.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the hub
hub = PartDesign.Cylinder(doc, "Hub", hub_diameter / 2, hub_width, hub_diameter / 2)
hub.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray color

# Create the shaft
shaft = PartDesign.Cylinder(doc, "Shaft", shaft_diameter / 2, whole_depth, shaft_diameter / 2)
shaft.ViewObject.ShapeColor = (0.2, 0.2, 0.2)  # Dark gray color

# Create the round bore
bore = PartDesign.Cylinder(doc, "Bore", shaft_diameter / 2, whole_depth, shaft_diameter / 2)
bore.ViewObject.ShapeColor = (0.4, 0.4, 0.4)  # Light gray color

# Create the gear teeth
teeth = PartDesign.ToothedGear(doc, "Teeth", number_of_teeth, pitch_diameter, face_width, pressure_angle)
teeth.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # Dark gray color

# Create the gear body feature
gear_body_feature = PartDesign.Feature(doc, "GearBodyFeature", gear_body)
gear_body_feature.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the hub feature
hub_feature = PartDesign.Feature(doc, "HubFeature", hub)
hub_feature.ViewObject.ShapeColor = (0.8, 0.8, 0.8)  # Light gray color

# Create the shaft feature
shaft_feature = PartDesign.Feature(doc, "ShaftFeature", shaft)
shaft_feature.ViewObject.ShapeColor = (0.2, 0.2, 0.2)  # Dark gray color

# Create the bore feature
bore_feature = PartDesign.Feature(doc, "BoreFeature", bore)
bore_feature.ViewObject.ShapeColor = (0.4, 0.4, 0.4)  # Light gray color

# Create the teeth feature
teeth_feature = PartDesign.Feature(doc, "TeethFeature", teeth)
teeth_feature.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # Dark gray color

# Create the gear body feature in the body
body.addObject(gear_body_feature)

# Create the hub feature in the body
body.addObject(hub_feature)

# Create the shaft feature in the body
body.addObject(shaft_feature)

# Create the bore feature in the body
body.addObject(bore_feature)

# Create the teeth feature in the body
body.addObject(teeth_feature)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
