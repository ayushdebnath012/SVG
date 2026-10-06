import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a shaft
shaft_length = 1000.0
outer_diameter = 50.0
inner_diameter = 40.0
shaft_material_thickness = 5.0

# Create a cylindrical shaft
cylinder = body.newObject("PartDesign::Cylinder", "Shaft")
cylinder.Radius = outer_diameter / 2
cylinder.Height = shaft_length
cylinder.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a hole for the material thickness
material_hole = body.newObject("PartDesign::Pocket", "MaterialHole")
material_hole.Base = cylinder
material_hole.Length = shaft_material_thickness
material_hole.BaseOffset = FreeCAD.Vector(0, 0, 0)
material_hole.LengthFilletRadius = 0

# Create the flanges
flange_diameter = 100.0
flange_thickness = 20.0
flange_length = shaft_length + 2 * flange_thickness

# Create a cylindrical flange
flange = body.newObject("PartDesign::Cylinder", "Flange")
flange.Radius = flange_diameter / 2
flange.Height = flange_length
flange.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a hole for the material thickness
flange_material_hole = body.newObject("PartDesign::Pocket", "FlangeMaterialHole")
flange_material_hole.Base = flange
flange_material_hole.Length = shaft_material_thickness
flange_material_hole.BaseOffset = FreeCAD.Vector(0, 0, 0)
flange_material_hole.LengthFilletRadius = 0

# Create the bolt hole pattern
bolt_hole_diameter = 10.0
bolt_hole_circle_diameter = 80.0
number_of_bolt_holes = 4

# Create the bolt holes
for i in range(number_of_bolt_holes):
    angle = 2 * i * 3.14159 / number_of_bolt_holes
    x = bolt_hole_circle_diameter / 2 * FreeCAD.sin(angle)
    y = bolt_hole_circle_diameter / 2 * FreeCAD.cos(angle)
    bolt_hole = body.newObject("PartDesign::Hole", f"BoltHole{i}")
    bolt_hole.Base = flange
    bolt_hole.Diameter = bolt_hole_diameter
    bolt_hole.Length = flange_thickness
    bolt_hole.BaseOffset = FreeCAD.Vector(x, y, 0)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
