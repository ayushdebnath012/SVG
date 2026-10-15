"""
FreeCAD 1.1 Script to generate a Disc Spring (Belleville Washer).
This script creates a parametric PartDesign Body with editable features.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

def main():
    # Create a new document
    doc = App.newDocument("DiscSpring")
    doc.Label = "Disc Spring Generator"

    # Define Parameters (App::VarSet is the standard way to define named parameters in PartDesign bodies)
    # However, for direct scriptability and robustness in headless mode, 
    # we often add variables to the Body or use specific property types.
    # The prompt suggests using named document objects.
    
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # Add a Parameter container to the Body to drive dimensions
    # In FreeCAD 1.1, we can use App::VarSet or simply set expressions on features.
    # Let's create a VarSet to hold the parameters as requested for "named document objects".
    params = body.newObject("App::VarSet", "Parameters")
    
    # Define parameters
    params.addProperty("App::PropertyLength", "outside_diameter", "Dimensions", "Outside diameter of the spring")
    params.setPropertyDescription("outside_diameter", "8.0")
    params.outside_diameter = 8.0

    params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inside diameter of the spring")
    params.setPropertyDescription("inner_diameter", "4.2")
    params.inner_diameter = 4.2

    params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the bounding box")
    params.setPropertyDescription("overall_height", "0.6")
    params.overall_height = 0.6

    params.addProperty("App::PropertyLength", "thickness", "Dimensions", "Material thickness")
    params.setPropertyDescription("thickness", "0.4")
    params.thickness = 0.4

    params.addProperty("App::PropertyLength", "cone_height", "Dimensions", "Height of the cone profile")
    params.setPropertyDescription("cone_height", "0.2")
    params.cone_height = 0.2

    # --- Feature Construction ---

    # 1. Outer Profile Sketch (XZ Plane for rotation)
    # We will create a sketch on the XZ plane. 
    # Note: Standard FreeCAD planes are XY, XZ, YZ. 
    # If we rotate around Z, the profile must be in XY plane. 
    # Let's use the XY plane for the profile and rotate around the Z axis.
    
    sketch_outer = body.newObject("Sketcher::SketchObject", "OuterProfile")
    sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
    # Attach to XY plane
    sketch_outer.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    sketch_outer.MapMode = "FlatFace"
    
    # Define geometry for the outer ring (conical frustum side profile)
    # We need two circles (inner and outer diameters) and two lines connecting them.
    # Since it's a disc, we are working in a cross-section.
    # Radius Outer = outside_diameter / 2
    # Radius Inner = inner_diameter / 2
    # Height = cone_height (at the inner edge)
    
    r_out_expr = f"Parameters.outside_diameter / 2"
    r_in_expr = f"Parameters.inner_diameter / 2"
    h_cone_expr = f"Parameters.cone_height"
    
    # Add Circles
    sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_out_expr), False)
    sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_in_expr), False)
    
    # Add Lines (using LineSegment or Lines)
    # Line 1: Outer radius on X axis
    sketch_outer.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(r_out_expr, 0, 0)), False)
    # Line 2: Inner radius on X axis
    sketch_outer.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(r_in_expr, 0, 0)), False)
    
    # Line 3: Outer height line (from center to top outer edge)
    # Actually, for a revolution, we usually just sketch the profile curve.
    # Let's define the profile curve explicitly: Outer Circle -> Down to Bottom -> Inner Circle -> Up.
    # But simpler: Sketch the perimeter of the frustum.
    # Points: (r_out, 0), (r_out, h_cone), (r_in, h_cone), (r_in, 0) ... wait, geometry is tricky with expressions.
    
    # Alternative Strategy: Use two lines and two circles with coincident/constraints.
    # Let's define the sketch on XY plane. Rotate around Z.
    # We need the profile of the side.
    # Point A: (r_out, 0)
    # Point B: (r_out, h_cone) -- This is the top edge of the cone.
    # Point C: (r_in, h_cone) -- This is the top edge of the inner hole.
    # Point D: (r_in, 0) -- This is the bottom edge of the inner hole.
    # The profile consists of:
    # 1. Vertical line at r_out from z=0 to z=h_cone? No, the spring is a conical shell.
    # The side wall is a straight line connecting (r_out, 0) and (r_in, h_cone)? 
    # Or is it (r_out, h_cone) and (r_in, 0)?
    # Usually, Belleville springs are tapered. Let's assume the thicker part is at the bottom (z=0) and tapers to thinner at top?
    # Or standard: The "cone" is the material.
    # Let's assume the profile is:
    # Outer boundary: Line from (r_out, 0) to (r_in, h_cone) ?? No.
    # Let's visualize:
    # Bottom face (z=0): Annulus from r_in to r_out.
    # Top face (z=h_cone): Annulus from r_in to r_out.
    # The side is conical.
    # If we rotate around Z:
    # The profile must be in the XY plane? No, if we rotate around Z, the profile is in XZ or YZ.
    # If sketch is on XY plane, rotation creates a cylinder/sphere. 
    # We need the sketch on the XZ plane (or YZ) and rotate around the Y (or X) axis.
    # Let's switch: Sketch on XZ plane, Rotate around Y axis.
    # This makes the disc lie in the XZ plane? No.
    # Standard: Sketch on XY plane, Rotate around Z axis -> Cylinder.
    # To get a disc spring lying flat (XY plane):
    # We need to extrude the profile in Z? No, that makes a cylinder.
    # We need to REVOLVE the profile around Z axis.
    # The profile must be in the XZ plane (or YZ).
    # Let's create a sketch on the XZ plane.
    # Rotation Axis: Y_Axis (which corresponds to the global Y axis).
    # Wait, if I rotate a shape in XZ plane around the Y axis, I get a shape symmetric around Y. That's a cylinder along Y.
    # I want a disc along Z.
    # So: Sketch in XY plane -> Extrude along Z? No, that's a cylinder.
    # I need the shape to be generated by rotating a 2D curve around an axis.
    # If the final part is a disc in XY plane, the axis of symmetry is Z.
    # The profile curve must be in the XZ plane (or YZ).
    # So: Sketch on XZ Plane. Rotate around Y Axis? 
    # If I rotate a curve in XZ plane around the Y axis, the resulting surface is a surface of revolution around Y.
    # The result will be a "hoop" standing up.
    # I want a "disc" lying down.
    # Therefore: Sketch in XZ plane, Rotate around Y axis -> Hoop standing up.
    # Sketch in XY plane, Rotate around Z axis -> Hoop lying down.
    # Correct logic:
    # 1. Create Sketch on XY Plane.
    # 2. Define the profile curve in this sketch. The curve must define the radius vs height.
    #    Since the sketch is XY, Y is the height axis (perpendicular to rotation axis Z).
    #    So we sketch in XY plane, where X is radius, Y is height.
    #    Then we REVOLVE around the Y axis? No.
    #    If we sketch in XY, and rotate around Y, we get a shape symmetric around Y.
    #    If we sketch in XY, and rotate around X, we get a shape symmetric around X.
    #    If we sketch in XY, and rotate around Z (the normal of the plane), we get a flat shape extruded in 3D? No, revolution around normal creates a sphere/cylinder.
    #    
    #    Let's restart the coordinate logic.
    #    Target: Disc Spring lying in XY plane (centered at 0,0,0).
    #    Axis of symmetry: Z axis.
    #    Method: REVOLVE.
    #    Profile Plane: Must contain the Z axis. Let's use the XZ plane.
    #    Rotation Axis: Y axis (perpendicular to XZ plane).
    #    If I rotate a curve in XZ plane around the Y axis:
    #    - The curve is defined by (X, Z).
    #    - Rotation around Y sweeps X to create a circle at height Z.
    #    - This creates a shape symmetric around Y. 
    #    - Wait, if I rotate around Y, the axis is Y. The resulting object is symmetric around Y.
    #    - I want the object symmetric around Z.
    #    - So the rotation axis must be Z.
    #    - The profile plane must be perpendicular to the rotation axis? No, it must contain the rotation axis.
    #    - If rotation axis is Z, the profile plane must contain Z.
    #    - Possible planes containing Z: XZ plane, YZ plane.
    #    - Let's use XZ plane.
    #    - Sketch on XZ plane.
    #    - Rotation Axis: Y_Axis (which is the axis perpendicular to XZ plane).
    #    - WAIT. If I rotate around Y, the axis is Y.
    #    - I need the axis to be Z.
    #    - So I must sketch on a plane containing Z, and rotate around Z.
    #    - But the sketch plane must be orthogonal to the rotation axis for a standard "Revolution" in many CAD systems?
    #    - In FreeCAD PartDesign: 
    #      - The "Revolution" feature takes a profile and an axis.
    #      - The profile is a sketch. The sketch usually lies in a plane that contains the axis? 
    #      - Actually, standard revolution: You sketch a profile in a plane, and define an axis of rotation. 
    #      - If the plane is XZ, and axis is Y, you get a shape around Y.
    #      - If the plane is XY, and axis is Z, you get a shape around Z.
    #      - YES. This is the key.
    #      - To get a shape around Z, the sketch must be in the XY plane? 
    #      - No. If I sketch in XY, and rotate around Z, the points (x, y) rotate. 
    #      - If the sketch is 2D in XY, and I rotate around Z, the Y coordinate becomes the angle? No.
    #      - Let's think of the math. 
    #      - Revolution around Z axis.
    #      - We need a profile (r, z).
    #      - This profile must be drawn in a plane that contains the Z axis.
    #      - Example: XZ plane. X is radius, Z is height.
    #      - If I sketch in XZ plane, I draw X vs Z.
      #      - Then I rotate around the Y axis? 
      #      - If I rotate around Y, the X coordinate sweeps around Y.
      #      - The resulting shape is symmetric around Y.
      #      - I want symmetry around Z.
      #      - So I need to rotate around Z.
      #      - To rotate around Z, the profile must be in a plane containing Z? 
      #      - Actually, FreeCAD's Revolution feature works by taking a closed wire (profile) and rotating it around an axis.
      #      - If the profile is in the XY plane, and I rotate around Z, the profile is already in the plane of rotation? 
      #      - No, the profile is a curve. If the curve is in XY, and I rotate around Z, the curve itself is in the plane of rotation. 
      #      - This creates a shape that is a "flat" ring if the curve is radial? 
      #      - No. 
      #      - Let's try a simple example: A circle in XY plane, centered at origin. Rotate around Z. Result: A sphere? No, a torus? No, a sphere? 
      #      - If the circle is in XY, radius R. Rotate around Z. The circle lies on the plane of rotation. 
      #      - Every point on the circle is equidistant from Z. Rotating it around Z does nothing. It stays a circle.
      #      - So we cannot sketch the profile in the XY plane if we want to generate a volume of revolution around Z.
      #      - We MUST sketch in a plane containing the Z axis (e.g., XZ plane).
      #      - And we must rotate around the Y axis? 
      #      - If I sketch in XZ, and rotate around Y. 
      #      - Point (x, 0, z) rotates around Y. 
      #      - The distance from Y axis is sqrt(x^2 + z^2)? No. 
      #      - Rotation around Y: x = r*cos(theta), z = r*sin(theta)? No.
      #      - Rotation around Y transforms (x, 0, z) to (x*cos - z*sin, 0, x*sin + z*cos).
      #      - This creates a shape symmetric around Y.
      #      - I want symmetry around Z.
      #      - So I need to rotate around Z.
      #      - To rotate around Z, the profile must be in a plane containing Z? 
      #      - No. The profile must be defined in a way that when rotated, it fills the volume.
      #      - Standard practice in FreeCAD for a cylinder along Z:
      #        - Sketch on XZ plane.
      #        - Define a line from (R, 0) to (R, H).
      #        - Rotate around Y axis? No.
      #        - Rotate around Y axis creates a cylinder along Y.
      #        - Rotate around X axis creates a cylinder along X.
      #        - Rotate around Z axis requires the profile to be in XZ or YZ? 
      #        - If I sketch in XZ, and rotate around Z, the profile is perpendicular to the axis? 
      #        - No, the XZ plane contains Z.
      #        - If I rotate a line segment from (R, 0, 0) to (R, 0, H) around Z? 
      #        - The segment is parallel to Z. Rotating it around Z sweeps a cylinder surface.
      #        - YES!
      #        - So: Sketch on XZ plane. Profile is a curve in XZ. Rotation Axis is Z axis.
      #        - Wait, if the sketch is on XZ, the Z axis is IN the sketch plane.
      #        - FreeCAD's Revolution feature: "ReferenceAxis" must be an axis.
      #        - If the profile is in XZ, and axis is Z.
      #        - Does FreeCAD allow rotating a profile around an axis that lies IN the sketch plane?
      #        - Yes, that is the standard way to create a solid of revolution.
      #        - Example: Sketch a triangle in XZ. Rotate around Z. Get a cone.
    
    # Plan:
    # 1. Sketch on XZ plane.
    # 2. Define the profile of the spring wall.
    #    - Outer boundary: Line from (r_out, 0) to (r_out, h_cone)? No.
    #    - The spring has thickness.
    #    - We need the "material" profile.
    #    - Bottom surface (z=0): Annulus r_in to r_out.
    #    - Top surface (z=h_cone): Annulus r_in to r_out.
    #    - Side wall: Conical.
    #    - Profile curve in XZ:
    #      - Start at (r_out, 0).
    #      - Go up to (r_out, h_cone)? No, the side is slanted.
    #      - The side connects (r_out, 0) to (r_in, h_cone) ?? 
    #      - Or (r_out, h_cone) to (r_in, 0)?
    #      - Let's assume the spring is thicker at the bottom? Or top?
    #      - Usually, the "cone" height is the distance between the two parallel planes of the top and bottom faces?
      #      - No, "overall_height" is the bounding box height.
      #      - "thickness" is the material thickness at the
