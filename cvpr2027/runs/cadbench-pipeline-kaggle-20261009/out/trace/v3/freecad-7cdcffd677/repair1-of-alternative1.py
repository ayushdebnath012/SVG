import FreeCAD as App
import Part
from pathlib import Path

# Initialize the document
doc = App.newDocument("PartHolder")

# 1. Create the Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# 2. Create Parameters (based on drawing dimensions)
params = body.newObject("App::Parameter", "Params")
params.addProperty("App::PropertyLength", "OverallWidth", "Dimensions", "Main overall length")
params.addProperty("App::PropertyLength", "OverallHeight", "Dimensions", "Main overall height")
params.addProperty("App::PropertyLength", "MountingHeight", "Dimensions", "Height of mounting bosses")
params.addProperty("App::PropertyLength", "ShaftHeight", "Dimensions", "Height of shaft section")
params.addProperty("App::PropertyLength", "ShaftDiameter", "Dimensions", "Diameter of main shaft")
params.addProperty("App::PropertyLength", "BossDiameter", "Dimensions", "Diameter of mounting bosses")
params.addProperty("App::PropertyLength", "BossRadius", "Dimensions", "Radius of mounting boss base")
params.addProperty("App::PropertyLength", "BossFlangeHeight", "Dimensions", "Height of mounting boss flange")
params.addProperty("App::PropertyLength", "BossFlangeWidth", "Dimensions", "Width of mounting boss flange")
params.addProperty("App::PropertyLength", "BaseLength", "Dimensions", "Length of bottom base")
params.addProperty("App::PropertyLength", "BaseWidth", "Dimensions", "Width of bottom base")
params.addProperty("App::PropertyLength", "BaseThickness", "Dimensions", "Thickness of bottom base")
params.addProperty("App::PropertyLength", "CenterDist", "Dimensions", "Distance between center of bosses")
params.addProperty("App::PropertyLength", "ShaftDist", "Dimensions", "Distance from boss center to shaft center")
params.addProperty("App::PropertyLength", "BossOffset", "Dimensions", "Offset from boss center to mounting hole")

# Set values from the drawing
# Overall: 33 (L) x 10.5 (W)
# Bosses: 2x Ø7 (flange 11.5), Ø5.5 (boss), Ø3.5 (hole)
# Shaft: Ø4 (shaft), 3.5 (flange)
# Base: 24.5 (L) x 10.5 (W) x 1.5 (T)
# Dimensions:
params.OverallWidth = 33.0
params.OverallHeight = 10.5
params.MountingHeight = 11.5
params.ShaftHeight = 10.5
params.ShaftDiameter = 4.0
params.BossDiameter = 5.5
params.BossRadius = 3.5
params.BossFlangeHeight = 2.0
params.BossFlangeWidth = 11.5
params.BaseLength = 24.5
params.BaseWidth = 10.5
params.BaseThickness = 1.5
params.CenterDist = 24.5
params.ShaftDist = 1.5
params.BossOffset = 3.5

