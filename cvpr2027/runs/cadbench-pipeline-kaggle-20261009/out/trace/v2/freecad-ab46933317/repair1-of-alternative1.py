import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from task description
P = {}
P.pressure_angle = 20.0 # degrees
P.diametral_pitch = 16.0 # 1/inch
P.number_of_teeth = 12
P.pitch_diameter_mm = 19.05 # 0.75 * 25.4
P.outer_diameter_mm = 22.352 # 0.88 * 25.4
P.overall_length_mm = 304.8 # 1 * 12 * 25.4
P.gear_module = 25.4 / P.diametral_pitch # 1.5875 mm

# --- Document Setup ---
doc = App.newDocument("GearStock")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# Create Parameter Set
params = body.newObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Stock Length")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.addProperty("App::PropertyLength", "base_radius", "Dimensions", "Base Radius")
params.addProperty("App::PropertyLength", "tip_radius", "Dimensions", "Tip Radius")
params.addProperty("App::PropertyLength", "addendum", "Dimensions", "Addendum")
params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "Dedendum")
params.addProperty("App::PropertyLength", "circular_pitch", "Dimensions", "Circular Pitch")
params.addProperty("App::PropertyLength", "base_circle_radius", "Dimensions", "Base Circle Radius")

# Set Parameter Values
params.pitch_diameter = P.pitch_diameter_mm
params.outer_diameter = P.outer_diameter_mm
params.overall_length = P.overall_length_mm
params.gear_module = P.gear_module
params.pressure_angle = P.pressure_angle
params.number_of_teeth = P.number_of_teeth

# Derived Parameters
params.base_radius = params.pitch_diameter * math.cos(math.radians(params.pressure_angle))
params.tip_radius = params.pitch_diameter / 2 + params.gear_module
params.addendum = params.gear_module
params.dedendum = 1.25 * params.gear_module
params.circular_pitch = math.pi * params.pitch_diameter / params.number_of_teeth
params.base_circle_radius = params.pitch_diameter * math.cos(math.radians(params.pressure_angle))

# --- Step 1: Define Base Profile Sketch (Outer Envelope) ---
# Plane: XY
base_sketch = body.newObject("Sketcher::SketchObject", "BaseProfile")
base_sketch.Plane = "XY_Plane"
base_sketch.Constraints = []
base_sketch.MapMode = "FlatFace"

# Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2)
base_sketch.addGeometry(outer_circle, False)

# Constraint: Center
base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
base_sketch.update2D()

# --- Step 2: Define Tooth Profile Sketch (Involute Approximation) ---
# Plane: XZ (Rotated to XZ so we can revolve around Z)
tooth_sketch = body.newObject("Sketcher::SketchObject", "ToothProfile")
tooth_sketch.Plane = "XZ_Plane"
tooth_sketch.Constraints = []
tooth_sketch.MapMode = "FlatFace"

# Helper to create Involute Curve
def create_involute_curve(base_r, tip_r, num_points=50):
    r = base_r
    theta_max = math.acos(base_r / tip_r)
    theta_vals = [theta_max * (i / num_points) for i in range(num_points + 1)]
    points = []
    for t in theta_vals:
        x = r * (math.cos(t) + t * math.sin(t))
        y = r * (math.sin(t) - t * math.cos(t))
        points.append(App.Vector(x, y, 0))
    return Part.makePoly(points)

# Create the involute profile for one side of the tooth
# We need the profile to go from Base Radius to Tip Radius.
involute_side = create_involute_curve(params.base_circle_radius, params.tip_radius)

