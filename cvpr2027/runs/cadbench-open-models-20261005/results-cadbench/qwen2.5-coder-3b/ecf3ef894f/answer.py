import FreeCAD
import PartDesign
import Part

# Define the parameters
outer_diameter = 125.4125
flange_thickness = 23.01875
bolt_circle_diameter = 103.1875
mounting_hole_diameter = 13.49375
number_of_mounting_holes = 4
bore_diameter = 28.971875

# Create a new document
doc = FreeCAD.newDocument("RoundFlange")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create the outer flange plate
outer_flange = PartDesign.Plane(doc, "OuterFlange")
outer_flange.Plane.Shape = Part.makeCircle(outer_diameter / 2, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1))
outer_flange.Plane.Placement.Base = FreeCAD.Vector(0, 0, flange_thickness / 2)
outer_flange.Plane.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

# Create the central through bore
bore = PartDesign.Plane(doc, "Bore")
bore.Plane.Shape = Part.makeCircle(bore_diameter / 2, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1))
bore.Plane.Placement.Base = FreeCAD.Vector(0, 0, flange_thickness / 2)
bore.Plane.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

# Create the mounting holes
mounting_holes = []
for i in range(number_of_mounting_holes):
    angle = 2 * 3.14159 / number_of_mounting_holes * i
    hole_center = FreeCAD.Vector(bore_diameter / 2 * math.cos(angle), bore_diameter / 2 * math.sin(angle), flange_thickness / 2)
    hole = PartDesign.Plane(doc, f"MountingHole_{i+1}")
    hole.Plane.Shape = Part.makeCircle(mounting_hole_diameter / 2, hole_center, FreeCAD.Vector(0, 0, 1))
    hole.Plane.Placement.Base = hole_center
    hole.Plane.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)
    mounting_holes.append(hole)

# Create the final solid body
body.addObject(outer_flange)
body.addObject(bore)
for hole in mounting_holes:
    body.addObject(hole)

# Save the document
doc.saveAs(os.path.join(os.path.dirname(__file__), "answer.FCStd"))