# 3. Create the Main Profile Sketch (Front View - XZ Plane)
sketch = body.newObject("Sketcher::SketchObject", "FrontSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
sketch.ConstraintNumbers = 1000
sketch.Plane = "XY_Plane"
sketch.TechDraw_Plane = "XY_Plane"

# Main outer profile
# Bottom edge (Y=0)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.OverallWidth/2, 0, 0), App.Vector(params.OverallWidth/2, 0, 0)), False)
# Top edge (Y=10.5)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.OverallWidth/2, params.OverallHeight, 0), App.Vector(params.OverallWidth/2, params.OverallHeight, 0)), False)
# Left side (X=-16.5)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.OverallWidth/2, 0, 0), App.Vector(-params.OverallWidth/2, params.OverallHeight, 0)), False)
# Right side (X=16.5)
sketch.addGeometry(Part.LineSegment(App.Vector(params.OverallWidth/2, 0, 0), App.Vector(params.OverallWidth/2, params.OverallHeight, 0)), False)

# Bottom Base Profile (Y=0 to Y=1.5)
# Bottom base edges
sketch.addGeometry(Part.LineSegment(App.Vector(-params.BaseLength/2, 0, 0), App.Vector(-params.BaseLength/2, params.BaseThickness, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.BaseLength/2, params.BaseThickness, 0), App.Vector(-params.BaseLength/2, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.BaseLength/2, params.BaseThickness, 0), App.Vector(params.BaseLength/2, params.BaseThickness, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.BaseLength/2, params.BaseThickness, 0), App.Vector(params.BaseLength/2, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.BaseLength/2, 0, 0), App.Vector(-params.BaseLength/2, 0, 0)), False)

# Mounting Bosses Profile (Y=1.5 to Y=11.5)
# Boss Centers at X = -12 and X = 12 (CenterDist = 24.5)
# Left Boss
sketch.addGeometry(Part.LineSegment(App.Vector(-params.CenterDist/2 - params.BossOffset, params.MountingHeight, 0), App.Vector(-params.CenterDist/2 - params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.CenterDist/2 - params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0), App.Vector(-params.CenterDist/2 - params.BossOffset, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.CenterDist/2 - params.BossOffset, 0, 0), App.Vector(-params.CenterDist/2 + params.BossOffset, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.CenterDist/2 + params.BossOffset, 0, 0), App.Vector(-params.CenterDist/2 + params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.CenterDist/2 + params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0), App.Vector(-params.CenterDist/2 + params.BossOffset, params.MountingHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.CenterDist/2 + params.BossOffset, params.MountingHeight, 0), App.Vector(-params.CenterDist/2 - params.BossOffset, params.MountingHeight, 0)), False)

# Right Boss
sketch.addGeometry(Part.LineSegment(App.Vector(params.CenterDist/2 - params.BossOffset, params.MountingHeight, 0), App.Vector(params.CenterDist/2 - params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.CenterDist/2 - params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0), App.Vector(params.CenterDist/2 - params.BossOffset, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.CenterDist/2 - params.BossOffset, 0, 0), App.Vector(params.CenterDist/2 + params.BossOffset, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.CenterDist/2 + params.BossOffset, 0, 0), App.Vector(params.CenterDist/2 + params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.CenterDist/2 + params.BossOffset, params.MountingHeight - params.BossFlangeHeight, 0), App.Vector(params.CenterDist/2 + params.BossOffset, params.MountingHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.CenterDist/2 + params.BossOffset, params.MountingHeight, 0), App.Vector(params.CenterDist/2 - params.BossOffset, params.MountingHeight, 0)), False)

# Main Shaft Profile (Y=1.5 to Y=10.5)
# Shaft Center at X=0
sketch.addGeometry(Part.LineSegment(App.Vector(-params.ShaftDist, params.ShaftHeight, 0), App.Vector(-params.ShaftDist, params.ShaftHeight - params.ShaftFlangeHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.ShaftDist, params.ShaftHeight - params.ShaftFlangeHeight, 0), App.Vector(-params.ShaftDist, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.ShaftDist, 0, 0), App.Vector(params.ShaftDist, 0, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.ShaftDist, 0, 0), App.Vector(params.ShaftDist, params.ShaftHeight - params.ShaftFlangeHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.ShaftDist, params.ShaftHeight - params.ShaftFlangeHeight, 0), App.Vector(params.ShaftDist, params.ShaftHeight, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.ShaftDist, params.ShaftHeight, 0), App.Vector(-params.ShaftDist, params.ShaftHeight, 0)), False)

# Add constraints to the sketch
# Horizontal lines
sketch.addConstraint(Sketcher.Constraint("Axis", 0, "X", 1, "X", 2, "X", 3, "X", 4, "X"))
sketch.addConstraint(Sketcher.Constraint("Axis", 5, "Y", 6, "Y", 7, "Y", 8, "Y", 9, "Y"))
sketch.addConstraint(Sketcher.Constraint("Axis", 10, "Z", 11, "Z", 12, "Z", 13, "Z", 14, "Z"))
sketch.addConstraint(Sketcher.Constraint("Axis", 15, "Y", 16, "Y", 17, "Y", 18, "Y", 19, "Y"))

# Vertical lines
sketch.addConstraint(Sketcher.Constraint("Axis", 20, "X", 21, "X", 22, "X", 23, "X"))
sketch.addConstraint(Sketcher.Constraint("Axis", 24, "X", 25, "X", 26, "X", 27, "X"))
sketch.addConstraint(Sketcher.Constraint("Axis", 28, "X", 29, "X", 30, "X", 31, "X"))
sketch.addConstraint(Sketcher.Constraint("Axis", 32, "X", 33, "X", 34, "X", 35, "X"))

# Length constraints
sketch.addConstraint(Sketcher.Constraint("Length", 0, "Y", 3, "Y", 3, "Y", 10, "Y"))
sketch.addConstraint(Sketcher.Constraint("Length", 1, "X", 2, "X", 2, "X", 11, "X"))
sketch.addConstraint(Sketcher.Constraint("Length", 4, "Y", 5, "Y", 5, "Y", 12, "Y"))
sketch.addConstraint(Sketcher.Constraint("Length", 6, "X", 7, "X", 7, "X", 13, "X"))
sketch.addConstraint(Sketcher.Constraint("Length", 8, "Y", 9, "Y", 9, "Y", 14, "Y"))

# Horizontal distances
sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, "X", 3, "X", 3, "X", 10, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 11, "X", 12, "X", 12, "X", 11, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 13, "X", 14, "X", 14, "X", 13, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 15, "X", 16, "X", 16, "X", 15, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 17, "X", 18, "X", 18, "X", 17, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 19, "X", 20, "X", 20, "X", 19, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 21, "X", 22, "X", 22, "X", 21, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 23, "X", 24, "X", 24, "X", 23, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 25, "X", 26, "X", 26, "X", 25, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 27, "X", 28, "X", 28, "X", 27, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 29, "X", 30, "X", 30, "X", 29, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 31, "X", 32, "X", 32, "X", 31, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 33, "X", 34, "X", 34, "X", 33, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 35, "X", 36, "X", 36, "X", 35, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 37, "X", 38, "X", 38, "X", 37, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 39, "X", 40, "X", 40, "X", 39, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 41, "X", 42, "X", 42, "X", 41, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 43, "X", 44, "X", 44, "X", 43, "X"))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 45, "X", 46, "X", 46, "X", 45, "X"))

