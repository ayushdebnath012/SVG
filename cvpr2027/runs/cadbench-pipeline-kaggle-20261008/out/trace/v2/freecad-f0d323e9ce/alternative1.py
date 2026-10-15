import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

def main():
    # --- 1. Create Document ---
    doc = App.newDocument("GearStock")
    doc.Label = "Spur Gear Stock"
    
    # --- 2. Define Parameters ---
    # Based on the prompt requirements:
    # pressure_angle = 20 deg
    # diametral_pitch = 12
    # number_of_teeth = 16
    # pitch_diameter = 33.8582 mm
    # outer_diameter = 38.1 mm
    # overall_length = 304.8 mm
    
    params = doc.addObject("App::Parameter", "Parameters")
    params.addProperty("App::PropertyFloat", "pressure_angle", "Dimensions", "20.0")
    params.addProperty("App::PropertyInteger", "diametral_pitch", "Dimensions", "12")
    params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "16")
    params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "33.8582")
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "38.1")
    params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "304.8")
    
    # Calculated derived parameters for geometry construction
    params.addProperty("App::PropertyFloat", "calculated_module", "Derived")
    params.addProperty("App::PropertyLength", "calculated_base_diameter", "Derived")
    params.addProperty("App::PropertyLength", "calculated_addendum", "Derived")
    params.addProperty("App::PropertyLength", "calculated_dedendum", "Derived")
    params.addProperty("App::PropertyLength", "calculated_root_diameter", "Derived")
    
    # Helper to set expressions
    def set_expr(obj, prop, ref):
        obj[prop] = ref

    # Set derived values
    set_expr(params, "calculated_module", f"25.4/{params.diametral_pitch}")
    set_expr(params, "calculated_base_diameter", f"{params.pitch_diameter} * cos(radians({params.pressure_angle}))")
    set_expr(params, "calculated_addendum", f"1/{params.diametral_pitch}") # in inches, then convert? 
    # Note: The prompt gives values in mm directly for some, inches for others. 
    # Let's rely on the explicit values given in the prompt for clarity and accuracy, 
    # but express them based on the base inputs to keep it parametric.
    # Addendum (inches) = 1/12. Convert to mm: (1/12) * 25.4
    set_expr(params, "calculated_addendum", f"(1/{params.diametral_pitch}) * 25.4")
    set_expr(params, "calculated_dedendum", f"(1.25/{params.diametral_pitch}) * 25.4")
    set_expr(params, "calculated_root_diameter", f"{params.pitch_diameter} - 2 * {params.calculated_dedendum}")
    
    doc.recompute()

    # --- 3. Create Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, -params.overall_length / 2.0)) # Center Y axis? No, usually center at base or middle. 
    # Let's center the gear stack at Y=0. So the plane is at Y=0, and the body extends to +/- length/2.
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # --- 4. Create Base Sketch (Cross Section) ---
    # We need a profile on the X-Y plane (Face Z).
    # Coordinate system: 
    # Y axis = Gear Axis (Rotation)
    # X axis = Radial direction
    # Z axis = Axial direction (Length of gear)
    
    sketch = body.newObject("Sketcher::SketchObject", "GearProfileSketch")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0)) # Origin
    sketch.Support = [(doc.getObject("XY_Plane"), [""])] # Face Z (X-Y plane)
    sketch.MapMode = "FlatFace"
    
    # We need to define the profile. 
    # Profile consists of:
    # 1. Outer Circle (Outer Diameter)
    # 2. Root Circle (Root Diameter)
    # 3. Involute Teeth between these circles.
    
    # Helper to add circle
    def add_circle(sk, center, radius, constr_type="Radius"):
        sk.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), float(radius)), False)
        return sk
    
    # Helper to add line segment
    def add_line(sk, p1, p2):
        sk.addGeometry(Part.LineSegment(p1, p2), False)
        return sk

    # 1. Add Root Circle
    root_circ = add_circle(sketch, App.Vector(0, 0, 0), params.calculated_root_diameter / 2.0)
    
    # 2. Add Outer Circle
    outer_circ = add_circle(sketch, App.Vector(0, 0, 0), params.outer_diameter / 2.0)
    
    # We need to generate an involute curve. 
    # Since FreeCAD Sketcher doesn't have a native involute constraint, we will approximate 
    # the tooth profile using a series of points calculated from the involute equation, 
    # connected by lines, or use a parametric curve if available (Sketcher::Curve).
    # However, for a robust "PartDesign" script, using an approximation with many points or 
    # the standard "Line" segments is safer and often accepted.
    # Let's calculate involute points.
    # Involute equation:
    # r = b * sqrt(1 + theta^2)
    # x = b * (cos(theta) + theta * sin(theta))
    # y = b * (sin(theta) - theta * cos(theta))
    # where b is base radius, theta is the unwrapped angle (radians).
    
    base_r = float(params.calculated_base_diameter) / 2.0
    outer_r = float(params.outer_diameter) / 2.0
    
    # Calculate number of points needed for smoothness
    num_points = 200 # High resolution for the teeth
    
    points = []
    
    # Generate involute for the full 180 degrees (or slightly more to cover the tip)
    # We need to cover the angular width of the teeth.
    # Pitch circle angle per tooth = 360 / N
    # Addendum angle: cos^-1(base_r / outer_r)
    # Dedendum angle: cos^-1(base_r / root_r)
    
    addendum_angle = math.acos(base_r / outer_r)
    dedendum_angle = math.acos(base_r / base_r) # Should be 0, root is base for involute start. 
    # Wait, root is smaller than base? 
    # Prompt: root_diameter = 28.56... mm, base_diameter = 31.81... mm.
    # So root < base. Involute cannot go inside base circle. 
    # Therefore, the root is a circular arc, and the involute starts at the base circle and goes OUTWARDS.
    # The profile is: 
    # - Inner arc (root)
    # - Involute from base to outer
    # - Outer arc
    # - Repeat for teeth.
    
    # Let's define the start and end angles for the involute on one side of the tooth.
    # The tooth is symmetric around the radial line.
    # Pressure angle 20 deg.
    # Half pitch angle = 180 / N = 180 / 16 = 11.25 deg.
    # Tooth thickness at pitch circle = 180/N.
    # Contact ratio considerations... simplified:
    # We need to draw the involute from the base circle up to the outer circle.
    # The involute starts at theta=0 (at base circle radius).
    # It ends when radius = outer_r.
    # max_theta = sqrt((outer_r/base_r)^2 - 1)
    
    max_theta = math.sqrt((outer_r/base_r)**2 - 1)
    
    # We need to construct the profile for half a tooth (from the valley to the peak) and mirror it?
    # No, the sketch is 2D. The gear body is revolved (extruded) along the Y axis?
    # Wait, the prompt says "cylindrical gear body... defined about a central axis".
    # Usually, gears are extruded along the axis of rotation.
    # If the axis of rotation is Y, the sketch should be in X-Z plane (Face Y).
    # Let's re-orient the sketch to be on the X-Z plane (Face Y).
    # X = Radial, Z = Axial (Length).
    # The teeth are in the X-Z plane? NO.
    # The teeth are in the X-Y plane (Cross section). The body is extruded along Z.
    # Correct orientation:
    # Axis of rotation: Z (Standard for gears in CAD usually).
    # Sketch Plane: X-Y (Face Z).
    # Extrusion: Along Z axis.
    
    # Let's switch the sketch plane to XY_Plane (Face Z).
    # X = Radial, Y = Tangential.
    
    # Re-evaluating Sketch Placement:
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.Support = [(doc.getObject("XY_Plane"), [""])]
    sketch.MapMode = "FlatFace"
    
    # Generate points for the Involute profile from Base Circle to Outer Circle.
    # We need to span the angle of the tooth.
    # Let's generate a full involute curve from theta = -max_theta to max_theta, but we only need 
    # the part corresponding to the tooth space and tooth top.
    # Actually, simpler approach:
    # 1. Draw Root Circle.
    # 2. Draw Outer Circle.
    # 3. Draw Involute lines connecting them.
    # To do this, we generate points on the involute and connect them.
    
    # Calculate the angular span of the tooth at the base circle?
    # The involute starts at the base circle.
    # The tooth is defined by the involute.
    # We need to create a profile that goes:
    # Root Circle -> Involute (to Base Circle) -> Involute (to Outer Circle) -> Outer Circle.
    # But the involute is continuous. We need to select the segments.
    
    # Let's calculate the angle corresponding to the root circle (which is inside base, so no involute there).
    # The involute starts at the base circle.
    # The profile must connect the Root Circle to the Base Circle via a tangent?
    # No, standard gear design: The tooth flanks are involutes starting from the base circle.
    # The root is a circular arc. The transition from root to involute is usually a fillet or a sharp corner (if no undercut).
    # For this script, we will draw the involute starting from the base circle and ending at the outer circle.
    # Then we connect the root circle to the start of the involute? 
    # Actually, the root is smaller than the base. The involute exists ONLY outside the base circle.
    # So the profile is:
    # - Arc at Root Diameter (internal arc of the tooth space).
    # - Arc at Outer Diameter (external arc of the tooth top).
    # - Two Involute curves connecting these.
    # The involute curves start at the Base Circle.
    # So we have a gap between Root and Base? No, the material exists there.
    # The profile of the TOOTH (the material) is the outer boundary.
    # The boundary consists of:
    # - Outer Arc (Radius = Outer_R)
    # - Involute (from Outer_R down to Base_R)
    # - ... wait, the tooth is bounded by the involute on both sides.
    # - Root Arc (Radius = Root_R) at the bottom.
    # - Involute (from Base_R up to Outer_R) on the sides.
    # How do we connect Root to Involute?
    # The involute starts at Base_R. The Root is smaller.
    # So the profile goes from Root_R (at some angle) to Base_R (at theta=0) along the involute?
    # No, the involute is defined for r >= Base_R.
    # So the profile of the tooth is:
    # Start at Root Circle (r = Root_R).
    # Go up the tooth flank. The flank is an involute.
    # The involute starts at r = Base_R.
    # So the profile is NOT purely involute from root to tip.
    # It is: Root Arc -> (Fillet/Sharp corner) -> Involute -> Outer Arc.
    # BUT, standard AGMA full depth gear: The root is a circle. The involute starts at the base circle.
    # There is a region between Root and Base where the tooth is circular (the dedendum circle).
    # So the profile is:
    # 1. Root Circle (Arc).
    # 2. Transition to Base Circle? (Usually a fillet, but for "exact" geometry we might just connect them or use a very small fillet).
    # 3. Involute from Base to Outer.
    # 4. Outer Circle (Arc).
    
    # Let's construct the profile for HALF a tooth (symmetric about the center line) and then mirror?
    # Or just draw the full profile of one tooth space?
    # It's easier to draw the profile of ONE tooth (the solid part) and pattern it.
    # Tooth Profile:
    # - Starts at Root Circle (Angle = -half_tooth_angle_at_root)
    # - Goes up to Base Circle (Angle = -half_tooth_angle_at_base) -> This part is a radial line? No.
    # - From Base Circle to Outer Circle: Involute.
    # - From Outer Circle (Angle = +half_tooth_angle_at_outer) to Root Circle (Angle = +half_tooth_angle_at_root): Involute.
    # - Root Circle arc.
    
    # Simplified approach for scripting:
    # Generate involute points from theta = -max_theta to max_theta.
    # These points lie on the involute curve starting from base circle (theta=0).
    # We need to clip these points to the specific angles of the tooth.
    
    # Tooth Angle calculation:
    # Pitch Angle (half) = 180 / N = 11.25 deg.
    # At the pitch circle, the tooth width is 2 * (180/N) = 22.5 deg? No, 180/N is the angle subtended by the tooth space (or tooth).
    # Angle per tooth = 360/N. Half angle = 180/N.
    # At the pitch circle, the tooth is symmetric.
    # We need to find the angle of the tooth at the Base Circle and Outer Circle.
    # The involute angle theta is related to the radius r by: r = b * sqrt(1+theta^2).
    # The polar angle of the involute point is: phi = theta + atan(theta).
    # The angle of the tooth relative to the centerline is phi.
    # We need the tooth to be centered at 0.
    # So the tooth occupies [-phi_outer, +phi_outer] at the outer circle?
    # No, the tooth is the space between two involutes.
    # Let's define the profile of the TOOTH (solid):
    # Left flank: Involute from Base to Outer.
    # Right flank: Involute from Base to Outer.
    # Top: Outer Circle arc.
    # Bottom: Root Circle arc.
    # We need to determine the start/end angles for the involutes.
    # The centerline of the tooth is at Angle 0.
    # The right flank involute starts at some angle phi_start_right and ends at phi_end_right.
    # The left flank involute starts at phi_start_left and ends at phi_end_left.
    # Due to symmetry: phi_end_right = -phi_end_left.
    # At the Outer Circle (r=Outer_R), theta = max_theta.
    # phi_outer = max_theta + atan(max_theta).
    # The tooth extends from -phi_outer to +phi_outer?
    # No, the tooth is the space between the flanks.
    # If we draw the profile of the TOOTH, we need the points on the flanks.
    # The flank is the involute curve.
    # The tooth is bounded by the involute on the left and the involute on the right.
    # Wait, the involute curve wraps around.
    # The profile of the TOOTH is:
    # - Arc on Root Circle.
    # - Involute curve (Right Flank) going from Root to Outer.
    # - Arc on Outer Circle.
    # - Involute curve (Left Flank) going from Outer to Root.
    
    # How to get the start angle of the involute at the Root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # 1. Root Circle Arc (from angle -alpha_root to alpha_root).
    # 2. Vertical line? No.
    # 3. Fillet from Root to Base?
    # Standard practice in CAD: The involute starts at the base circle. The dedendum circle is smaller.
    # The region between Base and Root is just the dedendum circle.
    # So the profile is:
    # -
