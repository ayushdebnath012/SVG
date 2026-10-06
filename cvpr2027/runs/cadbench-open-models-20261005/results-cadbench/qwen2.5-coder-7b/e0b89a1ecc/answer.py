import FreeCAD
import PartDesign

# Set the document name
doc_name = __file__.replace('.py', '.FCStd')
doc = FreeCAD.newDocument(doc_name)

# Set the parameters
pressure_angle = 20  # degrees
diametral_pitch = 24
number_of_teeth = 16
pitch_diameter = 16.9418  # mm
outer_diameter = 19.05  # mm
overall_length = 304.8  # mm
gear_module = 25.4 / diametral_pitch  # mm

# Create a PartDesign Body
body = doc.addObject('PartDesign::Body', 'Body')

# Create a cylindrical stock
cylinder = body.newObject('PartDesign::Cylinder', 'Cylinder')
cylinder.Radius = outer_diameter / 2
cylinder.Height = overall_length

# Create a datum plane for the gear teeth
datum_plane = body.newObject('PartDesign::Plane', 'DatumPlane')
datum_plane.Support = (cylinder, 'Face1')

# Create a datum axis for the gear teeth
datum_axis = body.newObject('PartDesign::Axis', 'DatumAxis')
datum_axis.Support = (datum_plane, 'Edge1')

# Create a gear teeth feature
gear_teeth = body.newObject('PartDesign::Gear', 'GearTeeth')
gear_teeth.Base = datum_axis
gear_teeth.NumberOfTeeth = number_of_teeth
gear_teeth.PressureAngle = pressure_angle
gear_teeth.DiametralPitch = diametral_pitch
gear_teeth.Profile = 'Spur'
gear_teeth.ProfileOffset = 0
gear_teeth.ProfileWidth = 0
gear_teeth.ProfileHeight = 0
gear_teeth.ProfileDepth = 0

# Finalize the body
body.finish()

# Save the document
doc.saveAs(doc_name)

# Close the document
FreeCAD.closeDocument(doc.Name)