# Vertical distances
sketch.addConstraint(Sketcher.Constraint("Vertical", 0, "Y", 1, "Y", 1, "Y", 0, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 2, "Y", 3, "Y", 3, "Y", 2, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 4, "Y", 5, "Y", 5, "Y", 4, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 6, "Y", 7, "Y", 7, "Y", 6, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 8, "Y", 9, "Y", 9, "Y", 8, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 10, "Y", 11, "Y", 11, "Y", 10, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 12, "Y", 13, "Y", 13, "Y", 12, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 14, "Y", 15, "Y", 15, "Y", 14, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 16, "Y", 17, "Y", 17, "Y", 16, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 18, "Y", 19, "Y", 19, "Y", 18, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 20, "Y", 21, "Y", 21, "Y", 20, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 22, "Y", 23, "Y", 23, "Y", 22, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 24, "Y", 25, "Y", 25, "Y", 24, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 26, "Y", 27, "Y", 27, "Y", 26, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 28, "Y", 29, "Y", 29, "Y", 28, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 30, "Y", 31, "Y", 31, "Y", 30, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 32, "Y", 33, "Y", 33, "Y", 32, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 34, "Y", 35, "Y", 35, "Y", 34, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 36, "Y", 37, "Y", 37, "Y", 36, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 38, "Y", 39, "Y", 39, "Y", 38, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 40, "Y", 41, "Y", 41, "Y", 40, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 42, "Y", 43, "Y", 43, "Y", 42, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 44, "Y", 45, "Y", 45, "Y", 44, "Y"))
sketch.addConstraint(Sketcher.Constraint("Vertical", 46, "Y", 47, "Y", 47, "Y", 46, "Y"))

