import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def create_document():
    doc = App.newDocument("Hydraulic_Cap")
    # Create reference planes
    # XY_Plane (Z=0)
    xy_plane = doc.addObject("Part::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # XZ_Plane (Y=0)
    xz_plane = doc.addObject("Part::Plane", "XZ_Plane")
    xz_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(90, 0, 0)) # Rotate -90 around X to make YZ the new XZ? 
    # Actually, let's stick to standard positions and attach sketches accordingly.
    # Standard XY is Z=0. Standard XZ is Y=0.
    xz_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 90)) # Rotate -90 around Z? No.
    # Rotation (x, y, z) rotates vector. 
    # To get XZ plane from XY (z=0), we rotate 90 deg around X axis. 
    # App.Rotation(90, 0, 0) rotates Z to Y. So Z=0 becomes Y=0. Correct.
    
    # YZ_Plane (X=0)
    yz_plane = doc.addObject("Part::Plane", "YZ_Plane")
    yz_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 90, 0))

    # Axes
    x_axis = doc.addObject("Part::Line", "X_Axis")
    x_axis.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0))
    x_axis.Line = Part.Line(App.Vector(-10,0,0), App.Vector(10,0,0))
    
    y_axis = doc.addObject("Part::Line", "Y_Axis")
    y_axis.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0))
    y_axis.Line = Part.Line(App.Vector(0,-10,0), App.Vector(0,10,0))
    
    z_axis = doc.addObject("Part::Line", "Z_Axis")
    z_axis.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0))
    z_axis.Line = Part.Line(App.Vector(0,0,-10), App.Vector(0,0,10))

    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "end_cap_outer_diameter", "Dimensions", "end_cap_outer_diameter"); params.end_cap_outer_diameter = 80.0
    params.addProperty("App::PropertyLength", "end_cap_thickness", "Dimensions", "end_cap_thickness"); params.end_cap_thickness = 130.0
    params.addProperty("App::PropertyLength", "annular_groove_inner_diameter", "Dimensions", "annular_groove_inner_diameter"); params.annular_groove_inner_diameter = 70.0
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "outer_diameter"); params.outer_diameter = 89.8937082
    params.addProperty("App::PropertyLength", "groove_depth", "Dimensions", "groove_depth"); params.groove_depth = 10.0
    params.addProperty("App::PropertyLength", "right_relief_length", "Dimensions", "right_relief_length"); params.right_relief_length = 31.1513256
    params.addProperty("App::PropertyLength", "right_relief_width", "Dimensions", "right_relief_width"); params.right_relief_width = 93.7870873
    params.addProperty("App::PropertyLength", "left_relief_length", "Dimensions", "left_relief_length"); params.left_relief_length = 30.8350117
    params.addProperty("App::PropertyLength", "left_relief_width", "Dimensions", "left_relief_width"); params.left_relief_width = 92.3636746
    params.addProperty("App::PropertyLength", "side_relief_depth", "Dimensions", "side_relief_depth"); params.side_relief_depth = 80.0
    params.addProperty("App::PropertyLength", "arc_relief_radius", "Dimensions", "arc_relief_radius"); params.arc_relief_radius = 28.1676805
    params.addProperty("App::PropertyLength", "arc_relief_depth", "Dimensions", "arc_relief_depth"); params.arc_relief_depth = 78.0
    params.addProperty("App::PropertyLength", "arc_relief_offset", "Dimensions", "arc_relief_offset"); params.arc_relief_offset = 39.0
    params.addProperty("App::PropertyLength", "small_center_bore_diameter", "Dimensions", "small_center_bore_diameter"); params.small_center_bore_diameter = 20.0
    params.addProperty("App::PropertyLength", "center_bore_depth", "Dimensions", "center_bore_depth"); params.center_bore_depth = 31.0
    params.addProperty("App::PropertyLength", "right_relief_x_min", "Dimensions", "right_relief_x_min"); params.right_relief_x_min = 12.5
    params.addProperty("App::PropertyLength", "right_relief_y_min", "Dimensions", "right_relief_y_min"); params.right_relief_y_min = -47.3680146
    params.addProperty("App::PropertyLength", "left_relief_x_min", "Dimensions", "left_relief_x_min"); params.left_relief_x_min = -43.3350117
    params.addProperty("App::PropertyLength", "left_relief_y_min", "Dimensions", "left_relief_y_min"); params.left_relief_y_min = -46.7353867
    params.addProperty("App::PropertyLength", "arc_relief_center_x", "Dimensions", "arc_relief_center_x"); params.arc_relief_center_x = 36.8323195
    params.addProperty("App::PropertyLength", "arc_relief_center_y", "Dimensions", "arc_relief_center_y"); params.arc_relief_center_y = -14.4165172
    params.addProperty("App::PropertyLength", "arc_relief_profile_x0", "Dimensions", "arc_relief_profile_x0"); params.arc_relief_profile_x0 = -17.5
    params.addProperty("App::PropertyLength", "arc_relief_profile_y0", "Dimensions", "arc_relief_profile_y0"); params.arc_relief_profile_y0 = 40.0
    params.addProperty("App::PropertyLength", "arc_relief_profile_x1", "Dimensions", "arc_relief_profile_x1"); params.arc_relief_profile_x1 = 47.2617529
    params.addProperty("App::PropertyLength", "arc_relief_profile_y1", "Dimensions", "arc_relief_profile_y1"); params.arc_relief_profile_y1 = 11.7492074
    params.addProperty("App::PropertyLength", "arc_relief_profile_x2", "Dimensions", "arc_relief_profile_x2"); params.arc_relief_profile_x2 = 48.6180581
    params.addProperty("App::PropertyLength", "arc_relief_profile_x3", "Dimensions", "arc_relief_profile_x3"); params.arc_relief_profile_x3 = 67.6634428

    # 1. Main Body
    sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_Main")
    sketch_main.Placement = App.Placement(App.Vector(0, 0, -params.end_cap_thickness/2))
    sketch_main.Placement = App.Placement(App.Vector(0, 0, -params.end_cap_thickness/2))
    sketch_main.Placement = App.Placement(App.Vector(0, 0, -params.end_cap_thickness/2))
    # Wait, Placement is App.Placement.
    # Top face is at +thickness/2, Bottom at -thickness/2.
    # Let's build the cylinder around Z axis, centered at Z=0.
    # So bottom is at -65, top is at +65.
    # The sketch for the cylinder profile should be in XZ plane (Y=0) or just extrude a circle in XY plane.
    # Let's use XY plane for the circle profile.
    
    # Actually, to make it easy for the groove and reliefs which are on the faces, let's build the cylinder first.
    # Cylinder profile: Circle in XY plane, centered at (0,0), radius = outer_diameter/2.
    # Extrude along Z.
    
    r_outer = params.end_cap_outer_diameter / 2.0
    # Circle in XY plane (Z = -thickness/2)
    sk_cyl = body.newObject("Sketcher::SketchObject", "Sketch_Cylinder_Profile")
    sk_cyl.Placement = App.Placement(App.Vector(0, 0, -params.end_cap_thickness/2))
    # Add circle
    sk_cyl.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_outer), False)
    sk_cyl.Constrain = True
    sk_cyl.addConstraint(Sketcher.Constraint("Center", 0, 0, 0)) # Center of circle
    sk_cyl.addConstraint(Sketcher.Constraint("Size", 0, 0, 0, 1)) # Radius? No, need to link radius to param.
    # Let's add expression to radius
    sk_cyl.Expression = "Radius", "Parameters.outer_diameter/2"
    # Wait, Circle object has Radius property.
    sk_cyl.Radius = "Parameters.outer_diameter/2"
    
    # Pad the cylinder
    pad_cyl = body.newObject("PartDesign::Pad", "Pad_Cylinder")
    pad_cyl.Profile = sk_cyl
    pad_cyl.Length = params.end_cap_thickness
    pad_cyl.Midplane = True
    
    # 2. Top Face Rebate (Groove)
    # Extends groove_depth inward from top face (+thickness/2).
    # Top face is Z = +65. Rebate goes down to Z = +55.
    # It's a ring cutout.
    # Outer boundary: outer_diameter (extends beyond main cylinder? "recessed shoulder opens into the outer cylindrical surface")
    # This implies the groove goes wider than the cylinder at the top.
    # "Its outer boundary uses outer_diameter... extends beyond the main cylinder"
    # Wait, the main cylinder is 80mm. The groove outer boundary is 89.89mm.
    # So the groove cuts into the side of the cylinder.
    # It's a pocket with an annular profile.
    # Outer radius of groove: outer_diameter / 2
    # Inner radius of groove: annular_groove_inner_diameter / 2
    # Depth: groove_depth
    
    r_groove_outer = params.outer_diameter / 2.0
    r_groove_inner = params.annular_groove_inner_diameter / 2.0
    
    # Sketch in XY plane at Z = +thickness/2
    sk_groove = body.newObject("Sketcher::SketchObject", "Sketch_Groove")
    sk_groove.Placement = App.Placement(App.Vector(0, 0, params.end_cap_thickness/2))
    
    # Outer arc
    sk_groove.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_groove_outer), False)
    # Inner arc
    sk_groove.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_groove_inner), False)
    # Constraint: Concentric
    sk_groove.addConstraint(Sketcher.Constraint("Concentric", 0, 0, 0, 0, 1, 0)) # Circle 0, Circle 1
    
    # Expressions
    sk_groove.Expression = "R1", "Parameters.outer_diameter/2"
    sk_groove.Expression = "R2", "Parameters.annular_groove_inner_diameter/2"
    # Note: Property names might be R1, R2 if added in order, or we set Radius directly.
    # Better to set Radius properties explicitly.
    sk_groove.Radius = "Parameters.outer_diameter/2" # This sets the first circle? No, there are two.
    # Let's use addGeometry with expressions?
    # Or just set the properties.
    # Let's assume the circles are added in order.
    # Actually, easiest way:
    # Circle 1 (Outer): Radius = outer_diameter/2
    # Circle 2 (Inner): Radius = annular_groove_inner_diameter/2
    # We need to select them.
    # Let's just set the properties after creation.
    
    # Pad the groove (subtractive)
    pocket_groove = body.newObject("PartDesign::Pocket", "Pocket_Groove")
    pocket_groove.Profile = sk_groove
    pocket_groove.Length = params.groove_depth
    pocket_groove.Type = "Blind"
    pocket_groove.Placement = App.Placement(App.Vector(0, 0, params.end_cap_thickness/2 + params.groove_depth)) # Reference to face? 
    # Actually, standard pocket on XY plane at Z=+H, extruding -Z.
    pocket_groove.Placement = App.Placement(App.Vector(0, 0, params.end_cap_thickness/2))
    pocket_groove.Placement = App.Placement(App.Vector(0, 0, params.end_cap_thickness/2))
    pocket_groove.Placement = App.Placement(App.Vector(0, 0, params.end_cap_thickness/2))
    # To extrude downwards, we need to specify direction or use Type=Blind with length and it goes away from plane normal?
    # Plane normal is +Z. Length goes in +Z direction by default.
    # So we need to reverse the pocket or place the sketch on the other side?
    # If sketch is on Top Face (normal +Z), and we want to cut INWARD (-Z), we need to reverse.
    pocket_groove.Reverse = True
    
    # 3. Small Center Bore
    # Starts on top face, depth center_bore_depth.
    # Diameter: small_center_bore_diameter.
    
    sk_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
    sk_bore.Placement = App.Placement(App.Vector(0, 0, params.end_cap_thickness/2))
    sk_bore.Radius = params.small_center_bore_diameter / 2.0
    
    pocket_bore = body.newObject("PartDesign::Pocket", "Pocket_Bore")
    pocket_bore.Profile = sk_bore
    pocket_bore.Length = params.center_bore_depth
    pocket_bore.Type = "Blind"
    pocket_bore.Reverse = True
    
    # 4. Bottom Side Reliefs
    # Two rectangular reliefs on the bottom face (Z = -thickness/2).
    # Extend side_relief_depth toward the top (in +Z direction).
    # Local frame of bottom face: X is global X, Y is global Y, Z is global Z.
    # Right relief:
    #   Starts at (right_relief_x_min, right_relief_y_min) in local frame.
    #   Spans right_relief_length in +X, right_relief_width in +Y.
    #   Inner flank at +right_relief_x_min.
    # Left relief:
    #   Starts at (left_relief_x_min, left_relief_y_min).
    #   Spans left_relief_length in +X, left_relief_width in +Y.
    #   Inner flank at -right_relief_x_min.
    
    # Right Relief
    sk_relief_right = body.newObject("Sketcher::SketchObject", "Sketch_Relief_Right")
    sk_relief_right.Placement = App.Placement(App.Vector(0, 0, -params.end_cap_thickness/2))
    
    # Points:
    p0 = App.Vector(params.right_relief_x_min, params.right_relief_y_min, 0)
    p1 = App.Vector(params.right_relief_x_min + params.right_relief_length, params.right_relief_y_min, 0)
    p2 = App.Vector(params.right_relief_x_min + params.right_relief_length, params.right_relief_y_min + params.right_relief_width, 0)
    p3 = App.Vector(params.right_relief_x_min, params.right_relief_y_min + params.right_relief_width, 0)
    
    sk_relief_right.addGeometry(Part.LineSegment(p0, p1), False)
    sk_relief_right.addGeometry(Part.LineSegment(p1, p2), False)
    sk_relief_right.addGeometry(Part.LineSegment(p2, p3), False)
    sk_relief_right.addGeometry(Part.LineSegment(p3, p0), False)
    
    # Left Relief
    sk_relief_left = body.newObject("Sketcher::SketchObject", "Sketch_Relief_Left")
    sk_relief_left.Placement = App.Placement(App.Vector(0, 0, -params.end_cap_thickness/2))
    
    p4 = App.Vector(params.left_relief_x_min, params.left_relief_y_min, 0)
    p5 = App.Vector(params.left_relief_x_min + params.left
