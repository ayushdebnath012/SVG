import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("LegoBrick")

# --- Parameters ---
# We will store these in a VarSet object to keep the document clean and editable
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "lego_unit_size", "Dimensions", "Base unit size")
params.addProperty("App::PropertyLength", "lego_height", "Dimensions", "Height of the main block")
params.addProperty("App::PropertyLength", "lego_thickness", "Dimensions", "Thickness of the main block")
params.addProperty("App::PropertyInteger", "num_studs_rows", "Dimensions", "Rows of studs")
params.addProperty("App::PropertyInteger", "num_studs_columns", "Dimensions", "Columns of studs")
params.addProperty("App::PropertyLength", "studs_distance", "Dimensions", "Distance between stud centers")
params.addProperty("App::PropertyVector", "stud_center", "Dimensions", "Offset of stud grid center")
params.addProperty("App::PropertyLength", "stud_diameter", "Dimensions", "Diameter of a stud")
params.addProperty("App::PropertyLength", "stud_height", "Dimensions", "Height of a stud")
params.addProperty("App::PropertyVector", "tube_center", "Dimensions", "Offset of tube grid center")
params.addProperty("App::PropertyLength", "tube_outer_diameter", "Dimensions", "Outer diameter of a tube")
params.addProperty("App::PropertyLength", "tube_inner_diameter", "Dimensions", "Inner diameter of a tube")
params.addProperty("App::PropertyLength", "tube_distance", "Dimensions", "Distance between tube centers")

# Set default values as per prompt
params.lego_unit_size = 8.0
params.lego_height = 9.6
params.lego_thickness = 1.6
params.num_studs_rows = 2
params.num_studs_columns = 4
params.studs_distance = 8.0
params.stud_center = App.Vector(4.0, 4.0, 0.0)
params.stud_diameter = 4.8
params.stud_height = 1.6
params.tube_center = App.Vector(8.0, 8.0, 0.0)
params.tube_outer_diameter = 6.4
params.tube_inner_diameter = 4.8
params.tube_distance = 8.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Main Block Sketch ---
# Create the main rectangular block sketch
sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_MainBlock")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.ConstrainAuto = True
sketch_main.MapMode = "FlatFace"

# Define the rectangle based on unit size
# Width = num_studs_columns * unit_size
# Height = num_studs_rows * unit_size
width = params.num_studs_columns * params.lego_unit_size
height = params.num_studs_rows * params.lego_unit_size

# Add rectangle geometry
# We construct a rectangle centered at (0,0) for simplicity, then we will offset the studs later
# Actually, standard Lego studs are centered on the brick. Let's make the sketch centered.
# Points: (-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)
p1 = App.Vector(-width/2, -height/2, 0)
p2 = App.Vector(width/2, -height/2, 0)
p3 = App.Vector(width/2, height/2, 0)
p4 = App.Vector(-width/2, height/2, 0)

sketch_main.addGeometry(Part.LineSegment(p1, p2), False)
sketch_main.addGeometry(Part.LineSegment(p2, p3), False)
sketch_main.addGeometry(Part.LineSegment(p3, p4), False)
sketch_main.addGeometry(Part.LineSegment(p4, p1), False)

# Add constraints to make it a perfect rectangle
sketch_main.addConstraint(Sketcher.Constraint("Axis", 0, 1, 0, 1)) # Horizontal
sketch_main.addConstraint(Sketcher.Constraint("Axis", 1, 2, 1, 2)) # Horizontal
sketch_main.addConstraint(Sketcher.Constraint("Axis", 2, 3, 0, 1)) # Vertical
sketch_main.addConstraint(Sketcher.Constraint("Axis", 3, 0, 1, 2)) # Vertical
sketch_main.addConstraint(Sketcher.Constraint("Length", 0, 1, width))
sketch_main.addConstraint(Sketcher.Constraint("Length", 2, 3, height))
sketch_main.addConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 1, 2))
sketch_main.addConstraint(Sketcher.Constraint("Perpendicular", 1, 2, 2, 3))
sketch_main.addConstraint(Sketcher.Constraint("Perpendicular", 2, 3, 3, 0))
sketch_main.addConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1))