# 4. Create the Main Pad (extrude the profile)
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = params.OverallHeight
pad.Type = "Solid"
pad.Midplane = False
pad.Reversed = False
pad.setExpression("Length", "Params.OverallHeight")

# 5. Create the Base Pad (extrude the base profile)
base_pad = body.newObject("PartDesign::Pad", "BasePad")
base_pad.Profile = sketch
base_pad.Length = params.BaseThickness
base_pad.Type = "Solid"
base_pad.Midplane = False
base_pad.Reversed = False
base_pad.setExpression("Length", "Params.BaseThickness")

# 6. Create the Bosses (using Revolution)
# Left Boss
left_boss = body.newObject("PartDesign::Revolution", "LeftBoss")
left_boss.Profile = sketch
left_boss.ReferenceAxis = (doc.getObject("Z_Axis"), [""])
left_boss.Angle = 360.0
left_boss.Type = "Solid"
left_boss.setExpression("Angle", "360")

# Right Boss
right_boss = body.newObject("PartDesign::Revolution", "RightBoss")
right_boss.Profile = sketch
right_boss.ReferenceAxis = (doc.getObject("Z_Axis"), [""])
right_boss.Angle = 360.0
right_boss.Type = "Solid"
right_boss.setExpression("Angle", "360")

# 7. Create the Shaft (using Revolution)
shaft = body.newObject("PartDesign::Revolution", "Shaft")
shaft.Profile = sketch
shaft.ReferenceAxis = (doc.getObject("Z_Axis"), [""])
shaft.Angle = 360.0
shaft.Type = "Solid"
shaft.setExpression("Angle", "360")

# 8. Create the Mounting Holes (using Pocket)
# Left Boss Hole
left_hole = body.newObject("PartDesign::Pocket", "LeftBossHole")
left_hole.Profile = sketch
left_hole.Type = "ThroughAll"
left_hole.setExpression("Length", "Params.MountingHeight")

# Right Boss Hole
right_hole = body.newObject("PartDesign::Pocket", "RightBossHole")
right_hole.Profile = sketch
right_hole.Type = "ThroughAll"
right_hole.setExpression("Length", "Params.MountingHeight")

# 9. Create the Shaft Hole (using Pocket)
shaft_hole = body.newObject("PartDesign::Pocket", "ShaftHole")
shaft_hole.Profile = sketch
shaft_hole.Type = "ThroughAll"
shaft_hole.setExpression("Length", "Params.ShaftHeight")

# 10. Create the Base Holes (using Pocket)
# Left Base Hole
left_base_hole = body.newObject("PartDesign::Pocket", "LeftBaseHole")
left_base_hole.Profile = sketch
left_base_hole.Type = "ThroughAll"
left_base_hole.setExpression("Length", "Params.BaseThickness")

# Right Base Hole
right_base_hole = body.newObject("PartDesign::Pocket", "RightBaseHole")
right_base_hole.Profile = sketch
right_base_hole.Type = "ThroughAll"
right_base_hole.setExpression("Length", "Params.BaseThickness")

# 11. Create the Fillets (using Fillet)
# Main outer fillets
main_fillet = body.newObject("PartDesign::Fillet", "MainFillet")
main_fillet.Base = (pad, ["Edge1"])
main_fillet.Radius = 1.0
main_fillet.setExpression("Radius", "1.0")

# 12. Create the Chamfers (using Chamfer)
# Main outer chamfers
main_chamfer = body.newObject("PartDesign::Chamfer", "MainChamfer")
main_chamfer.Base = (pad, ["Edge1"])
main_chamfer.Size = 0.5
main_chamfer.setExpression("Size", "0.5")

# 13. Recompute the document
doc.recompute()

# 14. Save the document
doc.saveAs(str(Path(__file__).resolve().with_suffix(".FCStd")))
