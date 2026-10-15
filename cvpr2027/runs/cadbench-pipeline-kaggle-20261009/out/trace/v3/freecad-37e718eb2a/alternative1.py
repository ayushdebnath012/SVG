import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

def create_doc():
    doc = App.newDocument("PartBracket")
    
    # --- Parameters ---
    # Create a parameter set for easy editing
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "corner_arc_radius", "Dimensions", "radius of the inner quarter round")
    params.corner_arc_radius = 63.50
    params.addProperty("App::PropertyLength", "plate_thickness", "Dimensions", "thickness of the main supporting body")
    params.plate_thickness = 482.60
    params.addProperty("App::PropertyLength", "cross_section_length", "Dimensions", "horizontal extent")
    params.cross_section_length = 255.93
    params.addProperty("App::PropertyLength", "cross_section_width", "Dimensions", "vertical extent")
    params.cross_section_width = 255.94
    params.addProperty("App::PropertyLength", "support_profile_inner_wall_top_y", "Dimensions", "y of inner wall top")
    params.support_profile_inner_wall_top_y = 175.36
    params.addProperty("App::PropertyLength", "support_profile_upper_shoulder_x", "Dimensions", "x of upper shoulder")
    params.support_profile_upper_shoulder_x = 58.62
    params.addProperty("App::PropertyLength", "support_profile_upper_apex_x", "Dimensions", "x of upper apex")
    params.support_profile_upper_apex_x = 139.19
    params.addProperty("App::PropertyLength", "support_profile_outer_diagonal_y", "Dimensions", "y of outer diagonal corner")
    params.support_profile_outer_diagonal_y = 139.19
    params.addProperty("App::PropertyLength", "support_profile_neck_x", "Dimensions", "x of neck start")
    params.support_profile_neck_x = 165.10
    params.addProperty("App::PropertyLength", "support_profile_neck_y", "Dimensions", "y of neck start")
    params.support_profile_neck_y = 48.36
    params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "count of main bores")
    params.number_of_mounting_holes = 3
    params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "diameter of main bores")
    params.mounting_hole_diameter = 127.00
    params.addProperty("App::PropertyLength", "adjacent_hole_center_spacing", "Dimensions", "spacing between main bores")
    params.adjacent_hole_center_spacing = 146.05
    params.addProperty("App::PropertyLength", "shaped_opening_depth", "Dimensions", "depth of shaped cutouts")
    params.shaped_opening_depth = 120.65
    params.addProperty("App::PropertyLength", "concave_profile_arc_radius", "Dimensions", "radius of concave sides")
    params.concave_profile_arc_radius = 76.20
    params.addProperty("App::PropertyLength", "mounting_lobe_arc_radius", "Dimensions", "radius of lobes")
    params.mounting_lobe_arc_radius = 12.70
    params.addProperty("App::PropertyLength", "profile_mounting_hole_diameter", "Dimensions", "diameter of small holes")
    params.profile_mounting_hole_diameter = 25.40
    params.addProperty("App::PropertyLength", "inner_lobe_center_x", "Dimensions", "x of inner lobe center")
    params.inner_lobe_center_x = -73.03
    params.addProperty("App::PropertyLength", "outer_lobe_center_x", "Dimensions", "x of outer lobe center")
    params.outer_lobe_center_x = -219.07
    params.addProperty("App::PropertyLength", "lobe_center_y", "Dimensions", "y of lobe centers")
    params.lobe_center_y = 55.88
    params.addProperty("App::PropertyLength", "secondary_concave_center_y", "Dimensions", "y of secondary concave center")
    params.secondary_concave_center_y = 0.01
    params.addProperty("App::PropertyLength", "outer_loop_upper_inner_x", "Dimensions", "x upper inner loop")
    params.outer_loop_upper_inner_x = -176.49
    params.addProperty("App::PropertyLength", "outer_loop_lower_inner_x", "Dimensions", "x lower inner loop")
    params.outer_loop_lower_inner_x = -176.52
    params.addProperty("App::PropertyLength", "outer_loop_outer_x", "Dimensions", "x outer loop")
    params.outer_loop_outer_x = -228.60
    params.addProperty("App::PropertyLength", "outer_loop_upper_y", "Dimensions", "y upper outer loop")
    params.outer_loop_upper_y = 69.86
    params.addProperty("App::PropertyLength", "outer_loop_lower_y", "Dimensions", "y lower outer loop")
    params.outer_loop_lower_y = -69.84
    params.addProperty("App::PropertyLength", "outer_loop_lobe_join_offset_y", "Dimensions", "y offset for lobe join")
    params.outer_loop_lobe_join_offset_y = 64.28
    params.addProperty("App::PropertyLength", "outer_loop_lobe_inner_offset_y", "Dimensions", "y offset for lobe inner join")
    params.outer_loop_lobe_inner_offset_y = 47.48
    params.addProperty("App::PropertyLength", "lens_outer_x", "Dimensions", "x of lens outer edge")
    params.lens_outer_x = -30.45
    params.addProperty("App::PropertyLength", "upper_lens_inner_x", "Dimensions", "x upper lens inner")
    params.upper_lens_inner_x = -115.61
    params.addProperty("App::PropertyLength", "lower_lens_inner_x", "Dimensions", "x lower lens inner")
    params.lower_lens_inner_x = -115.58
    params.addProperty("App::PropertyInteger", "number_of_secondary_mounting_holes", "Dimensions", "count of small holes")
    params.number_of_secondary_mounting_holes = 2
    params.addProperty("App::PropertyLength", "small_mounting_hole_diameter", "Dimensions", "diameter of small holes")
    params.small_mounting_hole_diameter = 9.52
    params.addProperty("App::PropertyLength", "small_hole_depth", "Dimensions", "depth of small holes")
    params.small_hole_depth = 76.00
    params.addProperty("App::PropertyLength", "bracket_plate_thickness", "Dimensions", "thickness of flanges")
    params.bracket_plate_thickness = 25.40
    params.addProperty("App::PropertyLength", "blind_recess_depth", "Dimensions", "depth of blind recess")
    params.blind_recess_depth = 22.00
    params.addProperty("App::PropertyInteger", "opposed_flange_count", "Dimensions", "number of flanges")
    params.opposed_flange_count = 2
    params.addProperty("App::PropertyLength", "flange_recess_root_x", "Dimensions", "x of recess root")
    params.flange_recess_root_x = -152.40
    params.addProperty("App::PropertyLength", "flange_recess_root_outer_y", "Dimensions", "y of recess root outer")
    params.flange_recess_root_outer_y = 53.62
    params.addProperty("App::PropertyLength", "flange_recess_root_inner_y", "Dimensions", "y of recess root inner")
    params.flange_recess_root_inner_y = 48.62
    params.addProperty("App::PropertyLength", "flange_recess_upper_inner_x", "Dimensions", "x of upper recess inner")
    params.flange_recess_upper_inner_x = -38.36
    params.addProperty("App::PropertyLength", "flange_recess_upper_edge_y", "Dimensions", "y of upper recess edge")
    params.flange_recess_upper_edge_y = 162.66
    params.addProperty("App::PropertyLength", "flange_recess_mid_x", "Dimensions", "x of mid recess")
    params.flange_recess_mid_x = -63.88
    params.addProperty("App::PropertyLength", "flange_recess_apex_x", "Dimensions", "x of apex recess")
    params.flange_recess_apex_x = -139.19
    params.addProperty("App::PropertyLength", "flange_recess_apex_y", "Dimensions", "y of apex recess")
    params.flange_recess_apex_y = 237.98
    params.addProperty("App::PropertyLength", "flange_recess_outer_x", "Dimensions", "x of outer recess")
    params.flange_recess_outer_x = -237.97
    params.addProperty("App::PropertyLength", "flange_recess_outer_y", "Dimensions", "y of outer recess")
    params.flange_recess_outer_y = 139.20

    # --- Setup Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Get reference planes
    XY_Plane = doc.addObject("PartDesign::PlanarObject", "XY_Plane")
    XY_Plane.Placement = App.Placement(App.Vector(0, 0, 0))
    XY_Plane.Rotation = App.Rotation(0, 0, 0)
    XY_Plane.Base = "XY_Plane"
    doc.recompute()
    
    XZ_Plane = doc.addObject("PartDesign::PlanarObject", "XZ_Plane")
    XZ_Plane.Placement = App.Placement(App.Vector(0, 0, 0))
    XZ_Plane.Rotation = App.Rotation(0, 90, 0)
    XZ_Plane.Base = "XZ_Plane"
    doc.recompute()
    
    YZ_Plane = doc.addObject("PartDesign::PlanarObject", "YZ_Plane")
    YZ_Plane.Placement = App.Placement(App.Vector(0, 0, 0))
    YZ_Plane.Rotation = App.Rotation(90, 0, 0)
    YZ_Plane.Base = "YZ_Plane"
    doc.recompute()
    
    Z_Axis = doc.addObject("PartDesign::PlanarObject", "Z_Axis")
    Z_Axis.Placement = App.Placement(App.Vector(0, 0, 0))
    Z_Axis.Rotation = App.Rotation(0, 0, 0)
    Z_Axis.Base = "Z_Axis"
    doc.recompute()

    # --- Feature 1: Main Body Sketch (Transverse Section) ---
    # This sketch defines the cross-section in the XY plane (Z=0).
    # We define the profile from X=0 to X=plate_thickness/2, then mirror it later or pad symmetrically.
    # Based on description: "The transverse outline lies in the positive quadrant about the center of its inward quarter-round... The body spans plate_thickness symmetrically about its axial mid-plane."
    # Let's define the half-profile in the first quadrant (X>0, Y>0).
    
    sketch_main = body.newObject("Sketcher::SketchObject", "MainSketch")
    sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_main.Placement.Rotation = App.Rotation(0, 0, 0)
    sketch_main.ObjectName = "MainSketch"
    sketch_main.Support = (XY_Plane, [""])
    sketch_main.MapMode = "FlatFace"
    
    # Points for the main profile (Right Half: X > 0)
    # Center of quarter round is at (0, 0). Radius = corner_arc_radius.
    # Quarter round goes from (0, R) to (R, 0).
    # Inner vertical wall rises from (R, 0) to (R, support_profile_inner_wall_top_y).
    # Shoulder from (R, support_profile_inner_wall_top_y) to (support_profile_upper_shoulder_x, support_profile_inner_wall_top_y).
    # Slope to apex (support_profile_upper_apex_x, support_profile_outer_diagonal_y).
    # Neck to (support_profile_neck_x, support_profile_neck_y).
    # Down to datum (support_profile_neck_x, 0).
    # Close to (0, 0).
    
    # Note: The description says "lies in the positive quadrant about the center of its inward quarter-round".
    # So the quarter round is at the origin.
    
    # Define points
    P1 = App.Vector(0, 0) # Center of quarter round
    P2 = App.Vector(params.corner_arc_radius.Value, 0) # End of quarter round
    P3 = App.Vector(params.corner_arc_radius.Value, params.support_profile_inner_wall_top_y.Value) # Top of inner wall
    P4 = App.Vector(params.support_profile_upper_shoulder_x.Value, params.support_profile_inner_wall_top_y.Value) # Shoulder
    P5 = App.Vector(params.support_profile_upper_apex_x.Value, params.support_profile_outer_diagonal_y.Value) # Apex
    P6 = App.Vector(params.support_profile_neck_x.Value, params.support_profile_neck_y.Value) # Neck
    P7 = App.Vector(params.support_profile_neck_x.Value, 0) # Neck bottom
    
    # Add Lines
    sketch_main.addGeometry(Part.LineSegment(P1, P2), False)
    sketch_main.addGeometry(Part.LineSegment(P2, P3), False)
    sketch_main.addGeometry(Part.LineSegment(P3, P4), False)
    sketch_main.addGeometry(Part.LineSegment(P4, P5), False)
    sketch_main.addGeometry(Part.LineSegment(P5, P6), False)
    sketch_main.addGeometry(Part.LineSegment(P6, P7), False)
    sketch_main.addGeometry(Part.LineSegment(P7, P1), False) # Close loop
    
    # Add constraints
    sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", 0, 0), 0) # P1
    sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", P2.X, P2.Y), 1) # P2
    sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", P3.X, P3.Y), 2) # P3
    sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", P4.X, P4.Y), 3) # P4
    sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", P5.X, P5.Y), 4) # P5
    sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", P6.X, P6.Y), 5) # P6
    sketch_main.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", P7.X, P7.Y), 6) # P7
    
    # Constraints
    sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 0, 1), 0, 1) # P1-P2
    sketch_main.addConstraint(Sketcher.Constraint("Vertical", 1, 2), 1, 2) # P2-P3
    sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 2, 3), 2, 3) # P3-P4
    sketch_main.addConstraint(Sketcher.Constraint("Coincident", 3, 0, 4, 1), 3, 4) # P4 on line P3-P5? No, just points.
    sketch_main.addConstraint(Sketcher.Constraint("Coincident", 4, 0, 5, 1), 4, 5)
    sketch_main.addConstraint(Sketcher.Constraint("Coincident", 5, 0, 6, 1), 5, 6)
    sketch_main.addConstraint(Sketcher.Constraint("Coincident", 6, 0, 0, 1), 6, 0)
    
    # Close loop constraint
    sketch_main.addConstraint(Sketcher.Constraint("Radius", 0, 1), 0, 1) # Quarter circle? 
    # Actually, let's use a circle for the quarter round to be precise.
    # Replace P1-P2 line with a circle arc.
    # Remove the line segment P1-P2
    sketch_main.removeGeometry(0)
    sketch_main.addGeometry(Part.Circle(P1, App.Vector(0, 1, 0), params.corner_arc_radius.Value), False)
    
    doc.recompute()

    # Pad the main body
    # The body spans plate_thickness symmetrically. So we pad from 0 to -plate_thickness (length = plate_thickness) and then we need to mirror it?
    # Or pad to -plate_thickness/2 and then mirror the sketch?
    # "The body spans plate_thickness symmetrically about its axial mid-plane."
    # Let's pad to -plate_thickness/2 and then create a mirrored version.
    # But simpler: Pad to -plate_thickness (full length) if the sketch is just the half.
    # Let's assume the sketch is the cross section at X=0. We pad along -X direction.
    # Length = plate_thickness.
    
    pad_main = body.newObject("PartDesign::Pad", "PadMain")
    pad_main.Profile = sketch_main
    pad_main.Length = -params.plate_thickness.Value # Pad in -X direction
    pad_main.Type = "Solid"
    doc.recompute()

    # Mirror the body to create the other half (positive X)
    # We need to mirror the whole solid.
    # PartDesign doesn't have a direct "Mirror" feature that works on a Body in older versions, but in 1.1 it might.
    # Alternatively, we can create a sketch of the mirrored profile and pad.
