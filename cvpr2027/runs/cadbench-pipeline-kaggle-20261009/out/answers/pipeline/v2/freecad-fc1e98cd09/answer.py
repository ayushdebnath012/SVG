import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Part Parameters (in mm)
P = App.Parametric()
P.pressure_angle = 20.0          # degrees
P.diametral_pitch = 24.0         # teeth per inch
P.number_of_teeth = 12           # teeth
P.pitch_diameter = 12.7          # mm (0.5 in)
P.outer_diameter = 14.732        # mm (0.58 in)
P.overall_length = 304.8         # mm (1 ft)

# --- Document Setup ---
doc = App.newDocument("SpurGearStock")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We create a VarSet to hold the named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.pitch_diameter = P.pitch_diameter
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.outer_diameter = P.outer_diameter
params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Overall Length")
params.overall_length = P.overall_length
params.addProperty("App::PropertyLength", "module", "Dimensions", "Module (calculated)")
# Module = Pitch Diameter / Number of Teeth
params.module = P.pitch_diameter / P.number_of_teeth
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = P.pressure_angle
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.number_of_teeth = P.number_of_teeth
params.addProperty("App::PropertyInteger", "diametral_pitch", "Dimensions", "Diametral Pitch")
params.diametral_pitch = P.diametral_pitch

# --- Base Sketch (Pitch Cylinder) ---
# We will build the gear tooth profile on the Pitch Circle, then revolve it.
# The profile will be defined relative to the pitch circle radius.
sketch = body.newObject("Sketcher::SketchObject", "GearProfile")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch.MapMode = "FlatFace"
sketch.ConstrainAuto = True
sketch.ConstrainFully = True

# Helper to add geometry
def add_line(p1, p2, visible=True):
    sketch.addGeometry(Part.LineSegment(p1, p2), visible)

def add_circle(center, radius, visible=True):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), visible)

# 1. Pitch Circle (Reference)
# Radius = Pitch Diameter / 2
pitch_radius = params.pitch_diameter / 2.0
add_circle(App.Vector(0, 0, 0), pitch_radius, False) # Hidden reference

# 2. Outer Circle (Tip Circle)
# Radius = Outer Diameter / 2
outer_radius = params.outer_diameter / 2.0
add_circle(App.Vector(0, 0, 0), outer_radius, False) # Hidden reference

# 3. Base Circle (for involute generation)
# Radius = Pitch Diameter * cos(Pressure Angle)
base_radius = params.pitch_diameter * (App.cos(App.degToRad(params.pressure_angle)))
add_circle(App.Vector(0, 0, 0), base_radius, False) # Hidden reference

