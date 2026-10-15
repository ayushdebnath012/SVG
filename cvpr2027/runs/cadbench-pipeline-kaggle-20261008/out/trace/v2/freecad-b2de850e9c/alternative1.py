from pathlib import Path
import FreeCAD as App
import Part
import PartDesign
import Sketcher
import math

def create_spur_gear_script():
    """
    Creates a parametric spur gear using PartDesign features.
    Saves the result as an FCStd file next to this script.
    """
    
    # Derive output path from __file__
    script_path = Path(__file__).resolve()
    output_path = script_path.with_name(script_path.stem + ".FCStd")
    
    # Create Document
    doc = App.newDocument("SpurGear")
    App.activeDocument() = doc
    
    # --- Parameters Block ---
    # Create a VarSet to hold all parameters for easy editing
    params = doc.addObject("App::VarSet", "GearParameters")
    
    # Gear Geometry Parameters
    params.addProperty("App::PropertyInteger", "number_of_teeth", "GearParameters", "Number of teeth")
    params.number_of_teeth = 50
    
    params.addProperty("App::PropertyLength", "gear_module", "GearParameters", "Module (m)")
    params.gear_module = 1.500
    
    params.addProperty("App::PropertyAngle", "pressure_angle", "GearParameters", "Pressure angle (deg)")
    params.pressure_angle = 20.0
    
    # Hub Parameters
    params.addProperty("App::PropertyLength", "hub_diameter", "GearParameters", "Hub diameter")
    params.hub_diameter = 45.0
    
    params.addProperty("App::PropertyLength", "hub_width", "GearParameters", "Hub width")
    params.hub_width = 10.0
    
    params.addProperty("App::PropertyLength", "overall_width", "GearParameters", "Overall face width")
    params.overall_width = 25.0
    
    # Bore Parameters
    params.addProperty("App::PropertyLength", "shaft_diameter", "GearParameters", "Shaft diameter")
    params.shaft_diameter = 10.0
    
    # Derived Parameters (Calculated based on Module & Teeth)
    # Addendum = m
    # Dedendum = 1.25 * m
    # Whole Depth = Addendum + Dedendum
    # Pitch Diameter = m * z
    # Outer Diameter = Pitch Diameter + 2*Addendum
    # Root Diameter = Pitch Diameter - 2*Dedendum
    
    params.addProperty("App::PropertyLength", "addendum", "GearParameters", "Addendum (calculated)")
    params.addExpression = "gear_module"
    
    params.addProperty("App::PropertyLength", "dedendum", "GearParameters", "Dedendum (calculated)")
    params.addExpression = "1.25 * gear_module"
    
    params.addProperty("App::PropertyLength", "whole_depth", "GearParameters", "Whole depth (calculated)")
    params.addExpression = "addendum + dedendum"
    
    params.addProperty("App::PropertyLength", "pitch_diameter", "GearParameters", "Pitch diameter (calculated)")
    params.addExpression = "gear_module * number_of_teeth"
    
    params.addProperty("App::PropertyLength", "outer_diameter", "GearParameters", "Outer diameter (calculated)")
    params.addExpression = "pitch_diameter + (2 * addendum)"
    
    params.addProperty("App::PropertyLength", "root_diameter", "GearParameters", "Root diameter (calculated)")
    params.addExpression = "pitch_diameter - (2 * dedendum)"

    doc.recompute()
    
    # --- Body Creation ---
    body = doc.addObject("PartDesign::Body", "Body")
    doc.recompute()
    
    # --- Feature Construction ---
    
    # 1. Create Sketch for Gear Teeth (Outer Profile)
    # We will use the "XY_Plane" (Z axis normal) for the gear face sketch
    sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
    sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_teeth.ConstrainAll = True
    sketch_teeth.MapMode = "FlatFace"
    
    # Define the profile geometry using trigonometry for gear teeth
    # Base circle radius = pitch_diameter / 2
    # Addendum circle radius = outer_diameter / 2
    # We need to construct the tooth profile. 
    # A simple approximation for a spur gear tooth profile involves:
    # - A fillet at the root
    # - A pressure angle flank
    # - A top land
    
    # Let's define the profile points relative to the center of the gear face.
    # We will create a polyline/curve that goes around the gear.
    # To make it a closed loop for the body, we need to close it.
    
    # Strategy: Create a sketch on the XY plane (Z=0).
    # The gear body will be a Pad from this sketch.
    
    # We need to generate the tooth profile. 
    # Since we can't easily use complex curves in a simple script without external libraries 
    # or very complex Python curve definitions, we will construct the profile using 
    # a series of lines and arcs, or simply use the standard "Gear" shape if available, 
    # but the prompt asks for a script construction.
    # 
    # Alternative: Use the "Part::Reversed" or "Part::Revolution" approach combined with a sketch.
    # However, the prompt requires PartDesign features.
    # 
    # Let's create the profile by defining a function to generate points and then 
    # approximating with lines/arcs or using a specific curve type if supported.
    # FreeCAD Part supports BezierCurves, BSplines, etc.
    
    # Let's build the profile by creating a sketch on the XY plane.
    # The profile will be a closed shape.
    
    # Helper to create a Bezier curve from points
    def create_gear_profile(points, close=True):
        """Creates a Part::BezierCurve from a list of (x,y) points."""
        pts = [(p.x, p.y, 0.0) for p in points]
        # Add closure if requested
        if close:
            pts.append(pts[0])
        # Create a B-Spline curve (smooth approximation)
        curve = Part.BSplineCurve()
        curve.Poles = pts
        # Create a solid from the curve? No, we need a shape for the sketch.
        # We can use the curve to generate a face, but Sketcher needs a shape.
        # Actually, Sketcher::SketchObject can take a Part::Shape.
        # But we need to generate the 2D profile.
        
        # Let's try a simpler approach: Create the geometry in the sketch directly 
        # using Part commands and constraints, or use a pre-built shape if possible.
        # Given the constraints of a script, generating the exact involute is hard.
        # We will approximate the tooth shape using a simplified symmetric profile:
        # - Root radius
        # - Flank lines at pressure angle
        # - Top land
        
        # Let's define the key radii
        r_pitch = params.pitch_diameter.Value / 2.0
        r_outer = params.outer_diameter.Value / 2.0
        r_root = params.root_diameter.Value / 2.0
        
        # We will construct a closed path.
        # Start at angle 0, go around.
        # To keep it simple and robust, we will create a single closed curve 
        # that represents the gear outline with teeth.
        
        # Since creating a perfect involute in pure Python script for Sketcher 
        # without a loop in the script itself (which is allowed) is tedious,
        # we will generate a list of points that approximates the gear shape 
        # and fit a BSpline.
        
        num_segments = 360 # Resolution
        points = []
        # Center
        cx, cy = 0.0, 0.0
        
        # We need to generate the profile.
        # Let's define the tooth geometry.
        # Angle between teeth
        theta_tooth = 2 * math.pi / params.number_of_teeth
        
        # We'll generate points for half a tooth and mirror it? 
        # No, let's just generate the full perimeter.
        
        # Simplified approximation:
        # 1. Root circle arc
        # 2. Flank lines
        # 3. Top land arc
        
        # Let's create a list of vertices for the entire gear.
        # This will be a bit verbose but accurate enough for the task.
        
        current_angle = 0.0
        # Base of tooth (start of flank)
        # For a standard gear, the flank starts at a specific angle relative to the tooth center.
        # Let's assume the flank starts at the root radius and goes to the pitch circle? 
        # Or from root to addendum?
        # Standard approximation: Flank from root to addendum at pressure angle.
        
        # Let's create a simplified "trapezoidal" tooth profile with fillets for simplicity 
        # while maintaining the exact dimensions.
        # This creates a gear that meshes reasonably well for simulation but is not mathematically perfect involute.
        # However, for a "PartDescription" task, an accurate approximation is expected.
        
        # Let's generate points for the entire gear perimeter.
        # We will iterate 360 degrees.
        
        # Define the profile logic:
        # If we are at the center of a tooth:
        #   Go up to outer radius.
        #   Go down to root radius at pressure angle.
        # Else (between teeth):
        #   Go along the flank? No, usually just the root and top land.
        
        # Actually, the easiest way to define a gear in a script for PartDesign is to 
        # create a sketch that contains the profile.
        # We will use Part to create the shape directly and attach it to the sketch?
        # No, the sketch must be constructed.
        
        # Let's try to generate the points for a closed spline.
        # We'll define the profile by iterating angles.
        
        # Let's define the tooth center angles.
        tooth_angles = [i * theta_tooth for i in range(params.number_of_teeth)]
        
        # We need a function to get the (x,y) at a given angle phi.
        def get_point(phi):
            # Find the tooth this angle belongs to
            # tooth center index
            idx = int((phi / theta_tooth) % params.number_of_teeth)
            
            # Angle relative to tooth center
            rel_angle = phi - tooth_angles[idx]
            
            # Determine profile based on rel_angle
            # -90 to 90 is the tooth half-width
            # -90: Flank start (root)
            # 0: Tooth tip
            # 90: Flank end (root)
            
            # Adjust for the fact that tooth center is at 0 deg relative.
            # Let's map the standard gear geometry.
            # Root circle radius: r_root
            # Pitch circle radius: r_pitch
            # Addendum circle radius: r_outer
            
            # The flank lines are at the pressure angle relative to the radial line? 
            # No, pressure angle is relative to the tangent of the pitch circle.
            # The flank line is a straight line passing through the base circle?
            # For a simplified script, we often use the pressure angle from the pitch circle.
            # Line equation: r = R_pitch / cos(alpha) ... no.
            
            # Let's use the simplified straight flank from root to addendum at pressure angle.
            # This is an approximation but visually correct for many purposes.
            
            # Angle of the flank relative to the tooth center line?
            # If the tooth center is at 0, the flank goes outwards.
            # The angle of the flank line is (90 - pressure_angle) from the radial?
            # Or simply: The line makes an angle of (pressure_angle) with the tangent.
            
            # Let's define the profile piecewise:
            # 1. Top Land: Arc at r_outer between two angles.
            # 2. Flank: Line from (r_outer, angle_start) to (r_root, angle_end).
            # 3. Root: Arc at r_root.
            
            # Approximate Tooth Width at Pitch Circle:
            # Circular Pitch p = pi * m
            # Tooth width at pitch circle approx = p / 2
            # Angle width = (p / 2) / r_pitch = (pi * m / 2) / (m * z) = pi / (2 * z)
            # Wait, tooth thickness = space width = p/2.
            # Angle = (p/2) / r_pitch = (pi * m / 2) / (m * z) = pi / (2 * z).
            
            # So the tooth spans an angle of `pi / z` centered at the tooth center.
            # Half angle = pi / (2 * z).
            
            half_tooth_angle = math.pi / (2 * params.number_of_teeth)
            
            # Check if we are in the "tooth" region or "space" region
            # The tooth exists between -half_tooth_angle and +half_tooth_angle relative to center.
            
            if abs(rel_angle) <= half_tooth_angle:
                # We are on a tooth
                # Calculate the angle where the tooth meets the root.
                # In a standard gear, the root angle is slightly less than the tooth angle.
                # Let's approximate the root start angle as slightly outside the pitch angle.
                # Let's assume the flank goes from r_root to r_outer.
                # Angle of the root corner relative to center:
                # We can calculate the angle at the root for the flank.
                # But let's simplify: 
                # The tooth exists from angle_start to angle_end.
                # Let's define the root corners.
                
                # Simplified: The tooth is a trapezoid rotated.
                # Top width at r_outer. Bottom width at r_root.
                
                # Let's find the intersection of the flank line with r_root and r_outer.
                # The flank line is tangent to the base circle? 
                # Base radius = r_pitch * cos(alpha)
                r_base = r_pitch * math.cos(math.radians(params.pressure_angle))
                
                # Flank line starts at r_base? No, usually drawn from root.
                # Let's draw from root.
                # Angle of the flank at the root:
                # We can approximate the root angle of the tooth as the angle where the circle r_root intersects the flank.
                # But we need the flank definition.
                
                # Let's use a standard approximation for the root angle:
                # Root angle = (Pitch Angle) - (Space Angle adjustment)
                # Actually, let's just define the profile by points.
                
                # Point 1: Start of root arc (just before tooth)
                # Point 2: Root corner
                # Point 3: Root corner (other side)
                # Point 4: Top corner (other side)
                # Point 5: Top corner (this side)
                # Point 6: End of root arc (just after tooth)
                
                # Let's calculate the angles for the corners.
                # Flank line: y = tan(90 - alpha) * x ? No.
                # In polar: r * cos(theta - theta_center) ... 
                
                # Let's use a known formula for the angle of the root corner.
                # theta_root = arcsin(r_base / r_root) ?? No.
                
                # Let's approximate:
                # The tooth exists from theta = -theta_tooth/2 to +theta_tooth/2.
                # The root circle arc is from -theta_root_limit to +theta_root_limit.
                # The top land is from -theta_top_limit to +theta_top_limit.
                
                # Let's define the profile by generating points on the boundary.
                # We will iterate from -180 to 180.
                pass
            
            else:
                # We are in the space (between teeth)
                # Profile is the root circle.
                return (r_root * math.cos(phi), r_root * math.sin(phi))
                
            # Inside the tooth:
            # We need to decide if we are on the flank or the top land.
            # Top land is at r_outer.
            # Flank is at r_root to r_outer.
            
            # Let's calculate the angle of the root corner.
            # Angle of the base circle intersection with the flank?
            # The flank is a line from (r_root, theta_root) to (r_outer, theta_outer).
            # The angle of the line is constant relative to the radial? No.
            
            # Let's use the property that the flank is tangent to the base circle.
            # But for simplicity, let's assume the root corner angle is such that the flank 
            # connects r_root and r_outer.
            
            # Approximation: 
            # The root corner angle is roughly the angle where the circle r_root intersects 
            # the line that is tangent to r_base at angle (theta_center - 90 + alpha)?
            
            # Let's try a different approach: 
            # Generate points for the entire gear by checking if the point is inside the gear.
            # But we need a curve.
            
            # Let's go back to the "simplified trapezoid" idea.
            # We define the root corner angle `alpha_root` and top corner angle `alpha_top`.
            # `alpha_top` is the angle where the flank meets the top land.
            # `alpha_root` is the angle where the flank meets the root land.
            
            # The flank line equation in polar coordinates (relative to tooth center):
            # r * cos(theta - theta_ref) = constant? No.
            # It's a straight line in Cartesian.
            # Line: X * sin(alpha) - Y * cos(alpha) = 0? (Passing through origin) -> No.
            # Line: Y = X * tan(90 - alpha) -> X * cos(alpha) + Y * sin(alpha) = 0?
            
            # Let's define the flank line in the local coordinate
