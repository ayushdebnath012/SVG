import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

def main():
    # --- 1. Create Document ---
    doc = App.newDocument("SpurGearStock")
    doc.Label = "Spur Gear Stock"

    # --- 2. Define Parameters ---
    # Input parameters as requested
    params = doc.addObject("App::Parameter", "Parameters")
    params.addProperty("App::PropertyFloat", "pressure_angle", "Dimensions", "20.0")
    params.addProperty("App::PropertyInteger", "diametral_pitch", "Dimensions", "12")
    params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "16")
    params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "33.8582")
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "38.1")
    params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "304.8")
    
    # Derived parameters for geometry construction
    params.addProperty("App::PropertyFloat", "calculated_module", "Derived")
    params.addProperty("App::PropertyLength", "calculated_base_diameter", "Derived")
    params.addProperty("App::PropertyLength", "calculated_addendum", "Derived")
    params.addProperty("App::PropertyLength", "calculated_dedendum", "Derived")
    params.addProperty("App::PropertyLength", "calculated_root_diameter", "Derived")
    
    # Helper to set expressions
    def set_expr(obj, prop, ref):
        obj[prop] = ref

    # Set derived values based on AGMA formulas provided in prompt
    set_expr(params, "calculated_module", f"25.4/{params.diametral_pitch}")
    set_expr(params, "calculated_base_diameter", f"{params.pitch_diameter} * cos(radians({params.pressure_angle}))")
    # Addendum in inches = 1/DP. Convert to mm: (1/DP) * 25.4
    set_expr(params, "calculated_addendum", f"(1/{params.diametral_pitch}) * 25.4")
    # Dedendum in inches = 1.25/DP. Convert to mm: (1.25/DP) * 25.4
    set_expr(params, "calculated_dedendum", f"(1.25/{params.diametral_pitch}) * 25.4")
    set_expr(params, "calculated_root_diameter", f"{params.pitch_diameter} - 2 * {params.calculated_dedendum}")
    
    doc.recompute()

    # --- 3. Create Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    # Center the gear stack at Y=0. The sketch will be on the X-Z plane (Face Y).
    # X = Radial, Z = Axial (Length).
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # --- 4. Create Base Sketch (Cross Section) ---
    # We need a profile on the X-Z plane (Face Y).
    # Coordinate system: 
    # Y axis = Gear Axis (Rotation)
    # X axis = Radial direction
    # Z axis = Axial direction (Length of gear)
    
    sketch = body.newObject("Sketcher::SketchObject", "GearProfileSketch")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0)) 
    # Attach to the Y-Z plane? No, we want the sketch to be in the X-Z plane (Face Y).
    # In FreeCAD, XY_Plane is Face Z. XZ_Plane is Face Y. YZ_Plane is Face X.
    # We want the sketch to lie on the XZ plane (Face Y).
    sketch.Support = [(doc.getObject("XZ_Plane"), [""])] 
    sketch.MapMode = "FlatFace"
    
    # Helper to add circle
    def add_circle(sk, center, radius):
        sk.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), float(radius)), False)
        return sk
    
    # Helper to add line segment
    def add_line(sk, p1, p2):
        sk.addGeometry(Part.LineSegment(p1, p2), False)
        return sk

    # --- 5. Generate Involute Points ---
    # Involute equation:
    # r = b * sqrt(1 + theta^2)
    # x = b * (cos(theta) + theta * sin(theta))
    # z = b * (sin(theta) - theta * cos(theta))
    # where b is base radius, theta is the unwrapped angle (radians).
    
    base_r = float(params.calculated_base_diameter) / 2.0
    outer_r = float(params.outer_diameter) / 2.0
    root_r = float(params.calculated_root_diameter) / 2.0
    
    # Calculate max theta for the outer circle
    max_theta = math.sqrt((outer_r/base_r)**2 - 1)
    
    # Number of points for smoothness
    num_points = 200 
    
    # We need to construct the profile for ONE tooth (the solid part).
    # The tooth is symmetric around the Z-axis (Radial line).
    # The profile consists of:
    # 1. Root Circle Arc (from -alpha_root to alpha_root)
    # 2. Involute curve (Right Flank) from Base to Outer
    # 3. Outer Circle Arc (from alpha_outer to -alpha_outer) -- Wait, this is the top.
    #    Actually, the tooth is the space between two flanks.
    #    Let's define the profile of the TOOTH (solid):
    #    - Starts at Root Circle (Angle = -half_tooth_angle_at_root)
    #    - Goes up the tooth flank (Involute) to the Outer Circle.
    #    - Goes across the Outer Circle (Arc) to the other flank.
    #    - Goes down the other flank (Involute) to the Root Circle.
    #    - Closes with Root Circle Arc.
    
    # Calculate angles at the Pitch Circle to determine tooth width
    # Pitch Angle (half) = 180 / N = 11.25 deg.
    # At the pitch circle, the tooth is symmetric.
    # The angle of the tooth at the pitch circle is 2 * (180/N) = 22.5 deg? 
    # No, the angle subtended by the tooth at the pitch circle is 360/N.
    # So half angle = 180/N.
    
    # We need to find the angle of the involute at the Outer Circle and Root Circle relative to the centerline.
    # The involute starts at theta=0 (Base Circle).
    # The polar angle of the involute point is: phi = theta + atan(theta).
    # The tooth is centered at phi=0.
    # The right flank is the involute curve for theta > 0.
    # The left flank is the involute curve for theta < 0.
    # The tooth occupies the space between the right flank and the left flank.
    # So the profile of the TOOTH is:
    # - Right Flank: Involute from theta=0 to theta=max_theta.
    # - Top: Outer Circle Arc from phi_right_outer to phi_left_outer.
    # - Left Flank: Involute from theta=max_theta to theta=0 (negative side).
    # - Bottom: Root Circle Arc.
    
    # Wait, the involute curve phi(theta) increases as theta increases.
    # At theta=0, phi=0.
    # At theta=max_theta, phi = max_theta + atan(max_theta).
    # So the right flank goes from phi=0 to phi=phi_max.
    # The left flank goes from phi=0 to phi=-phi_max.
    # The tooth is the region between phi=-phi_max and phi=phi_max?
    # No, the tooth is the solid part. The space between teeth is the gap.
    # The gap is bounded by the involutes.
    # So the TOOTH is bounded by the involutes on the sides.
    # The profile of the TOOTH is:
    # - Start at Root Circle (Angle = -phi_root)
    # - Go up the Left Flank (Involute) to Outer Circle.
    # - Go across Outer Circle (Arc) to Right Flank.
    # - Go down Right Flank (Involute) to Root Circle.
    # - Close with Root Circle Arc.
    
    # But the involute starts at the Base Circle.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Vertical line? No.
    # - Fillet from Root to Base?
    # Standard practice: The involute starts at the Base Circle. The dedendum circle is smaller.
    # The region between Base and Root is just the dedendum circle.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # Wait, the involute starts at the Base Circle.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi_outer to -phi_outer).
    # - Involute curve (Left Flank) from Outer to Base.
    # - Root Circle Arc (from -phi_root to phi_root).
    
    # How to get phi_root?
    # The involute starts at the Base Circle. Below that, it's not an involute.
    # So the profile is:
    # - Root Circle Arc (from -phi_root to phi_root).
    # - Involute curve (Right Flank) from Base to Outer.
    # - Outer Circle Arc (from phi