# 4. Tooth Profile Generation
# We need to generate the involute curve.
# Since FreeCAD Sketcher doesn't have a native "Involute" constraint, we will approximate
# the tooth profile using a series of points or a spline if possible, 
# but the most robust way in a script without external plugins is to define the key points
# of the involute and use a Spline, or construct the geometry mathematically.
# 
# Strategy: Define the involute curve mathematically and add it as a Spline.
# Involute equation:
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# where t is the involute parameter (angle in radians).
# 
# Tooth Geometry:
# - Start at Base Circle (t=0)
# - End at Outer Circle (t_max)
# - Center of tooth is at angle 0.
# - We need half-tooth profile (from center to flank).
# - Addendum = (Outer - Pitch) / 2
# - Dedendum is usually not part of the "tooth profile" sketch if we are just extruding the blank,
#   but for a gear stock, we usually extrude the full blank (cylinder) and then cut teeth.
#   HOWEVER, the prompt asks for "involute spur teeth distributed around the outer perimeter".
#   This implies we should model the teeth themselves.
#   
#   Approach: 
#   1. Create a sketch of ONE tooth profile (half tooth) on the Pitch Circle plane.
#   2. Use a Polar Pattern to create all teeth.
#   3. Pad the profile.
#   
#   Wait, standard gear modeling in PartDesign often involves:
#   - A base cylinder (blank).
#   - A sketch of the tooth profile on the pitch circle.
#   - A revolution of the tooth profile to create the gear.
#   
#   Let's refine the "Gear Stock" interpretation.
#   "A spur gear stock consists of a cylindrical gear blank extruded along an axial length, with involute spur teeth distributed around the outer perimeter."
#   This sounds like a solid block of material that has teeth cut into it.
#   So:
#   1. Create a cylinder (Blank).
#   2. Create a sketch of the tooth profile on the Pitch Circle.
#   3. Use a "Groove" or "Pocket" with a revolution to cut the teeth? 
#      OR, simpler: Create the tooth profile, revolve it to make the gear, then subtract the root fillets?
#      
#   Actually, the most efficient "Stock" representation that allows parameterization of the teeth 
#   is to model the teeth as positive geometry (Pad) and then maybe fillet the roots.
#   But "Stock" usually implies the raw material.
#   Let's interpret "Stock" as the final machined part shape (the gear itself).
#   
#   Revised Plan:
#   1. Create a sketch of the INVOLUTE TOOTH PROFILE (half tooth) on the Pitch Circle.
#   2. Pad this profile 360 degrees (Revolution) to create the gear teeth.
#   3. This creates the gear.
#   4. To make it a "stock" (cylindrical blank with teeth), we might need to ensure the root is cylindrical.
#      The involute profile naturally goes to the base circle. The space between teeth (valley) is usually 
#      defined by the dedendum.
#      
#   Let's stick to the prompt's specific parameters:
#   - pitch_diameter, outer_diameter, overall_length.
#   - These define the outer envelope.
#   
#   Let's build the tooth profile sketch:
#   - Origin at center of pitch circle.
#   - Draw the involute curve from Base Circle to Outer Circle.
#   - Draw the radial line from center to the start of the involute (Base Circle).
#   - Draw the radial line from center to the end of the involute (Outer Circle).
#   - Close the loop? No, we need the profile of the tooth.
#   
#   Actually, a simpler approach for a "Stock" with teeth:
#   1. Create a cylinder of Outer Diameter and Overall Length.
#   2. Create a sketch of the tooth profile on the Pitch Circle.
#   3. Use a "Groove" (subtractive revolution) to cut the teeth out of the cylinder?
#      This requires the groove to go from the outer diameter down to the root diameter.
#      We don't have a "root_diameter" parameter explicitly, but we can calculate it.
#      Root Diameter = Pitch Diameter - 2 * (1.25 / DP) (Standard full depth)
#      Or simply, the space between teeth.
#      
#   Let's try the "Positive" approach (Pad the teeth) as it's more robust for "Stock" visualization 
#   unless specifically asked for a subtractive process.
#   However, "Stock" implies the blank.
#   Let's assume the user wants the final gear shape (the stock of the gear).
#   
#   Let's calculate the Root Diameter (Dedendum circle).
#   Standard Gear:
#   Addendum = 1 / DP
#   Dedendum = 1.25 / DP
#   Clearance = 0.25 / DP
#   Whole Depth = Addendum + Dedendum = 1.25 / DP
#   
#   Pitch Radius = P.pitch_diameter / 2
#   Addendum = 1 / P.diametral_pitch
#   Dedendum = 1.25 / P.diametral_pitch
#   Root Radius = Pitch Radius - Dedendum
#   Outer Radius = Pitch Radius + Addendum
#   
#   Let's verify with given numbers:
#   DP = 24.
#   Addendum = 1/24 = 0.04166 in = 1.058 mm.
#   Pitch Radius = 6.35 mm.
#   Outer Radius = 6.35 + 1.058 = 7.408 mm.
#   Given Outer Diameter = 14.732 mm -> Radius = 7.366 mm. Close enough (rounding in prompt).
#   
#   So we will model the gear teeth using a Pad of the tooth profile.
#   To get the "Stock" look (cylindrical body with teeth), we can:
#   1. Pad the tooth profile 360 degrees.
#   2. This creates a gear with pointed roots at the base circle.
#   3. We need to round the roots (fillet) to match the dedendum circle.
#   
#   Wait, if we just pad the involute from Base to Outer, the valleys are sharp at the Base Circle.
#   We need to cut the valleys to the Root Diameter.
#   
#   Alternative Plan (Subtractive):
#   1. Create a Cylinder (Blank) of Outer Diameter and Length.
#   2. Create a sketch of the tooth profile (Involute + Root Chord) on the Pitch Circle.
#   3. Use a "Groove" (Revolution) to cut the teeth.
#      The groove profile will be the "negative" of the tooth.
#      It will go from Outer Diameter down to Root Diameter.
#   
#   This seems the most accurate representation of a "Stock" with teeth.
#   
#   Let's implement the Subtractive approach.
#   
#   Step 1: Create the Blank Cylinder.
#   Step 2: Create the Tooth Profile Sketch.
#   Step 3: Create a Groove (Revolution) to cut the teeth.
#   
#   Calculations:
#   Module = Pitch / Teeth = 12.7 / 12 = 1.05833 mm.
#   Addendum = Module = 1.05833 mm.
#   Dedendum = 1.25 * Module = 1.3229 mm.
#   Root Radius = Pitch Radius - Dedendum = 6.35 - 1.3229 = 5.027 mm.
#   Outer Radius = Pitch Radius + Addendum = 6.35 + 1.05833 = 7.408 mm.
#   
#   Let's adjust the parameters to match the prompt's specific Outer Diameter (14.732mm -> 7.366mm radius).
#   The prompt's Outer Diameter is slightly smaller than standard calculation (7.408 vs 7.366).
#   We will use the Prompt's Outer Diameter for the blank.
#   We will calculate the Root Diameter based on standard formulas or derive from the prompt's implied geometry.
#   Let's stick to standard formulas for the tooth depth, but cap the outer radius at the prompt's value.
#   
#   Actually, let's just use the prompt's values directly for the sketch boundaries.
#   Outer Radius = 14.732 / 2 = 7.366 mm.
#   Pitch Radius = 12.7 / 2 = 6.35 mm.
#   Base Radius = 12.7 * cos(20) = 11.97 mm.
#   
#   Tooth Profile Sketch:
#   - Start at Center (0,0).
#   - Draw line to Base Circle (Radius 11.97).
#   - Draw Involute from Base Circle to Outer Circle (Radius 7.366).
#   - Draw line from Outer Circle back to Center? No, that's the other side of the tooth.
#   - We need the profile of ONE tooth.
#   - A tooth is bounded by two flanks.
#   - We will draw the profile of HALF a tooth (from center line to flank).
#   - Then we will use a Polar Pattern to create the full gear.
#   
#   Wait, if we pattern the half-tooth, we need to be careful with the pattern axis.
#   Better: Draw the full tooth profile (one side of the tooth, then the other side) in one sketch?
#   No, usually we draw the profile of one tooth (from valley to peak) and pattern it.
#   But the valley is not a straight line.
#   
#   Let's try this:
#   1. Create a sketch on the Pitch Circle.
#   2. Draw the Involute curve for one flank (from Base to Outer).
#   3. Draw the radial line from Center to the start of the involute (Base).
#   4. Draw the radial line from Center to the end of the involute (Outer).
#   5. This forms a sector.
#   6. We need to close the loop to make a closed shape for the Groove?
#      No, the Groove is subtractive. We can define the profile as an open curve if we use "ThroughAll" and the axis is correct?
#      No, PartDesign::Groove requires a closed profile or a specific setup.
#      Actually, for a revolution groove, the profile must be closed.
#      So we need to connect the end of the involute (Outer) to the start (Base) via the root circle?
#      No, the root circle is the bottom of the valley.
#      
#   Let's rethink the "Stock" geometry.
#   If we have a cylinder, and we cut teeth:
#   The profile of the cut (the groove) is:
#   - Start at Outer Diameter (Top of tooth).
#   - Go down the flank (Involute) to the Root Diameter.
#   - Go across the bottom of the valley (Chord or Arc) to the other flank.
#   - Go up the other flank (Involute) to the Outer Diameter.
#   
#   This is complex to sketch manually.
#   
#   Alternative: Build the gear as a solid (Pad) and then fillet the roots.
#   1. Sketch: Half-tooth profile (Center -> Base -> Involute -> Outer -> Center).
#      Wait, the tooth is symmetric.
#      Profile: Center -> Base (Line) -> Involute (Curve) -> Outer (Line) -> Center (Line).
#      This creates a shape that, when revolved, creates the teeth.
#      BUT, this leaves the valleys as sharp spikes at the Base Circle.
#      We need to cut the valleys to the Root Diameter.
#   
#   Let's go with the "Positive" approach (Pad the teeth) and then use a "Fillet" or "Groove" to clean up the roots.
#   Actually, the simplest way to get a "Stock" with teeth in FreeCAD PartDesign is:
#   1. Create a Cylinder (Blank).
#   2. Create a sketch of the tooth profile (Involute) on the Pitch Circle.
#   3. Use a "Groove" (Revolution) to cut the teeth.
#      The groove profile will be the "negative" of the tooth.
#      We need to define the groove profile as:
#      - Line from Outer Radius to Base Radius (Radial).
#      - Involute from Base Radius to Outer Radius.
#      - Line from Outer Radius to Center? No.
#      
#   Let's try a different strategy:
#   1. Create a sketch of the TOOTH PROFILE (one tooth, from valley to peak).
#      - Start at Root Radius (on the centerline).
#      - Go to Outer Radius (on the centerline).
#      - Draw the Involute flank.
#      - Draw the other flank.
#      - Close the loop.
#   2. Pad this profile 360 degrees.
#   3. This creates the gear.
#   4. The valleys will be at the Root Radius.
#   
#   How to draw the tooth profile?
#   - Center of sketch at (0,0).
#   - Tooth is symmetric around X-axis (or Y-axis). Let's
