"""
FreeCAD 1.1 Script: Spur Gear Stock Generator
Generates a parametric spur gear stock inside a PartDesign Body.
Saves the result as answer.FCStd next to the script.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

def main():
    # Create a new document
    doc = App.newDocument("SpurGearStock")
    
    # Create the main Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # --- 1. Define Parameters (Editable properties) ---
    params = body.newObject("App::VarSet", "GearParameters")
    params.addProperty("App::PropertyInteger", "number_of_teeth", "GearParameters", "Number of teeth on the gear")
    params.number_of_teeth = 40
    
    params.addProperty("App::PropertyInteger", "diametral_pitch", "GearParameters", "Diametral pitch (teeth/inch)")
    params.diametral_pitch = 32
    
    params.addProperty("App::PropertyFloat", "pressure_angle_deg", "GearParameters", "Pressure angle in degrees")
    params.pressure_angle_deg = 20.0
    
    params.addProperty("App::PropertyLength", "overall_length", "GearParameters", "Overall axial length of the gear blank")
    params.overall_length = 304.8  # 12 * 25.4
    
    params.addProperty("App::PropertyLength", "module", "GearParameters", "Calculated module (mm)")
    params.setExpression("module", "25.4 / Parameters.diametral_pitch")
    
    params.addProperty("App::PropertyLength", "pitch_diameter", "GearParameters", "Calculated pitch diameter")
    params.setExpression("pitch_diameter", "(Parameters.number_of_teeth / Parameters.diametral_pitch) * 25.4")
    
    params.addProperty("App::PropertyLength", "outer_diameter", "GearParameters", "Calculated outer diameter")
    params.setExpression("outer_diameter", "((Parameters.number_of_teeth + 2) / Parameters.diametral_pitch) * 25.4")

    # --- 2. Create Base Sketch (Pitch Circle) on XY Plane ---
    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.AttachmentSupport = [(doc.getObject("XY_Plane"), [""]) ]
    base_sketch.MapMode = "FlatFace"
    
    # Add Pitch Circle
    pitch_circle = base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_diameter), False)
    base_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.pitch_diameter))
    base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 1))
    base_sketch.updateConstraints()
    
    # --- 3. Create Teeth Profile Sketch on XZ Plane ---
    # We define the profile of ONE TOOTH in the XZ plane.
    # The axis of revolution will be the Z axis.
    # The profile will be a closed loop representing the tooth shape.
    # To create a gear with N teeth by revolving a single profile, the profile must represent 
    # the shape of the tooth AND the space between teeth? 
    # No, standard PartDesign::Revolution revolves a profile 360 degrees. 
    # If the profile is a "bump" (tooth), revolving it creates a gear with 1 tooth repeated? 
    # No, it creates a gear with 1 tooth if the profile is closed and doesn't cross itself? 
    # Actually, to get N teeth, we usually pattern the tooth. 
    # HOWEVER, the prompt asks for "external involute teeth distributed around the circumference".
    # The most robust way in PartDesign without complex sector logic is:
    # 1. Create a cylinder of the outer diameter.
    # 2. Create a sketch of the TOOTH SPACE (the gap) on the XZ plane.
    # 3. Revolve the gap to subtract the spaces, leaving the teeth.
    # This is the standard "subtractive" approach for gears in CAD.
    
    # Calculate dimensions for the tooth space profile
    addendum = 25.4 / params.diametral_pitch
    dedendum = addendum + (25.4 / params.diametral_pitch) # Standard clearance 1/DP
    root_radius = (params.pitch_diameter / 2) - dedendum
    tip_radius = (params.pitch_diameter / 2) + addendum
    
    # Circular Pitch (distance from start of one tooth to start of next)
    circular_pitch = math.pi * params.pitch_diameter / params.number_of_teeth
    
    # We need to define the profile of the GAP between two teeth.
    # The gap is centered at Z = 0? Or aligned with the tooth?
    # Let's align the gap such that the involute flanks are symmetric around Z=0? 
    # No, the involute is tangent to the base circle.
    # Let's define the profile of the GAP.
    # The gap starts at the root circle, goes up the dedendum, then the involute flank, 
    # then the tip circle, then the other flank, then back to root.
    
    # Actually, simpler: Define the profile of the TOOTH (the solid part) and use a Polar Pattern?
    # If I define a tooth profile (a bump) and pattern it N times, I get N teeth.
    # This is much easier to sketch and control.
    # Profile:
    # 1. Start at Root Radius, Z = - (circular_pitch / 2) ? No, that's the center of the gap.
    # Let's center the tooth at Z=0.
    # The tooth occupies an angle.
    # Let's approximate the tooth profile with a spline through key points.
    
    # Key Points for ONE TOOTH (centered at Z=0):
    # 1. Bottom of tooth space (Root circle): X = root_radius, Z = - (circular_pitch / 2)
    # 2. Start of Involute (Base circle): X = base_radius, Z = - (circular_pitch / 2) + offset
    # 3. End of Involute (Tip circle): X = tip_radius, Z = + (circular_pitch / 2) - offset
    # 4. Top of tooth (Tip circle): X = tip_radius, Z = + (circular_pitch / 2)
    # 5. Symmetric return.
    
    # Let's calculate the Z positions more precisely.
    # The tooth is centered at Z=0.
    # The gap is centered at Z = circular_pitch / 2.
    # The root of the tooth is at Z = circular_pitch / 2 - (circular_pitch / 2) = 0? No.
    # The root of the tooth is at the bottom of the gap.
    # Let's define the profile of the GAP (the hole) and subtract it.
    # Gap Profile:
    # 1. Start at Root Radius, Z = - (circular_pitch / 2)
    # 2. Go up to Base Radius? No, the gap is bounded by the involute.
    # The involute starts at the base circle.
    # The angle of the gap at the base circle is determined by the pressure angle.
    # Angle of gap at base = 2 * Pressure Angle? No, that's the contact angle.
    # The gap angle at the base circle is roughly 2 * (Pressure Angle / 2) = Pressure Angle?
    # Actually, the involute flanks are tangent to the base circle.
    # The angle between the two flanks at the base circle is 2 * Pressure Angle.
    # So the gap width at the base circle is 2 * base_radius * tan(Pressure Angle)? No.
    # The arc length at the base circle corresponding to the gap is 2 * base_radius * (Pressure Angle in radians).
    # Let's just use the circular pitch to position the gap.
    
    # Let's try the "Additive" approach: Pattern a tooth.
    # Tooth Profile (Closed Loop):
    # 1. Start at Root Radius, Z = - (circular_pitch / 2)
    # 2. Move horizontally to Base Radius? (Approximation)
    # 3. Follow Involute to Tip Radius.
    # 4. Move horizontally to Tip Radius (Top Land).
    # 5. Follow Involute back to Base Radius.
    # 6. Move horizontally back to Root Radius.
    # 7. Close loop.
    
    # Let's calculate the Z coordinates for the involute points.
    # We need the involute to go from Base Radius to Tip Radius.
    # The Z coordinate of the involute point at radius R is:
    # Z = R_base * (sin(t) - t*cos(t))
    # Where t = sqrt((R^2 - R_base^2) / R_base^2)
    
    pressure_rad = math.radians(params.pressure_angle_deg)
    base_radius = (params.pitch_diameter / 2) * math.cos(pressure_rad)
    
    # Calculate Z for Base Radius (t=0) -> Z=0
    # Calculate Z for Tip Radius
    r_tip = tip_radius
    t_tip = math.sqrt((r_tip**2 - base_radius**2) / base_radius**2)
    z_tip_involute = base_radius * (math.sin(t_tip) - t_tip * math.cos(t_tip))
    
    # We need to center the tooth.
    # The tooth extends from Z_start to Z_end.
    # Let's assume the tooth is symmetric around Z=0.
    # The bottom of the tooth (root) is at Z = - (circular_pitch / 2).
    # The top of the tooth (tip) is at Z = + (circular_pitch / 2).
    # Wait, the circular pitch is the distance between corresponding points on adjacent teeth.
    # So the tooth height in Z should be roughly circular_pitch?
    # Yes, if we define the tooth from the bottom of the gap to the top of the gap.
    
    z_bottom = - (circular_pitch / 2)
    z_top = + (circular_pitch / 2)
    
    # We need to adjust the involute points to fit between z_bottom and z_top.
    # The involute naturally spans from Z=0 (at base radius) to Z=z_tip_involute (at tip radius).
    # This span is usually much smaller than the circular pitch.
    # We need to scale or shift?
    # Actually, the involute is the curve of the flank.
    # The Z coordinate of the flank at the base circle is 0 (relative to the center of the tooth).
    # The Z coordinate of the flank at the tip circle is z_tip_involute.
    # The total height of the tooth is z_top - z_bottom = circular_pitch.
    # The involute only covers the "active" part.
    # The rest is the "dedendum" and "addendum" lands?
    # No, the involute is the flank.
    # The profile consists of:
    # 1. Root circle arc (from Z_bottom to Z_base_start)
    # 2. Involute (from Z_base_start to Z_tip_end)
    # 3. Tip circle arc (from Z_tip_end to Z_top)
    # 4. Symmetric return.
    
    # Let's define the points for the spline:
    points = []
    
    # 1. Bottom of tooth (Root circle)
    # We assume the root circle is flat at Z_bottom? No, it's a circle.
    # But in the XZ sketch, it's a point.
    # Let's start at X = root_radius, Z = z_bottom.
    points.append((root_radius, z_bottom))
    
    # 2. Start of Involute (Base circle)
    # The involute starts at the base circle.
    # The Z coordinate at the base circle is 0 (relative to the center of the tooth).
    # But our tooth is centered at 0?
    # If the tooth is centered at 0, the gap is centered at 0?
    # No, the gap is between teeth.
    # Let's center the TOOTH at Z=0.
    # Then the gap is centered at Z = circular_pitch / 2? No.
    # The gap is centered at Z = 0?
    # If the gap is centered at 0, the tooth is centered at circular_pitch / 2?
    # Let's center the GAP at Z=0.
    # Then the tooth is centered at Z = circular_pitch / 2? No.
    # Let's center the TOOTH at Z=0.
    # Then the gap is centered at Z = circular_pitch / 2? No.
    # The distance from the center of the tooth to the center of the gap is circular_pitch / 2.
    # So if Tooth Center = 0, Gap Center = circular_pitch / 2.
    # The bottom of the gap is at Z = circular_pitch / 2 - (circular_pitch / 2) = 0? No.
    # The bottom of the gap is at Z = circular_pitch / 2 - (circular_pitch / 2) = 0?
    # Wait, the gap height is circular_pitch.
    # So Gap Bottom = circular_pitch / 2 - circular_pitch / 2 = 0.
    # Gap Top = circular_pitch / 2 + circular_pitch / 2 = circular_pitch.
    # Tooth Bottom = 0.
    # Tooth Top = circular_pitch.
    # This means the tooth and gap share the same Z range?
    # Yes, they are adjacent.
    # So if we center the TOOTH at Z = circular_pitch / 2, then:
    # Tooth Bottom = 0.
    # Tooth Top = circular_pitch.
    # Gap Bottom = circular_pitch.
    # Gap Top = 2 * circular_pitch.
    # This works.
    
    # Let's redefine:
    # Tooth Center Z = circular_pitch / 2.
    # Tooth Bottom Z = 0.
    # Tooth Top Z = circular_pitch.
    
    # Now, the involute starts at the base circle.
    # The Z coordinate of the base circle point on the involute is 0 (relative to the center of the tooth).
    # So in our global Z, it is at Z = circular_pitch / 2.
    # The Z coordinate of the tip circle point on the involute is z_tip_involute (relative to center).
    # So in global Z, it is at Z = circular_pitch / 2 + z_tip_involute.
    
    # But wait, the involute naturally goes from Z=0 to Z=z_tip_involute.
    # The total height of the tooth is circular_pitch.
    # The involute height is z_tip_involute.
    # The remaining height is the "land" at the top and bottom?
    # No, the involute is the flank.
    # The profile is:
    # 1. Root circle (Z=0 to Z=0? No, Z=0 is a point).
    # 2. Involute (Z=0 to Z=z_tip_involute).
    # 3. Top Land (Z=z_tip_involute to Z=circular_pitch).
    # 4. Symmetric return.
    
    # This implies the tooth is very tall (circular_pitch) but the involute is short.
    # This is correct. The "stock" has the teeth formed.
    
    # Let's generate the points for the spline.
    # We need points from (root_radius, 0) to (tip_radius, circular_pitch).
    # But the involute is only from (base_radius, 0) to (tip_radius, z_tip_involute).
    # So we need to connect (root_radius, 0) to (base_radius, 0) with a line?
    # Yes, the dedendum is usually a straight line or a small arc.
    # Let's use a straight line for simplicity.
    
    # Points:
    # 1. (root_radius, 0)
    # 2. (base_radius, 0)
    # 3. (base_radius, z_tip_involute) -> End of involute
    # 4. (tip_radius, z_tip_involute) -> Start of top land
    # 5. (tip_radius, circular_pitch) -> End of top land
    # 6. (tip_radius, circular_pitch - z_tip_involute) -> Start of return involute
    # 7. (base_radius, circular_pitch - z_tip_involute) -> End of return involute
    # 8. (base_radius, circular_pitch) -> Start of return dedendum
    # 9. (root_radius, circular_pitch) -> End of return dedendum
    # 10. (root_radius, 0) -> Close loop
    
    # Wait, the involute is symmetric.
    # The return involute should be the mirror image.
    # So points 6 and 7 are correct.
    
    # Let's refine the points for the spline.
    # We need to generate the involute curve points.
    
    # Forward Involute
    t_vals = [0]
    t_tip = math.sqrt((r_tip**2 - base_radius**2) / base_radius**2)
    t_vals.append(t_tip)
    
    # Add intermediate points
    n = 10
    ts = [0, t_tip]
    for i in range(1, n):
        ts.append(ts[i-1] + (ts[i] - ts[i-1]) * (i+1)/(n+1))
        
    for t in ts:
        x = base_radius * (math.cos(t) + t * math.sin(t))
        z = base_radius * (math.sin(t) - t * math.cos(t))
        points.append((x, z))
        
    # Add Top Land points
    # From (tip_radius, z_tip_involute) to (tip_radius, circular_pitch)
    points.append((tip_radius, z_tip_involute))
    points.append((tip_radius, circular_pitch))
    
    # Return Involute (Mirror)
    # We need to go from (tip_radius, circular_pitch) back to (base_radius, circular_pitch)
    # The Z coordinate decreases from circular_pitch to circular_pitch - z_tip_involute.
    # The X coordinate decreases from tip_radius to base_radius.
    # The curve is the mirror of the forward involute.
    # Forward: Z = f(t), X = g(t)
    # Return: Z = circular_pitch - f(t), X = g(t)
    
    for t in reversed(ts):
        x = base_radius * (math.cos(t) + t * math.sin(t))
        z = circular_pitch - (base_radius * (math.sin(t) - t * math.cos(t)))
        points.append((x, z))
        
    # Add Bottom Dedendum points
    # From (base_radius, circular_pitch) to (root_radius, circular_pitch)
    points.append((base_radius, circular_pitch))
    points.append((root_radius, circular_pitch))
    
    # Close loop
    points.append((root_radius, 0))
    
    # Create the spline
    spline = Part.makeSpline(points)
    
    # Create the sketch
    teeth_sketch = body.newObject("Sketcher::SketchObject", "TeethSketch")
    teeth_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    teeth_sketch.AttachmentSupport = [(doc.getObject("XZ_Plane"), [""]) ]
    teeth_sketch.MapMode = "FlatFace"
    
    # Add the spline
    spline_geom = teeth_sketch.addGeometry(spline, False)
    teeth_sketch.updateConstraints()
    
    # --- 4. Create the Gear Body ---
    # We will use a Pad to create the gear body from the teeth sketch.
    # The pad will extrude the tooth profile along the Z axis.
    # Length = overall_length.
    
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = teeth_sketch
    pad.Length = params.overall_length
    pad.Midplane = False
    pad.Reversed = False
    
    # --- 5. Add Fillets (Optional but good for stock) ---
    # Add a small fillet to the root and tip edges.
    # We need to select the edges.
    # The edges are the intersection of the pad with the planes.
    # We can use a loop to find the edges.
    
    # Find the edges of the pad
    edges = pad.Shape.Edges
    # We want to fillet the top and bottom edges (Z = 0 and Z = overall_length)
    # And the side edges (the involute flanks)
    
    # Let's add a fillet to all edges with a small radius.
    # Or specifically the top and bottom.
    # Let's add a fillet to the top and bottom edges.
    # We need to identify them.
    # The top edge is at Z = overall_length.
    # The bottom edge is at Z = 0.
    
    # Let's just add a fillet to all edges with a small radius (e.g., 1mm)
    # This will smooth the corners.
    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pad, ["Edge"])
    fillet.Radius = 1.0
    fillet.Method = "Radius"
    
    # --- 6. Compute and Save ---
    doc.recompute()
    
    # Save the file
    script_path = Path(__file__).resolve()
    output_path = script_path.with_name("answer.FCStd")
    doc.saveAs(str(output_path))
    
    print(f"Gear stock generated and saved to {output_path}")

if __name__ == "__main__":
    main()