# --- Main Block Pad ---
pad_main = body.newObject("PartDesign::Pad", "Pad_MainBlock")
pad_main.Profile = sketch_main
pad_main.Length = params.lego_thickness
pad_main.Type = "Solid"

# --- Studs Sketch ---
# We need a sketch for the studs. We will create a sketch that contains circles.
# To make it parametric, we can use a pattern feature, but the prompt asks for sketches and features.
# A common approach for Lego studs is to sketch one stud and use a Polar/Linear pattern.
# However, the prompt specifies an MxN matrix. A Polar pattern is usually circular.
# We can use a Linear Pattern (Rectangular) if available, or create the sketch with all circles.
# Given the constraints of "PartDesign features", creating a sketch with all circles is the most robust way 
# to ensure the "MxN matrix" is respected without complex pattern logic that might fail on non-circular grids.
# Alternatively, we can sketch one stud and use a Linear Pattern. Let's try Linear Pattern.

# Sketch for a single stud
sketch_stud = body.newObject("Sketcher::SketchObject", "Sketch_Stud")
sketch_stud.Placement = App.Placement(App.Vector(0, 0, params.lego_thickness)) # On top of the block
sketch_stud.ConstrainAuto = True
sketch_stud.MapMode = "FlatFace"

# Add a circle for the stud
# Center at 0,0, radius = diameter/2
r_stud = params.stud_diameter / 2.0
sketch_stud.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_stud), False)

# Constraint: Center at origin
sketch_stud.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_stud.addConstraint(Sketcher.Constraint("Radius", 0, r_stud))

# --- Studs Pattern ---
# We will use a Linear Pattern to create the grid.
# Note: FreeCAD PartDesign Linear Pattern can take a sketch object.
# We need to define the pattern vector and count.
# The studs are arranged in a grid. We can do one direction then another, or use a 2D pattern if supported.
# Standard PartDesign::LinearPattern supports one direction. We will chain two patterns or use a specific setup.
# Actually, PartDesign::LinearPattern can handle multiple vectors if we set it up right, but typically it's one vector.
# Let's create a pattern for rows, then another for columns? No, that duplicates the feature.
# Better: Use a Linear Pattern with a vector that covers the whole grid? No, that's not how it works.
# Let's use a Linear Pattern for the columns (N), then another Linear Pattern for the rows (M) on the result?
# That creates a dependency chain.
# Alternative: Use a Polar Pattern? No, grid is rectangular.
# Let's use a Linear Pattern for the X-axis (columns) and then another Linear Pattern for the Y-axis (rows) on the first pattern's output.
# Wait, the prompt says "MxN matrix".
# Let's create the pattern for the columns first.
# Vector: (studs_distance, 0, 0)
# Count: num_studs_columns
# Offset: 0 (centered)

# However, to get a perfect grid, it's often easier to sketch the whole grid if the number of studs is small, 
# but for a script, patterns are better.
# Let's try a Linear Pattern for the columns.
pattern_cols = body.newObject("PartDesign::LinearPattern", "Pattern_Studs_Cols")
pattern_cols.Placement = App.Placement(App.Vector(0, 0, 0))
pattern_cols.Profile = sketch_stud
pattern_cols.Vector = (App.Vector(params.studs_distance, 0, 0), [""])
pattern_cols.Occurrences = params.num_studs_columns
pattern_cols.Centered = True

# Now pattern the rows on the result of the column pattern.
# We need to reference the last feature.
pattern_rows = body.newObject("PartDesign::LinearPattern", "Pattern_Studs_Rows")
pattern_rows.Placement = App.Placement(App.Vector(0, 0, 0))
pattern_rows.Profile = pattern_cols
pattern_rows.Vector = (App.Vector(0, params.studs_distance, 0), [""])
pattern_rows.Occurrences = params.num_studs_rows
pattern_rows.Centered = True

