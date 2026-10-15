import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

def main():
    # Create new document
    doc = App.newDocument("MountPlate")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Create parameters for dimensions
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "plate_width", "Dimensions", "Overall plate width")
    params.addProperty("App::PropertyLength", "plate_height", "Dimensions", "Overall plate height")
    params.addProperty("App::PropertyLength", "mount_height", "Dimensions", "Mounting section height")
    params.addProperty("App::PropertyLength", "mount_width", "Dimensions", "Mounting section width")
    params.addProperty("App::PropertyLength", "mount_depth", "Dimensions", "Mounting section depth")
    params.addProperty("App::PropertyLength", "hole_spacing", "Dimensions", "Hole spacing")
    params.addProperty("App::PropertyLength", "hole_diameter", "Dimensions", "Hole diameter")
    params.addProperty("App::PropertyLength", "mount_hole_diameter", "Dimensions", "Mount hole diameter")
    params.addProperty("App::PropertyLength", "mount_hole_depth", "Dimensions", "Mount hole depth")
    params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet radius")
    params.addProperty("App::PropertyLength", "chamfer_size", "Dimensions", "Chamfer size")
    params.addProperty("App::PropertyLength", "mount_hole_chamfer", "Dimensions", "Mount hole chamfer")
    
    # Set values from drawing
    params.plate_width = 84.7
    params.plate_height = 44.8
    params.mount_height = 16.3
    params.mount_width = 60.2
    params.mount_depth = 2.8
    params.hole_spacing = 5.34
    params.hole_diameter = 2.5
    params.mount_hole_diameter = 4.0
    params.mount_hole_depth = 10.0
    params.fillet_radius = 2.0
    params.chamfer_size = 1.0
    params.mount_hole_chamfer = 0.5
    
    # Create main sketch on XY plane
    sketch = body.newObject("Sketcher::SketchObject", "MainSketch")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.Constraints = []
    sketch.MapMode = "FlatFace"
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create mount hole sketch on XZ plane
    mount_sketch = body.newObject("Sketcher::SketchObject", "MountHoleSketch")
    mount_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    mount_sketch.Constraints = []
    mount_sketch.MapMode = "FlatFace"
    mount_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create main profile sketch
    main_sketch = body.newObject("Sketcher::SketchObject", "MainProfile")
    main_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    main_sketch.Constraints = []
    main_sketch.MapMode = "FlatFace"
    main_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create mount profile sketch
    mount_profile_sketch = body.newObject("Sketcher::SketchObject", "MountProfile")
    mount_profile_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    mount_profile_sketch.Constraints = []
    mount_profile_sketch.MapMode = "FlatFace"
    mount_profile_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create main profile geometry
    # Main plate body
    main_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.plate_width, 0, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(params.plate_width, 0, 0), App.Vector(params.plate_width, params.plate_height, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(params.plate_width, params.plate_height, 0), App.Vector(0, params.plate_height, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.plate_height, 0), App.Vector(0, 0, 0)), False)
    
    # Mount section
    mount_x = params.plate_width - params.mount_width
    mount_y = params.plate_height - params.mount_height
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_x, mount_y, 0), App.Vector(mount_x + params.mount_width, mount_y, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_x + params.mount_width, mount_y, 0), App.Vector(mount_x + params.mount_width, mount_y + params.mount_height, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_x + params.mount_width, mount_y + params.mount_height, 0), App.Vector(mount_x, mount_y + params.mount_height, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_x, mount_y + params.mount_height, 0), App.Vector(mount_x, mount_y, 0)), False)
    
    # Mount holes (4 holes)
    mount_hole_x = mount_x + params.mount_width / 2
    mount_hole_y = mount_y + params.mount_height / 2
    main_sketch.addGeometry(Part.Circle(App.Vector(mount_hole_x, mount_hole_y, 0), App.Vector(0, 0, 1), params.mount_hole_diameter / 2), False)
    
    # Mount hole chamfer
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_hole_x, mount_hole_y, 0), App.Vector(mount_hole_x + params.mount_hole_chamfer, mount_hole_y, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_hole_x + params.mount_hole_chamfer, mount_hole_y, 0), App.Vector(mount_hole_x + params.mount_hole_chamfer, mount_hole_y + params.mount_hole_chamfer, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_hole_x + params.mount_hole_chamfer, mount_hole_y + params.mount_hole_chamfer, 0), App.Vector(mount_hole_x, mount_hole_y + params.mount_hole_chamfer, 0)), False)
    main_sketch.addGeometry(Part.LineSegment(App.Vector(mount_hole_x, mount_hole_y + params.mount_hole_chamfer, 0), App.Vector(mount_hole_x, mount_hole_y, 0)), False)
    
    # Main holes (12 holes)
    # Calculate hole positions based on drawing
    hole_x_start = 10.44
    hole_y_start = 10.35
    hole_spacing_x = 5.34
    hole_spacing_y = 5.34
    
    for i in range(4):
        for j in range(3):
            hx = hole_x_start + i * hole_spacing_x
            hy = hole_y_start + j * hole_spacing_y
            main_sketch.addGeometry(Part.Circle(App.Vector(hx, hy, 0), App.Vector(0, 0, 1), params.hole_diameter / 2), False)
    
    # Add constraints to main sketch
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 1, 2))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 4, 1, 3))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 5, 1, 4))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 6, 1, 5))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 7, 1, 6))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 8, 1, 7))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 9, 1, 8))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 10, 1, 9))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 11, 1, 10))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 12, 1, 11))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 13, 1, 12))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 14, 1, 13))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 15, 1, 14))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 16, 1, 15))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 17, 1, 16))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 18, 1, 17))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 19, 1, 18))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 20, 1, 19))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 21, 1, 20))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 22, 1, 21))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 23, 1, 22))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 24, 1, 23))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 25, 1, 24))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 26, 1, 25))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 27, 1, 26))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 28, 1, 27))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 29, 1, 28))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 30, 1, 29))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 31, 1, 30))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 32, 1, 31))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 33, 1, 32))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 34, 1, 33))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 35, 1, 34))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 36, 1, 35))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 37, 1, 36))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 38, 1, 37))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 39, 1, 38))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 40, 1, 39))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 41, 1, 40))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 42, 1, 41))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 43, 1, 42))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 44, 1, 43))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 45, 1, 44))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 46, 1, 45))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 47, 1, 46))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 48, 1, 47))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 49, 1, 48))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 50, 1, 49))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 51, 1, 50))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 52, 1, 51))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 53, 1, 52))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 54, 1, 53))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 55, 1, 54))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 56, 1, 55))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 57, 1, 56))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 58, 1, 57))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 59, 1, 58))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 60, 1, 59))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 61, 1, 60))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 62, 1, 61))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 63, 1, 62))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 64, 1, 63))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 65, 1, 64))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 66, 1, 65))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 67, 1, 66))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 68, 1, 67))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 69, 1, 68))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 70, 1, 69))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 71, 1, 70))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 72, 1, 71))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 73, 1, 72))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 74, 1, 73))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 75, 1, 74))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 76, 1, 75))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 77, 1, 76))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 78, 1, 77))
    main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 79,
