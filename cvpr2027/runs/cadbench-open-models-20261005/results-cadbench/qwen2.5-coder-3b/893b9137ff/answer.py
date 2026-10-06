import FreeCAD
import PartDesign
import Part

# Define the parameters
lego_unit_length = 8.0
lego_height = 9.6
lego_thickness = 1.6
num_studs_rows = 2
num_studs_columns = 4
studs_distance = 8.0
stud_center = (4.0, 4.0)
stud_diameter = 4.8
stud_height = 1.6
tube_center = (8.0, 8.0)
tube_outer_diameter = 6.4
tube_inner_diameter = 4.8
tube_distance = 8.0

# Create a new document
doc = FreeCAD.newDocument("LegoBrick")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create the lego brick body
lego_brick_body = PartDesign.Box(doc, lego_unit_length, lego_unit_length, lego_thickness)
body.addObject(lego_brick_body)

# Create the studs
for row in range(num_studs_rows):
    for col in range(num_studs_columns):
        stud_position = (stud_center[0] + col * studs_distance, stud_center[1] + row * studs_distance)
        stud = PartDesign.Cylinder(doc, stud_diameter / 2, stud_height)
        stud.Placement.Base = stud_position
        body.addObject(stud)

# Create the receiver tubes
for row in range(num_studs_rows):
    for col in range(num_studs_columns):
        tube_position = (tube_center[0] + col * tube_distance, tube_center[1] + row * tube_distance)
        tube = PartDesign.Cylinder(doc, (tube_outer_diameter - tube_inner_diameter) / 2, tube_distance)
        tube.Placement.Base = tube_position
        body.addObject(tube)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
