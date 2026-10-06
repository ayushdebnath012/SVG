```python
import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1.5  # mm
number_of_teeth = 80
pitch_diameter = 120  # mm
outer_diameter = 123  # mm
face_width = 15  # mm
hub_diameter = 55  # mm
hub_width = 10  # mm
shaft_diameter = 12  # mm
overall_width = 25  # mm
addendum = gear_module  # ISO 54 / DIN 867
dedendum = 1.25 * gear_module  # ISO 54 / DIN 867
whole_depth = addendum + dedendum  # ISO 54 / DIN 867
clearance = dedendum - addendum  # ISO 54 / DIN 867
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 54
tooth_thickness = circular_pitch / 2  # ISO 54
root_diameter = pitch_diameter - (2 * dedendum)  # ISO 54 / DIN 867

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create the gear body
gear_body = PartDesign.Cylinder(doc, "GearBody", outer_diameter / 2, pitch_diameter / 2, whole_depth / 2)
gear_body.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the hub
hub = PartDesign.Cylinder(doc, "Hub", hub_diameter / 2, hub_diameter / 2, whole_depth / 2)
hub.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the central bore
bore = PartDesign.Cylinder(doc, "Bore", shaft_diameter / 2, shaft_diameter / 2, whole_depth / 2)
bore.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the gear teeth
gear_teeth = PartDesign.Cylinder(doc, "GearTeeth", outer_diameter / 2, pitch_diameter / 2, whole_depth / 2)
gear_teeth.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the hub teeth
hub_teeth = PartDesign.Cylinder(doc, "HubTeeth", hub_diameter / 2, hub_diameter / 2, whole_depth / 2)
hub_teeth.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the bore teeth
bore_teeth = PartDesign.Cylinder(doc, "BoreTeeth", shaft_diameter / 2, shaft_diameter / 2, whole_depth / 2)
bore_teeth.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Gray color

# Create the gear body and hub
gear_body_and_hub = PartDesign.Sketch(doc, "GearBodyAndHub")
gear_body_and_hub.addGeometry(gear_body.Shape)
gear_body_and_hub.addGeometry(hub.Shape)
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, 0), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part.Vector(0, 0, 1), 0))))
gear_body_and_hub.addConstraint(PartDesign.Constraint.Placement(Part.Placement(Part.Vector(0, 0, whole_depth / 2), Part.Rotation(Part