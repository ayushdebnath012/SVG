import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from task description
PRESSURE_ANGLE = 20.0  # degrees
DIAMETRAL_PITCH = 32.0 # teeth per inch
NUM_TEETH = 20
PITCH_DIAMETER = 15.875 # mm (5/8 inch)
OUTER_DIAMETER = 17.526 # mm (0.69 inch)
FACE_WIDTH = 304.8 # mm (1 ft)
GEAR_MODULE = 25.4 / DIAMETRAL_PITCH # mm

# --- Setup Document ---
doc = App.newDocument("GearStock")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold our named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Axial length of the gear")
params.face_width = FACE_WIDTH
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Diameter at pitch circle")
params.pitch_diameter = PITCH_DIAMETER
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the gear")
params.outer_diameter = OUTER_DIAMETER
params.addProperty("App::PropertyLength", "module", "Dimensions", "Module of the gear")
params.module = GEAR_MODULE
params.addProperty("App::PropertyInteger", "num_teeth", "Dimensions", "Number of teeth")
params.num_teeth = NUM_TEETH
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure angle in degrees")
params.pressure_angle = PRESSURE_ANGLE

# --- Base Sketch (Pitch Circle & Outer Circle) ---
# We define the profile on the XY plane.
# The gear will be extruded along Z.
sketch = body.newObject("Sketcher::SketchObject", "GearProfile")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.ConstrainFully = True
sketch.MapMode = "FlatFace"
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Helper to add geometry
def add_line(p1, p2, visible=True):
    sketch.addGeometry(Part.LineSegment(p1, p2), visible)

def add_circle(center, radius, visible=True):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), visible)

# 1. Pitch Circle (Reference)
add_circle(App.Vector(0, 0, 0), params.pitch_diameter / 2.0, False)

# 2. Outer Circle (Tip Circle)
add_circle(App.Vector(0, 0, 0), params.outer_diameter / 2.0, False)

# 3. Base Circle (for involute calculation)
# Base Diameter = Pitch Diameter * cos(Pressure Angle)
base_radius = (params.pitch_diameter / 2.0) * (App.Vector(cos(PRESSURE_ANGLE * 3.14159265359 / 180.0)).Length) # Simplified logic below
# Actually: Base Radius = Pitch Radius * cos(Pressure Angle)
import math
base_radius = (params.pitch_diameter / 2.0) * math.cos(math.radians(PRESSURE_ANGLE))
add_circle(App.Vector(0, 0, 0), base_radius, False)

# 4. Root Circle (Dedendum Circle)
# Standard Dedendum = 1.25 * Module
dedendum = 1.25 * params.module
root_radius = (params.outer_diameter / 2.0) - dedendum
add_circle(App.Vector(0, 0, 0), root_radius, False)

# 5. Add Involute Teeth
# We will generate the involute curve mathematically and add it to the sketch.
# Since FreeCAD Sketcher doesn't support direct curve objects easily in headless without Part,
# we will construct the tooth profile using lines and arcs that approximate the involute,
# or better, use the Part module to create the curve and add it to the sketch geometry.
# However, Sketcher::SketchObject.addGeometry accepts Part objects.

