"""
FreeCAD 1.1 Parametric Spur Gear Generator
Generates a spur gear with hub and bore using PartDesign features.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# --- Configuration ---
# Derive output paths from __file__
script_dir = Path(__file__).resolve().parent
output_path = script_dir / "answer.FCStd"

# Gear Parameters (ISO 21771 / Standard Spur Gear)
PARAMS = {
    "pressure_angle_deg": 20.0,
    "gear_module": 1.0,
    "number_of_teeth": 22,
    "face_width": 10.0,
    "hub_diameter": 18.0,
    "hub_width": 10.0,
    "shaft_diameter": 8.0,
    "overall_width": 20.0,
    
    # Calculated Dimensions
    "addendum": 1.0,              # m
    "dedendum": 1.25 * 1.0,       # m
    "root_diameter": 22.0 - 2 * 1.25, # m
    "circular_pitch": math.pi * 1.0, # m
    "base_diameter": 22.0 * math.cos(math.radians(20.0)), # m
    "pitch_diameter": 22.0,       # m
    "outer_diameter": 24.0,       # m
    "bore_diameter": 8.0,         # m
}

def create_spur_gear():
    # 1. Create Document
    doc = App.newDocument("SpurGear")
    
    # 2. Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # 3. Define Parameters (Named Variables)
    # We will add a VarSet to store our named parameters so they are editable in the tree
    param_set = body.newObject("App::VarSet", "Parameters")
    
    # Add properties to VarSet
    prop_names = [
        "pressure_angle_deg", "gear_module", "number_of_teeth", "face_width",
        "hub_diameter", "hub_width", "shaft_diameter", "overall_width",
        "addendum", "dedendum", "root_diameter", "circular_pitch",
        "base_diameter", "pitch_diameter", "outer_diameter", "bore_diameter"
    ]
    
    for name in prop_names:
        param_set.addProperty("App::PropertyLength", name, "Parameters", "Gear Dimension")
        param_set.setPropertyLabel(name, name.replace('_', ' ').title())
        param_set[name] = PARAMS[name]
    
    # 4. Create Base Sketch (Pitch Circle / Reference)
    # We need a sketch on XY plane to define the tooth profile and hub dimensions.
    sketch_ref = body.newObject("Sketcher::SketchObject", "Sketch_RefProfile")
    sketch_ref.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_ref.PlacementIn = sketch_ref.PlacementOf = App.Placement(App.Vector(0, 0, 0))
    sketch_ref.Supports = (doc.getObject("XY_Plane"),)
    sketch_ref.MapMode = "FlatFace"
    sketch_ref.ConstrainToCurrent = False
    
    # Create a circle representing the Pitch Diameter
    # This serves as the reference for tooth generation
    pitch_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["pitch_diameter"])
    sketch_ref.addGeometry(pitch_circle, False)
    
    # Add reference lines for construction
    center_point = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, 0, 1))
    sketch_ref.addGeometry(center_point, True)
    
    doc.recompute()
    
    # 5. Generate Tooth Profile Sketch (Top Face of Gear)
    # We will create a sketch on the top face (Z = face_width / 2)
    # To do this cleanly in PartDesign without external geometry manipulation:
    # We create a sketch on a temporary plane offset from XY, then move it to the body context.
    # However, standard practice is to sketch on the body's top face directly.
    # Since we haven't extruded anything yet, we can't sketch on the face.
    # Strategy: Extrude the Hub first, then sketch on the top face for teeth.
    
    # 5a. Create Hub Cylinder (Base for Teeth)
    # Sketch for Hub
    sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub")
    sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_hub.Supports = (doc.getObject("XY_Plane"),)
    sketch_hub.MapMode = "FlatFace"
    
    hub_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["hub_diameter"] / 2)
    sketch_hub.addGeometry(hub_circle, False)
    
    doc.recompute()
    
    # 5b. Create Hub Pad
    pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub")
    pad_hub.Profile = sketch_hub
    pad_hub.Length = PARAMS["hub_width"]
    pad_hub.Type = "FullyRestricted"
    doc.recompute()
    
    # 5c. Create Tooth Profile Sketch
    # Place on top face of Hub
    sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
    sketch_teeth.Placement = App.Placement(App.Vector(0, 0, PARAMS["hub_width"] / 2))
    sketch_teeth.Supports = (body.getObject("Pad_Hub"), ["Top"])
    sketch_teeth.MapMode = "FlatFace"
    
    # Construct the tooth profile on the Pitch Circle
    # We need to draw the involute/addendum/root profile.
    # Since drawing an involute is complex in pure lines, we will approximate with splines or 
    # use a standard "Involute" constraint if available, or construct via points.
    # Given FreeCAD constraints, we will construct a polygon approximating the tooth space 
    # and then use a pattern. 
    # Better approach for robust scripting: Draw the space between teeth using lines/circles 
    # and constrain them to the pitch circle and base circle.
    
    # Let's create the profile for ONE TOOTH SPACE and pattern it.
    # Coordinates calculation for one tooth space (starting at angle 0, going to 360/N)
    theta_step = 360.0 / PARAMS["number_of_teeth"]
    
    # Define key points on the profile relative to the pitch circle radius
    # We will draw a simplified tooth profile consisting of:
    # 1. Arc on Pitch Circle (Tip)
    # 2. Arc on Base Circle (Root/Flank start)
    # Actually, for a scriptable, robust gear, we often use the "Gear" workbench. 
    # But the prompt requires manual PartDesign features.
    # We will construct the profile of the gear blank minus the teeth (or teeth minus blank).
    # Let's construct the Tooth Profile (Outer boundary of the gear tooth).
    
    # Helper to calculate involute angle
    def get_involute_point(t):
        """
        Calculate point on involute of circle with radius R_base, at tangential angle t.
        t is the angle of the tangent point on the base circle.
        """
        R_base = PARAMS["base_diameter"] / 2
        # Involute function: 
        # x = R_base * (cos(t) + t*sin(t))
        # y = R_base * (sin(t) - t*cos(t))
        # where t is in radians.
        # The angle of the radius vector is t + atan(t)
        x = R_base * (math.cos(t) + t * math.sin(t))
        y = R_base * (math.sin(t) - t * math.cos(t))
        return App.Vector(x, y, 0)

    # Define the profile points for one tooth
    # We will define the profile of the tooth itself.
    # Start from the root, go up the flank, across the tip, down the other flank.
    
    # 1. Root Point (Start of flank)
    # Root circle radius
    R_root = PARAMS["root_diameter"] / 2
    
    # 2. Tip Point (End of tip)
    R_tip = PARAMS["outer_diameter"] / 2
    
    # Pressure angle alpha = 20 deg
    # At the pitch circle, the tangent is at 20 deg to the line of action.
    # The line of action is tangent to the base circle.
    
    # Let's construct the profile of a single tooth centered at angle 0.
    # The tooth spans from -theta_step/2 to +theta_step/2.
    # The space between teeth spans the rest.
    
    # Simplified Tooth Profile Construction:
    # We will create a sketch that defines the cross section of ONE TOOTH.
    # Then we will use a Linear Pattern or Revolution to place them?
    # No, standard gears use Polar Pattern of the TOOTH.
    # So we sketch ONE TOOTH, then Polar Pattern it.
    
    # Tooth Geometry:
    # Start at bottom of flank (Root circle), go along base circle involute to Pitch circle,
    # then along Pitch circle to tip? No.
    # Standard: Involute from Base to Pitch, then Addendum (straight line perpendicular to line of action?)
    # For simplicity and robustness in script:
    # We will define the profile using a chain of constrained curves.
    
    # Point A: Root circle intersection (approx)
    # Point B: Pitch circle intersection
    # Point C: Tip circle intersection
    
    # Let's define the profile of the tooth space (to cut out the tooth) or the tooth itself.
    # Easier: Sketch the Tooth, then Pad it? No, gear teeth are usually formed by the body.
    # We will sketch the Tooth Profile and then use a Polar Pattern to place them, 
    # then subtract from a solid cylinder? 
    # Or: Create a solid cylinder (blank), then Pattern the Tooth Space (Pocket)?
    # Patterning a pocket is cleaner.
    
    # Let's construct the Profile of the TOOTH SPACE (the void).
    # The void is bounded by two flanks and the root circle arc.
    
    # We need to generate points for the flank.
    # Flank is an involute.
    # Angle of involute at pitch circle:
    # Pressure angle at pitch = 20 deg.
    # The involute starts at Base Circle.
    # Angle on base circle (t) where it hits Pitch Circle:
    # R_pitch = R_base / cos(alpha) -> cos(alpha) = R_base / R_pitch
    # t_pitch = alpha (in radians) ? No.
    # The angle of the tangent point on base circle (t) is such that the radius vector is at t + atan(t).
    # The angle of the radius vector at pitch circle is alpha.
    # So t + atan(t) = alpha.
    
    alpha_rad = math.radians(PARAMS["pressure_angle_deg"])
    # Solve t + atan(t) = alpha_rad
    # Since alpha is small, t approx alpha - alpha^3/3 ... 
    # Let's iterate for accuracy.
    t = 0.0
    for _ in range(10):
        prev = t
        t = alpha_rad - math.atan(t)
    
    # Now we can define points on the flank.
    # We need the point at the Pitch Circle (P) and Root Circle (R).
    
    # Point at Pitch Circle (P):
    # Radius vector angle = alpha_rad
    # Tangent point angle on base circle = t
    # Point P is on the line of action? No, P is on the pitch circle.
    # The flank passes through P.
    # Coordinate of P (relative to center, rotated to be at 0 for symmetry):
    # We want the tooth centered at 0.
    # The flank at P has a slope of -tan(alpha).
    
    # Let's define the profile of ONE HALF of a tooth (symmetric).
    # From Pitch Circle (P) down to Root Circle (R) along the flank.
    # Then along Root Circle arc to the opposite flank.
    # Then up the other flank.
    # Then Tip Circle arc.
    
    # Actually, constructing the exact involute in Sketcher is hard with primitives.
    # Alternative: Use a spline with constraints.
    # We will define 3 points: Root, Pitch, Tip.
    # And constrain the spline to be an involute? No constraint for that in FreeCAD Sketcher.
    # However, we can approximate the flank with a line segment from Pitch to Root if the module is small, 
    # but for accuracy, we must use the involute.
    
    # Hack: Use the "Gear" workbench logic but manually? No.
    # Let's use the "Involute" constraint? Not standard.
    # Let's use the property that the distance from the base circle tangent point to the current point 
    # is R_base * t.
    
    # Let's construct the profile using a spline and force it to pass through calculated points.
    # We will define the profile of the TOOTH.
    # We will generate a spline that goes through:
    # 1. Root (Root Circle, Angle -theta_step/2) -> No, Root is the bottom of the tooth.
    # The tooth is bounded by Root Circle at the bottom.
    # So the profile starts at Root Circle, goes up the flank, across the tip, down the other flank.
    
    # Let's calculate the intersection of the flank (involute) with the Root Circle.
    # This is mathematically complex to solve for 't' where radius is R_root.
    # sqrt(x^2+y^2) = R_root.
    # R_base^2 * ( (cos t + t sin t)^2 + (sin t - t cos t)^2 ) = R_root^2
    # R_base^2 * (1 + t^2) = R_root^2
    # 1 + t^2 = (R_root / R_base)^2
    # t_root = sqrt( (R_root/R_base)^2 - 1 )
    
    R_base = PARAMS["base_diameter"] / 2
    R_root = PARAMS["root_diameter"] / 2
    
    # Check validity: Root circle must be >= Base circle.
    if R_root < R_base:
        # This would be an undercut gear. Assume standard non-undercut.
        # If undercut, the root is determined by the involute cut.
        # But our params: 22 teeth, m=1. No undercut.
        pass
        
    t_root_val = math.sqrt((R_root / R_base)**2 - 1)
    t_pitch_val = t # calculated earlier (approx alpha for small alpha, but let's be precise)
    # Re-calc t_pitch precisely: t + atan(t) = alpha
    t_pitch_val = 0.0
    for _ in range(10):
        t_pitch_val = alpha_rad - math.atan(t_pitch_val)
        
    # Now we have the parameter t for the involute at Pitch and Root.
    # We can generate points along the flank.
    
    # Profile Points for ONE HALF TOOTH (Right side):
    # 1. Root Point (Bottom of tooth):
    # Angle of radius vector at root: theta_root = t_root_val (since t is the angle of the tangent, 
    # and the radius vector angle is t + atan(t) = alpha at pitch, but at root it's different).
    # Wait, the relationship is: The radius vector angle phi = t + atan(t).
    # So at t_root_val, phi_root = t_root_val + atan(t_root_val).
    # At t_pitch_val, phi_pitch = t_pitch_val + atan(t_pitch_val) = alpha_rad.
    
    # We want the tooth centered at 0.
    # So the left flank is at phi_root - theta_step/2 ... phi_root + theta_step/2?
    # No, the tooth space is between flanks.
    # The tooth is centered at 0.
    # The flank on the right (from root to tip) corresponds to angles increasing from the root angle?
    # Let's define the Tooth Profile explicitly.
    # It consists of:
    # - Left Flank (from Root to Tip)
    # - Tip (Arc)
    # - Right Flank (from Tip to Root)
    # - Root (Arc connecting the two root points)
    
    # We need the coordinates of the start of the flank (Root) and end of flank (Tip).
    # Start of Right Flank (at Pitch Circle):
    # Angle = alpha_rad (relative to the tangent point logic, but we want absolute angle).
    # If the tooth is centered at 0, the pitch point is at 0? No, the pitch point is at the center of the pitch.
    # The tangent to the base circle is at angle alpha_rad relative to the line of centers.
    # If the tooth is symmetric around 0, the pitch point is at 0.
    # Then the tangent point on base circle is at angle -alpha_rad?
    # Let's set up the coordinate system:
    # Tooth Center at (0,0).
    # Pitch Point at (R_pitch, 0).
    # The Line of Action is tangent to Base Circle and passes through Pitch Point.
    # The angle of the Line of Action with the horizontal (radius to Pitch Point) is -alpha_rad (downwards).
    # The tangent point on Base Circle is at angle -alpha_rad (polar)? No.
    # The tangent point T_base is such that angle(T_base, O, P)
