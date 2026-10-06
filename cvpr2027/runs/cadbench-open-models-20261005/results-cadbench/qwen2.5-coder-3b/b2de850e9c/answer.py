import FreeCAD
import PartDesign

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1.5  # mm
number_of_teeth = 50
pitch_diameter = 75  # mm
outer_diameter = 78  # mm
face_width = 15  # mm
hub_diameter = 45  # mm
hub_width = 10  # mm
shaft_diameter = 10  # mm
overall_width = 25  # mm
addendum = gear_module  # ISO 21771 / DIN 867
dedendum = 1.25 * gear_module  # ISO 21771 / DIN 867
whole_depth = addendum + dedendum  # ISO 21771 / DIN 867
root_diameter = pitch_diameter - (2 * dedendum)  # ISO 21771 / DIN 867

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.ToothProfile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"
gear_tooth_profile.NumberOfTeeth = number_of_teeth
gear_tooth_profile.GearModule = gear_module
gear_tooth_profile.PressureAngle = pressure_angle
gear_tooth_profile.FaceWidth = face_width
gear_tooth_profile.PitchDiameter = pitch_diameter
gear_tooth_profile.OuterDiameter = outer_diameter
gear_tooth_profile.RootDiameter = root_diameter
gear_tooth_profile.Addendum = addendum
gear_tooth_profile.Dedendum = dedendum
gear_tooth_profile.WholeDepth = whole_depth

# Create the gear body from the tooth profile
gear_body.addFeature(gear_tooth_profile)

# Create the hub
hub = PartDesign.Hub(doc)
hub.Label = "Hub"
hub.HubDiameter = hub_diameter
hub.HubWidth = hub_width
hub.OverallWidth = overall_width

# Create the hub from the gear body
gear_body.addFeature(hub)

# Create the bore
bore = PartDesign.Bore(doc)
bore.Label = "Bore"
bore.ShootDiameter = shaft_diameter

# Create the bore from the gear body
gear_body.addFeature(bore)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
