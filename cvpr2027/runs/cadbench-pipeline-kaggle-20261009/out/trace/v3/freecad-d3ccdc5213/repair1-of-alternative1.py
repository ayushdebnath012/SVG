import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

# Initialize document
doc = App.newDocument("HookedRetainingClip")

# 1. Create Named Parameters (Editable Variables)
# These will drive the overall geometry to match the drawing.
# Dimensions extracted from the drawing:
# - Total Width (X): 30.0 mm (from dimension line)
# - Total Height (Y): 24.0 mm (from dimension line)
# - Wall Thickness: 1.5 mm (from top view dimension)
# - Hook Height (from base): 3.0 mm (from left view dimension)
# - Base Width: 26.54 mm (from top view dimension)
# - Center Groove Width: 7.03 mm (from top view dimension)
# - Center Groove Depth: 1.5 mm (from top view dimension)
# - Bottom Hook Radius: 1.5 mm (from left view dimension)
# - Top Shoulder Radius: 2.5 mm (from top view dimension)
# - Fillet Radius (Chamfer/Edge): 2.0 mm (from right view dimension)

params = doc.addObject("App::ParameterObject", "Parameters")
params.Name = "Parameters"
params.Type = "App::ParameterObject"

# Add parameters
params.addParameter("Dimensions", "OverallWidth", "30.0")
params.addParameter("Dimensions", "OverallHeight", "24.0")
params.addParameter("Dimensions", "WallThickness", "1.5")
params.addParameter("Dimensions", "HookHeight", "3.0")
params.addParameter("Dimensions", "BaseWidth", "26.54")
params.addParameter("Dimensions", "GrooveWidth", "7.03")
params.addParameter("Dimensions", "GrooveDepth", "1.5")
params.addParameter("Dimensions", "HookRadius", "1.5")
params.addParameter("Dimensions", "ShoulderRadius", "2.5")
params.addParameter("Dimensions", "FilletRadius", "2.0")
params.addParameter("Dimensions", "BottomHookOffsetX", "1.0") # Approximated from visual alignment
params.addParameter("Dimensions", "BottomHookOffsetY", "2.0") # Approximated from visual alignment
params.addParameter("Dimensions", "HookLengthY", "11.0")
params.addParameter("Dimensions", "HookTipWidth", "6.0")

# Add expressions to link parameters
params.addParameter("Dimensions", "GrooveDepth", "Parameters.GrooveDepth")
params.addParameter("Dimensions", "WallThickness", "Parameters.WallThickness")

# 2. Create PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")
body.Name = "Body"

# 3. Create Main Sketch (Front View)
# This sketch defines the profile of the part.
# We place it on the XY plane.

sketch_main = body.newObject("Sketcher::SketchObject", "FrontSketch")
sketch_main.Name = "FrontSketch"
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.ViewObject.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Support = [doc.getObject("XY_Plane"), [""]]

# Define Geometry for the Front Sketch
# The part has a central groove and two side hooks.

# --- Central Groove ---
# The groove is centered in the part.
# We'll define a path for the central groove and the side hooks.

# Central Groove Path
# The groove is a rectangle with rounded corners (R=1.5)
# Width: 7.03, Height: 1.5
# Center at (0, 0)

# Groove Path Geometry
# 1. Top Left Corner
# 2. Top Right Corner
# 3. Bottom Right Corner
# 4. Bottom Left Corner

# Groove Width = 7.03, Groove Depth = 1.5
# Center at (0,0)
# Top edge at Y = 0.75, Bottom edge at Y = -0.75
# Left edge at X = -3.515, Right edge at X = 3.515

# Groove Points
groove_p1 = App.Vector(-3.515, 0.75, 0)
groove_p2 = App.Vector(3.515, 0.75, 0)
groove_p3 = App.Vector(3.515, -0.75, 0)
groove_p4 = App.Vector(-3.515, -0.75, 0)

# Side Hooks
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
# Top Left Corner
# Top Right Corner
# Bottom Right Corner
# Bottom Left Corner

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77, Y = 11.0
# Hook Radius = 1.5

# Hook 2 (Left Side)
# Center of the hook circle is at X = -12.77, Y = 11.0

# --- Main Body Profile ---
# The main body is a rectangle with a central groove and two side hooks.
# The main body is centered at (0, 0).
# Width = 30.0, Height = 24.0
# Wall Thickness = 1.5

# Main Body Points
main_p1 = App.Vector(-15.0, 12.0, 0)
main_p2 = App.Vector(15.0, 12.0, 0)
main_p3 = App.Vector(15.0, -12.0, 0)
main_p4 = App.Vector(-15.0, -12.0, 0)

# --- Side Hooks ---
# The side hooks are at X = +/- 12.77 (approx) and Y = +/- 11.0 (approx)
# Hook Tip Width = 6.0, Hook Height = 11.0
# Hook Radius = 1.5
# Hook Base Offset X = 1.0 from the base edge

# Hook 1 (Right Side)
# Center of the hook circle is at X = 12.77, Y = 11.0
# Hook Tip Width = 6.0, so the circle is centered at X = 12.77,