# --- Receiver Tubes Sketch ---
# Tubes are inside the brick.
# We will sketch one tube and pattern it.
sketch_tube = body.newObject("Sketcher::SketchObject", "Sketch_Tube")
sketch_tube.Placement = App.Placement(App.Vector(0, 0, 0)) # Inside the block
sketch_tube.ConstrainAuto = True
sketch_tube.MapMode = "FlatFace"

# Tube geometry: Annulus (Circle with hole)
r_outer = params.tube_outer_diameter / 2.0
r_inner = params.tube_inner_diameter / 2.0

# Outer circle
sketch_tube.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_outer), False)
# Inner circle (hole)
sketch_tube.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_inner), True) # True = subtract

# Constraints
sketch_tube.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_tube.addConstraint(Sketcher.Constraint("Radius", 0, r_outer))
sketch_tube.addConstraint(Sketcher.Constraint("Radius", 1, r_inner))

# --- Tubes Pattern ---
# Similar to studs, we need a grid.
# Pattern columns
pattern_tube_cols = body.newObject("PartDesign::LinearPattern", "Pattern_Tubes_Cols")
pattern_tube_cols.Placement = App.Placement(App.Vector(0, 0, 0))
pattern_tube_cols.Profile = sketch_tube
pattern_tube_cols.Vector = (App.Vector(params.tube_distance, 0, 0), [""])
pattern_tube_cols.Occurrences = params.num_studs_columns
pattern_tube_cols.Centered = True

# Pattern rows
pattern_tube_rows = body.newObject("PartDesign::LinearPattern", "Pattern_Tubes_Rows")
pattern_tube_rows.Placement = App.Placement(App.Vector(0, 0, 0))
pattern_tube_rows.Profile = pattern_tube_cols
pattern_tube_rows.Vector = (App.Vector(0, params.tube_distance, 0), [""])
pattern_tube_rows.Occurrences = params.num_studs_rows
pattern_tube_rows.Centered = True

# --- Fillets ---
# Lego bricks usually have a small fillet on the top edges of the main block, 
# and sometimes on the bottom. Let's add a fillet to the top edges of the main block.
# The top edges are the edges of the main block at height = lego_thickness.
# We can select the edges of the main block.
# Since we don't have direct access to edge indices easily without recomputing or complex selection,
# we can use the "Edge" property of the Pad feature if it exposes them, or select the sketch edges.
# However, PartDesign::Fillet works on edges of the body.
# Let's try to fillet the top edges of the main block.
# We can select the edges of the sketch that form the top perimeter.
# Actually, the Pad creates edges. Let's assume the top edges are the ones at Z = lego_thickness.
# We can select the edges of the sketch "Sketch_MainBlock" which are the top edges of the pad.
# But the Pad feature doesn't directly expose the resulting edges as a list of objects in the same way.
# A common trick is to fillet the edges of the sketch before padding? No, that changes the profile.
# We fillet the edges of the solid.
# Let's try to select the edges of the main block.
# We can use the "Edge" property of the Pad if we can reference it.
# Or, simpler: The prompt doesn't strictly require fillets, but "lego brick" implies them.
# Let's add a fillet to the top edges of the main block.
# We will select the edges of the main block.
# Since we can't easily get the edge indices programmatically without a GUI or complex logic,
# and the prompt asks for a script that builds the part, we will skip the automatic edge selection 
# for fillets to ensure the script runs headless without errors, OR we can try to select the sketch edges 
# if the fillet feature allows referencing sketch edges (it usually references body edges).
# Let's omit the fillet to ensure robustness, as selecting specific edges of a generated solid 
# in a headless script without a GUI is tricky. The core geometry (studs, tubes, block) is the priority.
# If I must include it, I would need to know the edge indices. Let's skip to guarantee the script works.
# Wait, I can try to fillet the edges of the sketch if I use a different approach, but standard Fillet is on Body edges.
# Let's skip fillets to ensure the script is 100% reliable in headless mode.

# --- Finalize ---
doc.recompute()

# Save the file
# The output path must be derived from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