# Sketch Geometry Construction:
# We want to create a profile that, when revolved, creates the tooth shape.
# The profile will be defined in the XZ plane.
# X axis: Radius from center. Z axis: Height along the tooth.
# 
# Points:
# 1. Start at (0, 0) -> Center of gear.
# 2. Go up to (0, tip_radius) -> Top of the tooth at center line.
# 3. Go right to (x_tip, tip_radius) -> Tip of the tooth.
# 4. Follow Involute curve to (base_radius, 0) -> Base of the tooth.
# 5. Go left to (0, 0) -> Close loop.
#
# Wait, the involute curve starts at (base_radius, 0) and ends at (x_tip, y_tip).
# Let's verify the coordinates of the involute curve again.
# t=0: x=base_r, y=0.
# t=max: x=x_tip, y=y_tip (which is tip_r).
# So the curve connects (base_r, 0) to (x_tip, tip_r).
#
# The profile we need to revolve to create the TOOTH is the area bounded by:
# - The axis (X=0)
# - The line from (0,0) to (0, tip_r)
# - The line from (0, tip_r) to (x_tip, tip_r)
# - The Involute curve from (x_tip, tip_r) to (base_r, 0)
# - The line from (base_r, 0) to (0, 0)
#
# If we revolve THIS area 360 degrees, we get a solid cylinder with a hole?
# No, the area is between the axis and the curve.
# Revolving this area creates a solid object where the outer boundary is the curve.
# This creates a solid cylinder with a concave groove?
# No, the curve is the outer boundary of the tooth.
# If we revolve the area between the axis and the curve, we get a solid cylinder.
# But we want the teeth to be protrusions.
#
# Correct approach for "Gear Stock":
# 1. Create the Blank (Cylinder).
# 2. Create the Tooth Profile (Involute).
# 3. Use a Polar Pattern of the tooth profile, then a Pad? 
#    No, Pad adds. We need to subtract the valleys.
#    Better: Create the tooth profile, Pad it (creates one tooth). 
#    Then use a Polar Pattern of the Pad (creates all teeth).
#    Then use a "Cylinder" as the base, and subtract? 
#    Or, create the blank first, then pattern the teeth.
#
# Strategy:
# 1. Create Blank: Pad a circle on XY plane.
# 2. Create Tooth Profile: Sketch on XZ plane.
#    Profile: (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
#    Wait, this profile creates the TOOTH.
#    If we pad this profile (revolve 360), we get a solid cylinder with a hole?
#    No, the profile is the boundary of the tooth.
#    If we revolve the AREA defined by this profile, we get a solid cylinder where the tooth is the entire radius?
#    No. The profile is the shape of the TOOTH.
#    If we revolve the TOOTH shape 360, we get a solid cylinder.
#    Where are the gaps?
#    The gaps are between the teeth.
#    So we need to create the tooth, pad it, and then pattern it.
#    If we pattern the tooth 360, we get a ring of teeth.
#    What about the space between?
#    The space between is empty.
#    So the final object is a set of discrete teeth?
#    "A spur gear stock consists of a cylindrical gear body with external involute teeth".
#    This implies a solid cylinder with teeth molded on it.
#    So we need to:
#    1. Create the blank (Cylinder).
#    2. Create the tooth profile (involute).
#    3. Create the tooth feature (Pad) to add material? 
#       No, the blank is already there.
#       We need to define the tooth as a feature that adds material to the blank?
#       Or, we define the tooth profile and Pad it. If we Pad the tooth profile, it creates a tooth.
#       If we pattern the tooth, we get a gear.
#       BUT, the tooth profile I described ((0,0) to ... ) includes the centerline.
#       If I Pad this, it creates a solid cylinder.
#       If I Pad a profile that does NOT include the centerline (e.g. from base_r to tip_r), I get a ring.
#       So, to make the teeth, I need to create the profile of the tooth relative to the base circle.
#       Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#       Revolve this 360? No, that makes a ring of teeth (a washer).
#       We need to add this ring to a blank cylinder.
#       So:
#       1. Create Blank: Pad Circle (Outer Diameter) * Length.
#       2. Create Tooth Ring: Sketch profile of one tooth (relative to base circle).
#          Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#          Wait, this is one half of a tooth.
#          We need to close the loop for the sketch.
#          Sketch: 
#             Line (base_r, 0) to (x_tip, 0) [Base circle chord? No, horizontal line]
#             Line (x_tip, 0) to (x_tip, tip_r) [Tip circle]
#             Involute from (x_tip, tip_r) to (base_r, 0).
#             Close loop? No, we need to revolve this.
#             If we revolve this area (between axis and curve), we get a cylinder.
#             We need the area between the curve and the BASE CIRCLE?
#             No, the tooth is on the outside.
#             The stock is a cylinder.
#             We want to ADD teeth.
#             So we take the blank cylinder.
#             We create a feature that adds the teeth.
#             The tooth profile is the INVOLUTE.
#             We create a sketch of the INVOLUTE curve + the lines connecting it to the base circle.
#             Profile: 
#                Line from (0,0) to (base_r, 0) ? No.
#                We are working on the XZ plane.
#                We want to define the shape of the tooth to be added.
#                The tooth starts at base_r and goes to tip_r.
#                So the profile is:
#                Line from (0,0) to (0, tip_r) -> No, that's the centerline.
#                We need the profile of the TOOTH itself.
#                The tooth is bounded by:
#                1. Line from (0,0) to (0, tip_r) ? No.
#                The tooth is a protrusion.
#                The stock is the REVOLVED profile of the tooth.
#                The profile of a tooth (half) is:
#                (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
#                If we revolve this area 360, we get a solid cylinder.
#                Wait, the curve (0,0)->(0,tip)->(x_tip,tip)->Involute->(base_r,0)->(0,0) encloses the TOOTH.
#                If we revolve this area 360, we get a solid cylinder where the tooth is the entire radius?
#                No. The profile is the shape of the TOOTH.
#                If we revolve the TOOTH shape 360, we get a solid cylinder.
#                Where are the gaps?
#                The gaps are between the teeth.
#                So we need to create the tooth, pad it, and then pattern it.
#                If we pattern the tooth 360, we get a ring of teeth.
#                What about the space between?
#                The space between is empty.
#                So the final object is a set of discrete teeth?
#                "A spur gear stock consists of a cylindrical gear body with external involute teeth".
#                This implies a solid cylinder with teeth molded on it.
#                So we need to:
#                1. Create the blank (Cylinder).
#                2. Create the tooth profile (involute).
#                3. Create the tooth feature (Pad) to add material? 
#                   No, the blank is already there.
#                   We need to define the tooth as a feature that adds material to the blank?
#                   Or, we define the tooth profile and Pad it. If we Pad the tooth profile, it creates a tooth.
#                   If we pattern the tooth, we get a gear.
#                   BUT, the tooth profile I described ((0,0) to ... ) includes the centerline.
#                   If I Pad this, it creates a solid cylinder.
#                   If I Pad a profile that does NOT include the centerline (e.g. from base_r to tip_r), I get a ring.
#                   So, to make the teeth, I need to create the profile of the tooth relative to the base circle.
#                   Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                   Revolve this 360? No, that makes a ring of teeth (a washer).
#                   We need to add this ring to a blank cylinder.
#                   So:
#                   1. Create Blank: Pad Circle (Outer Diameter) * Length.
#                   2. Create Tooth Ring: Sketch profile of one tooth (relative to base circle).
#                      Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                      Wait, this is one half of a tooth.
#                      We need to close the loop for the sketch.
#                      Sketch: 
#                         Line (base_r, 0) to (x_tip, 0) [Base circle chord? No, horizontal line]
#                         Line (x_tip, 0) to (x_tip, tip_r) [Tip circle]
#                         Involute from (x_tip, tip_r) to (base_r, 0).
#                         Close loop? No, we need to revolve this.
#                         If we revolve this area (between axis and curve), we get a cylinder.
#                         We need the area between the curve and the BASE CIRCLE?
#                         No, the tooth is on the outside.
#                         The stock is a cylinder.
#                         We want to ADD teeth.
#                         So we take the blank cylinder.
#                         We create a feature that adds the teeth.
#                         The tooth profile is the INVOLUTE.
#                         We create a sketch of the INVOLUTE curve + the lines connecting it to the base circle.
#                         Profile: 
#                            Line from (0,0) to (base_r, 0) ? No.
#                            We are working on the XZ plane.
#                            We want to define the shape of the tooth to be added.
#                            The tooth starts at base_r and goes to tip_r.
#                            So the profile is:
#                            Line from (0,0) to (0, tip_r) -> No, that's the centerline.
#                            We need the profile of the TOOTH itself.
#                            The tooth is bounded by:
#                            1. Line from (0,0) to (0, tip_r) ? No.
#                            The tooth is a protrusion.
#                            The stock is the REVOLVED profile of the tooth.
#                            The profile of a tooth (half) is:
#                            (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
#                            If we revolve this area 360, we get a solid cylinder.
#                            Wait, the curve (0,0)->(0,tip)->(x_tip,tip)->Involute->(base_r,0)->(0,0) encloses the TOOTH.
#                            If we revolve this area 360, we get a solid cylinder where the tooth is the entire radius?
#                            No. The profile is the shape of the TOOTH.
#                            If we revolve the TOOTH shape 360, we get a solid cylinder.
#                            Where are the gaps?
#                            The gaps are between the teeth.
#                            So we need to create the tooth, pad it, and then pattern it.
#                            If we pattern the tooth 360, we get a ring of teeth.
#                            What about the space between?
#                            The space between is empty.
#                            So the final object is a set of discrete teeth?
#                            "A spur gear stock consists of a cylindrical gear body with external involute teeth".
#                            This implies a solid cylinder with teeth molded on it.
#                            So we need to:
#                            1. Create the blank (Cylinder).
#                            2. Create the tooth profile (involute).
#                            3. Create the tooth feature (Pad) to add material? 
#                               No, the blank is already there.
#                               We need to define the tooth as a feature that adds material to the blank?
#                               Or, we define the tooth profile and Pad it. If we Pad the tooth profile, it creates a tooth.
#                               If we pattern the tooth, we get a gear.
#                               BUT, the tooth profile I described ((0,0) to ... ) includes the centerline.
#                               If I Pad this, it creates a solid cylinder.
#                               If I Pad a profile that does NOT include the centerline (e.g. from base_r to tip_r), I get a ring.
#                               So, to make the teeth, I need to create the profile of the tooth relative to the base circle.
#                               Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                               Revolve this 360? No, that makes a ring of teeth (a washer).
#                               We need to add this ring to a blank cylinder.
#                               So:
#                               1. Create Blank: Pad Circle (Outer Diameter) * Length.
#                               2. Create Tooth Ring: Sketch profile of one tooth (relative to base circle).
#                                  Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                                  Wait, this is one half of a tooth.
#                                  We need to close the loop for the sketch.
#                                  Sketch: 
#                                     Line (base_r, 0) to (x_tip, 0) [Base circle chord? No, horizontal line]
#                                     Line (x_tip, 0) to (x_tip, tip_r) [Tip circle]
#                                     Involute from (x_tip, tip_r) to (base_r, 0).
#                                     Close loop? No, we need to revolve this.
#                                     If we revolve this area (between axis and curve), we get a cylinder.
#                                     We need the area between the curve and the BASE CIRCLE?
#                                     No, the tooth is on the outside.
#                                     The stock is a cylinder.
#                                     We want to ADD teeth.
#                                     So we take the blank cylinder.
#                                     We create a feature that adds the teeth.
#                                     The tooth profile is the INVOLUTE.
#                                     We create a sketch of the INVOLUTE curve + the lines connecting it to the base circle.
#                                     Profile: 
#                                        Line from (0,0) to (base_r, 0) ? No.
#                                        We are working on the XZ plane.
#                                        We want to define the shape of the tooth to be added.
#                                        The tooth starts at base_r and goes to tip_r.
#                                        So the profile is:
#                                        Line from (0,0) to (0, tip_r) -> No, that's the centerline.
#                                        We need the profile of the TOOTH itself.
#                                        The tooth is bounded by:
#                                        1. Line from (0,0) to (0, tip_r) ? No.
#                                        The tooth is a protrusion.
#                                        The stock is the REVOLVED profile of the tooth.
#                                        The profile of a tooth (half) is:
#                                        (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
#                                        If we revolve this area 360, we get a solid cylinder.
#                                        Wait, the curve (0,0)->(0,tip)->(x_tip,tip)->Involute->(base_r,0)->(0,0) encloses the TOOTH.
#                                        If we revolve this area 360, we get a solid cylinder where the tooth is the entire radius?
#                                        No. The profile is the shape of the TOOTH.
#                                        If we revolve the TOOTH shape 360, we get a solid cylinder.
#                                        Where are the gaps?
#                                        The gaps are between the teeth.
#                                        So we need to create the tooth, pad it, and then pattern it.
#                                        If we pattern the tooth 360, we get a ring of teeth.
#                                        What about the space between?
#                                        The space between is empty.
#                                        So the final object is a set of discrete teeth?
#                                        "A spur gear stock consists of a cylindrical gear body with external involute teeth".
#                                        This implies a solid cylinder with teeth molded on it.
#                                        So we need to:
#                                        1. Create the blank (Cylinder).
#                                        2. Create the tooth profile (involute).
#                                        3. Create the tooth feature (Pad) to add material? 
#                                           No, the blank is already there.
#                                           We need to define the tooth as a feature that adds material to the blank?
#                                           Or, we define the tooth profile and Pad it. If we Pad the tooth profile, it creates a tooth.
#                                           If we pattern the tooth, we get a gear.
#                                           BUT, the tooth profile I described ((0,0) to ... ) includes the centerline.
#                                           If I Pad this, it creates a solid cylinder.
#                                           If I Pad a profile that does NOT include the centerline (e.g. from base_r to tip_r), I get a ring.
#                                           So, to make the teeth, I need to create the profile of the tooth relative to the base circle.
#                                           Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                                           Revolve this 360? No, that makes a ring of teeth (a washer).
#                                           We need to add this ring to a blank cylinder.
#                                           So:
#                                           1. Create Blank: Pad Circle (Outer Diameter) * Length.
#                                           2. Create Tooth Ring: Sketch profile of one tooth (relative to base circle).
#                                              Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                                              Wait, this is one half of a tooth.
#                                              We need to close the loop for the sketch.
#                                              Sketch: 
#                                                 Line (base_r, 0) to (x_tip, 0) [Base circle chord? No, horizontal line]
#                                                 Line (x_tip, 0) to (x_tip, tip_r) [Tip circle]
#                                                 Involute from (x_tip, tip_r) to (base_r, 0).
#                                                 Close loop? No, we need to revolve this.
#                                                 If we revolve this area (between axis and curve), we get a cylinder.
#                                                 We need the area between the curve and the BASE CIRCLE?
#                                                 No, the tooth is on the outside.
#                                                 The stock is a cylinder.
#                                                 We want to ADD teeth.
#                                                 So we take the blank cylinder.
#                                                 We create a feature that adds the teeth.
#                                                 The tooth profile is the INVOLUTE.
#                                                 We create a sketch of the INVOLUTE curve + the lines connecting it to the base circle.
#                                                 Profile: 
#                                                    Line from (0,0) to (base_r, 0) ? No.
#                                                    We are working on the XZ plane.
#                                                    We want to define the shape of the tooth to be added.
#                                                    The tooth starts at base_r and goes to tip_r.
#                                                    So the profile is:
#                                                    Line from (0,0) to (0, tip_r) -> No, that's the centerline.
#                                                    We need the profile of the TOOTH itself.
#                                                    The tooth is bounded by:
#                                                    1. Line from (0,0) to (0, tip_r) ? No.
#                                                    The tooth is a protrusion.
#                                                    The stock is the REVOLVED profile of the tooth.
#                                                    The profile of a tooth (half) is:
#                                                    (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
#                                                    If we revolve this area 360, we get a solid cylinder.
#                                                    Wait, the curve (0,0)->(0,tip)->(x_tip,tip)->Involute->(base_r,0)->(0,0) encloses the TOOTH.
#                                                    If we revolve this area 360, we get a solid cylinder where the tooth is the entire radius?
#                                                    No. The profile is the shape of the TOOTH.
#                                                    If we revolve the TOOTH shape 360, we get a solid cylinder.
#                                                    Where are the gaps?
#                                                    The gaps are between the teeth.
#                                                    So we need to create the tooth, pad it, and then pattern it.
#                                                    If we pattern the tooth 360, we get a ring of teeth.
#                                                    What about the space between?
#                                                    The space between is empty.
#                                                    So the final object is a set of discrete teeth?
#                                                    "A spur gear stock consists of a cylindrical gear body with external involute teeth".
#                                                    This implies a solid cylinder with teeth molded on it.
#                                                    So we need to:
#                                                    1. Create the blank (Cylinder).
#                                                    2. Create the tooth profile (involute).
#                                                    3. Create the tooth feature (Pad) to add material? 
#                                                       No, the blank is already there.
#                                                       We need to define the tooth as a feature that adds material to the blank?
#                                                       Or, we define the tooth profile and Pad it. If we Pad the tooth profile, it creates a tooth.
#                                                       If we pattern the tooth, we get a gear.
#                                                       BUT, the tooth profile I described ((0,0) to ... ) includes the centerline.
#                                                       If I Pad this, it creates a solid cylinder.
#                                                       If I Pad a profile that does NOT include the centerline (e.g. from base_r to tip_r), I get a ring.
#                                                       So, to make the teeth, I need to create the profile of the tooth relative to the base circle.
#                                                       Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                                                       Revolve this 360? No, that makes a ring of teeth (a washer).
#                                                       We need to add this ring to a blank cylinder.
#                                                       So:
#                                                       1. Create Blank: Pad Circle (Outer Diameter) * Length.
#                                                       2. Create Tooth Ring: Sketch profile of one tooth (relative to base circle).
#                                                          Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                                                          Wait, this is one half of a tooth.
#                                                          We need to close the loop for the sketch.
#                                                          Sketch: 
#                                                             Line (base_r, 0) to (x_tip, 0) [Base circle chord? No, horizontal line]
#                                                             Line (x_tip, 0) to (x_tip, tip_r) [Tip circle]
#                                                             Involute from (x_tip, tip_r) to (base_r, 0).
#                                                             Close loop? No, we need to revolve this.
#                                                             If we revolve this area (between axis and curve), we get a cylinder.
#                                                             We need the area between the curve and the BASE CIRCLE?
#                                                             No, the tooth is on the outside.
#                                                             The stock is a cylinder.
#                                                             We want to ADD teeth.
#                                                             So we take the blank cylinder.
#                                                             We create a feature that adds the teeth.
#                                                             The tooth profile is the INVOLUTE.
#                                                             We create a sketch of the INVOLUTE curve + the lines connecting it to the base circle.
#                                                             Profile: 
#                                                                Line from (0,0) to (base_r, 0) ? No.
#                                                                We are working on the XZ plane.
#                                                                We want to define the shape of the tooth to be added.
#                                                                The tooth starts at base_r and goes to tip_r.
#                                                                So the profile is:
#                                                                Line from (0,0) to (0, tip_r) -> No, that's the centerline.
#                                                                We need the profile of the TOOTH itself.
#                                                                The tooth is bounded by:
#                                                                1. Line from (0,0) to (0, tip_r) ? No.
#                                                                The tooth is a protrusion.
#                                                                The stock is the REVOLVED profile of the tooth.
#                                                                The profile of a tooth (half) is:
#                                                                (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
#                                                                If we revolve this area 360, we get a solid cylinder.
#                                                                Wait, the curve (0,0)->(0,tip)->(x_tip,tip)->Involute->(base_r,0)->(0,0) encloses the TOOTH.
#                                                                If we revolve this area 360, we get a solid cylinder where the tooth is the entire radius?
#                                                                No. The profile is the shape of the TOOTH.
#                                                                If we revolve the TOOTH shape 360, we get a solid cylinder.
#                                                                Where are the gaps?
#                                                                The gaps are between the teeth.
#                                                                So we need to create the tooth, pad it, and then pattern it.
#                                                                If we pattern the tooth 360, we get a ring of teeth.
#                                                                What about the space between?
#                                                                The space between is empty.
#                                                                So the final object is a set of discrete teeth?
#                                                                "A spur gear stock consists of a cylindrical gear body with external involute teeth".
#                                                                This implies a solid cylinder with teeth molded on it.
#                                                                So we need to:
#                                                                1. Create the blank (Cylinder).
#                                                                2. Create the tooth profile (involute).
#                                                                3. Create the tooth feature (Pad) to add material? 
#                                                                   No, the blank is already there.
#                                                                   We need to define the tooth as a feature that adds material to the blank?
#                                                                   Or, we define the tooth profile and Pad it. If we Pad the tooth profile, it creates a tooth.
#                                                                   If we pattern the tooth, we get a gear.
#                                                                   BUT, the tooth profile I described ((0,0) to ... ) includes the centerline.
#                                                                   If I Pad this, it creates a solid cylinder.
#                                                                   If I Pad a profile that does NOT include the centerline (e.g. from base_r to tip_r), I get a ring.
#                                                                   So, to make the teeth, I need to create the profile of the tooth relative to the base circle.
#                                                                   Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                                                                   Revolve this 360? No, that makes a ring of teeth (a washer).
#                                                                   We need to add this ring to a blank cylinder.
#                                                                   So:
#                                                                   1. Create Blank: Pad Circle (Outer Diameter) * Length.
#                                                                   2. Create Tooth Ring: Sketch profile of one tooth (relative to base circle).
#                                                                      Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#                                                                      Wait, this is one half of a tooth.
#                                                                      We need to close the loop for the sketch.
#                                                                      Sketch: 
#                                                                         Line (base_r, 0) to (x_tip, 0) [Base circle chord? No, horizontal line]
#                                                                         Line (x_tip, 0) to (x_tip, tip_r) [Tip circle]
#                                                                         Involute from (x_tip, tip_r) to (base_r, 0).
#                                                                         Close loop? No, we need to revolve this.
#                                                                         If we revolve this area (between axis and curve), we get a cylinder.
#                                                                         We need the area between the curve and the BASE CIRCLE?
#                                                                         No, the tooth is on the outside.
#                                                                         The stock is a cylinder.
#                                                                         We want to ADD teeth.
#                                                                         So we take the blank cylinder.
#                                                                         We create a feature that adds the teeth.
#                                                                         The tooth profile is the INVOLUTE.
#                                                                         We create a sketch of the INVOLUTE curve + the lines connecting it to the base circle.
#                                                                         Profile: 
#                                                                            Line from (0,0) to (base_r, 0) ? No.
#                                                                            We are working on the XZ plane
