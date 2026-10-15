import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("TaperPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Define parameters as properties on the Body to ensure they are editable and named.
# We use expressions in the feature definitions to link to these parameters.

# Small end diameter (at the start of the taper section)
body.addProperty("App::PropertyLength", "p_small_dia", "Parameters", "Small End Diameter")
body.p_small_dia = 0.6

# Overall length
body.addProperty("App::PropertyLength", "p_length", "Parameters", "Overall Length")
body.p_length = 4.0

# Rounded end height (axial length of the rounded tip)
body.addProperty("App::PropertyLength", "p_round_height", "Parameters", "Rounded Tip Height")
body.p_round_height = 0.08

# Taper ratio (slope per unit length)
body.addProperty("App::PropertyLength", "p_taper_ratio", "Parameters", "Taper Ratio")
body.p_taper_ratio = 0.02

# --- Sketch 1: Base Profile (Side View) ---
# We create a sketch on the XY plane to define the profile of the pin.
# The profile will consist of:
# 1. A rounded tip at the bottom.
# 2. A tapered section going up to the large diameter.
# 3. A flat top section.

sketch_profile = body.newObject("Sketcher::SketchObject", "Sketch_Profile")
# Correct placement syntax for FreeCAD 1.1
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Support = (doc.getObject("XY_Plane"), [])
sketch_profile.ConstrainAuto = True
sketch_profile.MapMode = "FlatFace"

# Calculate derived values for geometry construction
# Tip radius: Assuming the "rounded section" is a hemisphere of the given height.
# If height = 0.08, then radius = 0.04.
r_tip = body.p_round_height.Value / 2.0

# Taper section starts at Z = r_tip.
# Diameter at start of taper = p_small_dia.
# Length of taper section = Total Length - Tip Height.
L_taper = body.p_length.Value - body.p_round_height.Value

# Diameter increase = Length * Slope
delta_D = L_taper * body.p_taper_ratio.Value
D_large = body.p_small_dia.Value + delta_D
R_large = D_large / 2.0
R_small_taper = body.p_small_dia.Value / 2.0

# --- Construct Geometry ---
# 1. Tip Circle (Bottom)
# Center at (0, 0), Radius = r_tip.
circle_tip = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_tip)
sketch_profile.addGeometry(circle_tip, False)

# 2. Line from top of tip to start of taper (Shoulder)
# Start: (r_tip, r_tip)
# End: (R_small_taper, r_tip)
line_shoulder = Part.LineSegment(App.Vector(r_tip, r_tip, 0), App.Vector(R_small_taper, r_tip, 0))
sketch_profile.addGeometry(line_shoulder, False)

# 3. Taper Line
# Start: (R_small_taper, r_tip)
# End: (R_large, p_length)
line_taper = Part.LineSegment(App.Vector(R_small_taper, r_tip, 0), App.Vector(R_large, body.p_length.Value, 0))
sketch_profile.addGeometry(line_taper, False)

# 4. Top Line (Center to Large End)
# Start: (R_large, p_length)
# End: (0, p_length)
line_top = Part.LineSegment(App.Vector(R_large, body.p_length.Value, 0), App.Vector(0, body.p_length.Value, 0))
sketch_profile.addGeometry(line_top, False)

# 5. Bottom Line (Center to Tip Center)
# Start: (0, p_length)
# End: (0, 0)
line_bottom = Part.LineSegment(App.Vector(0, body.p_length.Value, 0), App.Vector(0, 0, 0))
sketch_profile.addGeometry(line_bottom, False)

# --- Constraints ---
# Constrain the lines to meet at the circle and each other.
# We need to identify the geometry indices.
# Let's add constraints manually to ensure robustness.

# Get geometry indices
geom_indices = sketch_profile.Geometry
# 0: Circle Tip
# 1: Line Shoulder
# 2: Line Taper
# 3: Line Top
# 4: Line Bottom

# Constraint: Coincident - Top of Tip Circle (0, 0.08) with Start of Shoulder Line
# Circle point 0, 2 (top) coincident with Line 1, 0 (start)
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 0))

# Constraint: Coincident - End of Shoulder Line with Start of Taper Line
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 2, 0))

# Constraint: Coincident - End of Taper Line with Start of Top Line
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 2, 1, 3, 0))

# Constraint: Coincident - End of Top Line with Start of Bottom Line
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 3, 1, 4, 0))

# Constraint: Coincident - End of Bottom Line with Center of Tip Circle
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 4, 1, 0, 0))

# Constraint: Horizontal - Shoulder Line
sketch_profile.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))

# Constraint: Vertical - Bottom Line
sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 4, 0))

# Constraint: Vertical - Top Line
sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 3, 0))

# --- Pad Feature ---
# Extrude the profile along the Z axis.
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch_profile
pad.Length = body.p_length.Value
pad.Midplane = False
pad.Reversed = False

# --- Save ---
# Save the document next to the script file.
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.recompute()
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
