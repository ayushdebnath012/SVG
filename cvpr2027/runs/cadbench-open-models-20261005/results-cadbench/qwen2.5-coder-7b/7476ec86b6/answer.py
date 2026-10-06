import FreeCAD
import PartDesign

# Set the document name
doc_name = __file__.replace('.py', '.FCStd')
doc = FreeCAD.newDocument(doc_name)

# Set the parameters
pressure_angle = 20  # degrees
diametral_pitch = 32
number_of_teeth = 20
pitch_diameter = 15.875  # mm
outer_diameter = 17.526  # mm
face_width = 304.8  # mm
gear_module = 25.4 / diametral_pitch  # mm

# Create a PartDesign Body
body = doc.addObject('PartDesign::Body', 'Body')

# Create a cylindrical gear stock
cylinder = body.newObject('PartDesign::Cylinder', 'Cylinder')
cylinder.Radius = outer_diameter / 2
cylinder.Height = face_width

# Create a datum plane for the gear teeth
datum_plane = body.newObject('PartDesign::Plane', 'DatumPlane')
datum_plane.Support = (cylinder, 'Face', (0, 0, 0))

# Create a datum axis for the gear teeth
datum_axis = body.newObject('PartDesign::Axis', 'DatumAxis')
datum_axis.Support = (cylinder, 'Edge', (0, 0, 0))

# Create a gear teeth feature
gear_teeth = body.newObject('PartDesign::Gear', 'GearTeeth')
gear_teeth.Base = datum_plane
gear_teeth.Axis = datum_axis
gear_teeth.NumberOfTeeth = number_of_teeth
gear_teeth.PressureAngle = pressure_angle
gear_teeth.GearModule = gear_module

# Finalize the body
body.finish()

# Save the document
doc.saveAs(doc_name)

# Close the document
FreeCAD.closeDocument(doc.Name)