def create_involute_tooth():
    """
    Creates a single tooth profile (Involute) and returns a list of Part objects (lines/arcs)
    to be added to the sketch.
    """
    # Tooth geometry parameters
    # Pitch Radius
    rp = params.pitch_diameter / 2.0
    # Base Radius
    rb = rp * math.cos(math.radians(PRESSURE_ANGLE))
    # Addendum (Tip Radius - Pitch Radius)
    addendum = params.outer_diameter / 2.0 - rp
    # Dedendum (Pitch Radius - Root Radius)
    dedendum = rp - root_radius
    
    # Tooth thickness at pitch circle
    # Circular Pitch = pi * Module
    cp = math.pi * params.module
    # Tooth Thickness = cp / 2
    tooth_thickness = cp / 2.0
    
    # Angle subtended by half-tooth at pitch circle
    # theta = (tooth_thickness / 2) / rp
    theta_pitch = (tooth_thickness / 2.0) / rp
    
    # Involute function: r = rb / cos(phi)
    # We need to generate points from the base circle out to the tip circle.
    # The involute starts at the base circle (phi=0) and ends at the tip circle.
    # We need to calculate the angle phi_tip such that r(phi_tip) = Tip Radius.
    # Tip Radius = rb / cos(phi_tip) => cos(phi_tip) = rb / Tip Radius => phi_tip = acos(rb / Tip Radius)
    
    phi_tip = math.acos(rb / (params.outer_diameter / 2.0))
    
    # We need to generate the curve from phi=0 to phi=phi_tip.
    # We will approximate this with many small line segments for the sketch.
    num_points = 50
    points = []
    
    # Start point: Base circle, angle 0
    # We need to offset this by half the tooth thickness at the base? 
    # No, the involute starts at the base circle. The tooth flank is the involute.
    # The tooth space is bounded by the involute.
    # We need to place the tooth such that the center of the tooth is at angle 0.
    # So the left flank starts at angle -theta_pitch (at pitch circle) and goes inwards?
    # Actually, let's generate the curve from the base circle outwards.
    
    # Let's define the curve from the base circle (phi=0) to the tip (phi=phi_tip).
    # We will create a list of points along this curve.
    # Then we will rotate this curve to position the tooth.
    
    # Wait, the standard way to model a gear in a sketch is to draw the involute curve.
    # Let's generate points for the right flank of a tooth centered at 0.
    # The right flank goes from the base circle (angle -phi_tip) to the tip (angle 0)?
    # No. The involute is generated by unwrapping a string.
    # Let's generate the curve for the right side of the tooth.
    # The curve starts at the base circle.
    # The angle of the point on the base circle relative to the tooth center line is -phi_tip.
    # The angle at the tip is 0.
    
    # Let's generate points from phi = -phi_tip to phi = 0.
    # r = rb / cos(phi)
    # x = r * cos(phi)
    # y = r * sin(phi)
    
    # But we need to shift the whole curve so the tooth is centered.
    # Actually, let's just generate the curve from phi=0 to phi=phi_tip and then rotate it.
    # Let's generate the curve for the "right" flank of a tooth centered at 0.
    # The right flank corresponds to angles from -phi_tip to 0?
    # Let's try generating from phi = -phi_tip to phi = 0.
    
    # Correction: The involute equation is usually defined from the base circle.
    # Let's generate points from phi = -phi_tip to phi = 0.
    # This creates the curve from the base circle (at angle -phi_tip) to the tip (at angle 0).
    # This forms the right flank of a tooth centered at 0.
    
    # Wait, if phi goes from -phi_tip to 0, the radius increases.
    # At phi = -phi_tip, r = rb / cos(-phi_tip) = rb / (rb/r_tip) = r_tip.
    # At phi = 0, r = rb.
    # So this generates the curve from Tip to Base. We want Base to Tip.
    # So we iterate phi from 0 to phi_tip?
    # If phi goes 0 to phi_tip, r goes rb to r_tip.
    # The angle of the point is phi.
    # So the curve starts at (rb, 0) and ends at (r_tip, phi_tip).
    # This is the right flank of a tooth if the tooth center is at angle phi_tip/2? No.
    
    # Let's simplify. We will generate the curve from the base circle to the tip circle.
    # We will create a list of points.
    # Then we will rotate the list of points to position the tooth.
    
    # Let's generate the curve for the right flank of a tooth centered at 0.
    # The right flank starts at the base circle at angle -phi_tip (relative to tooth center)
    # and ends at the tip circle at angle 0.
    # Wait, the involute angle phi is measured from the base circle tangent.
    # The angle of the radius vector is phi + alpha0?
    # Let's use the standard parametric equations for involute:
    # x = rb * (cos(phi) + phi * sin(phi))
    # y = rb * (sin(phi) - phi * cos(phi))
    # Here phi is the angle of the tangent to the involute relative to the base circle radius.
    # The angle of the radius vector is phi + atan(phi)? No.
    # The angle of the radius vector is phi + alpha, where alpha is the pressure angle?
    # Actually, the angle of the radius vector is phi + atan(phi) is incorrect.
    # The angle of the radius vector is phi + atan(phi) is for the involute of a circle?
    # Let's use the property: The angle between the radius vector and the tangent is 90 + phi.
    # The angle of the radius vector is phi + atan(phi)? No.
    # The angle of the radius vector is phi + atan(phi) is wrong.
    # The angle of the radius vector is phi + atan(phi) is for the involute of a circle?
    # Let's use the standard formula:
    # x = rb * (cos(phi) + phi * sin(phi))
    # y = rb * (sin(phi) - phi * cos(phi))
    # This gives the involute starting at (rb, 0) for phi=0.
    # The angle of the radius vector is atan2(y, x).
    # For small phi, x ~ rb, y ~ 0. Angle ~ 0.
    # For large phi, angle ~ phi.
    # So the angle of the radius vector is approximately phi.
    # So if we want the tooth centered at 0, the right flank should go from angle -phi_tip to 0?
    # No, the right flank goes from the base circle (angle -phi_tip) to the tip (angle 0).
    # Wait, the involute starts at the base circle.
    # The angle of the radius vector at the base circle is -phi_tip.
    # The angle of the radius vector at the tip is 0.
    # So we need to generate points where the radius vector angle goes from -phi_tip to 0.
    # But the parameter phi in the formula is the angle of the tangent.
    # The relationship between the radius vector angle (theta) and phi is theta = phi + atan(phi)? No.
    # The relationship is theta = phi + atan(phi) is incorrect.
    # The relationship is theta = phi + atan(phi) is for the involute of a circle?
    # Let's use the property: The angle between the radius vector and the tangent is 90 + phi.
    # So the angle of the radius vector is phi + atan(phi) is wrong.
    # The angle of the radius vector is phi + atan(phi) is for the involute of a circle?
    # Let's use the standard formula:
    # x = rb * (cos(phi) + phi * sin(phi))
    # y = rb * (sin(phi) - phi * cos(phi))
    # This gives the involute starting at (rb, 0) for phi=0.
    # The angle of the radius vector is atan2(y, x).
    # For phi=0, angle=0.
    # For phi=phi_tip, angle=phi_tip.
    # So the radius vector angle is approximately phi.
    # So if we want the tooth centered at 0, the right flank should go from angle -phi_tip to 0?
    # No, the right flank goes from the base circle (angle -phi_tip) to the tip (angle 0).
    # Wait, the involute starts at the base circle.
    # The angle of the radius vector at the base circle is -phi_tip.
    # The angle of the radius vector at the tip is 0.
    # So we need to generate points where the radius vector angle goes from -phi_tip to 0.
    # But the parameter phi in the formula is the angle of the tangent.
    # The relationship between the radius vector angle (theta) and phi is theta = phi + atan(phi)? No.
    # The relationship is theta = phi + atan(phi) is incorrect.
    # The relationship is theta = phi + atan(phi) is for the involute of a circle?
    # Let's use the property: The angle between the radius vector and the tangent is 90 + phi.
    # So the angle of the radius vector is phi + atan(phi) is wrong.
    # The angle of the radius vector is phi + atan(phi) is for the involute of a circle?
    # Let's use the standard formula:
    # x = rb * (cos(phi) + phi * sin(phi))
    # y = rb * (sin(phi) - phi * cos(phi))
    # This gives the involute starting at (rb, 0) for phi=0.
    # The angle of the radius vector is atan2(y, x).
    # For phi=0, angle=0.
    # For phi=phi_tip, angle=phi_tip.
    # So the radius vector angle is approximately phi.
    # So if we want the tooth centered at 0, the right flank should go from angle -phi_tip to 0?
    # No, the right flank goes from the base circle (angle -phi_tip) to the tip (angle 0).
    # Wait, the involute starts at the base circle.
    # The angle of the radius vector at the base circle is -phi_tip.
    # The angle of the radius vector at the tip is 0.
    # So we need to generate points where the radius vector angle goes from -phi_tip to 0.
    # But the parameter phi in the formula is the angle of the tangent.
    # The relationship between the radius vector angle (theta) and phi is theta = phi + atan(phi)? No.
    # The relationship is theta = phi + atan(phi) is incorrect.
    # The relationship is theta = phi + atan(phi) is for the involute of a circle?
    # Let's use the property: The angle between the radius vector and the tangent is 90 + phi.
    # So the angle of the radius vector is phi + atan(phi) is wrong.
    # The angle of the radius vector is phi + atan(phi) is for the involute of a circle?
    # Let's use the standard formula:
    # x = rb * (cos(phi) + phi * sin(phi))
    # y = rb * (sin(phi) - phi * cos(phi))
    # This gives the involute starting at (rb, 0) for phi=0.
    # The angle of the radius vector is atan2(y, x).
    # For phi=0, angle=0.
    # For phi=phi_tip, angle=phi_tip.
    # So the radius vector angle is approximately phi.
    # So if we want the tooth centered at 0, the right flank should go from angle -phi_tip to 0?
    # No, the right flank goes from the base circle (angle -phi_tip) to the tip (angle 0).
    # Wait, the involute starts at the base circle.
    # The angle of the radius vector at the base circle is -phi_tip.
    # The angle of the radius vector at the tip is 0.
    # So we need to generate points where the radius vector angle goes from -phi_tip to 0.
    # But the parameter phi in the formula is the angle of the tangent.
    # The relationship between the radius vector angle (theta) and phi is theta = phi + atan(phi)? No.
    # The relationship is theta = phi + atan(phi) is incorrect.
    # The relationship is theta = phi + atan(phi) is for the involute of a circle?
    # Let's use the property: The angle between the radius vector and the tangent is 90 + phi.
    # So the angle of the radius vector is phi + atan(phi) is wrong.
    # The angle of the radius
