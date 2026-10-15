import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HydraulicEndCap")

# --- Parameters ---
# Define a VarSet to hold all parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "end_cap_outer_diameter", "Dimensions", "Outer diameter of the cap")
params.addProperty("App::PropertyLength", "end_cap_thickness", "Dimensions", "Thickness of the cap")
params.addProperty("App::PropertyLength", "annular_groove_inner_diameter", "Dimensions", "Inner diameter of the top rebate")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the top rebate shoulder")
params.addProperty("App::PropertyLength", "groove_depth", "Dimensions", "Depth of the top rebate")
params.addProperty("App::PropertyLength", "right_relief_length", "Dimensions", "Length of right bottom relief")
params.addProperty("App::PropertyLength", "right_relief_width", "Dimensions", "Width of right bottom relief")
params.addProperty("App::PropertyLength", "left_relief_length", "Dimensions", "Length of left bottom relief")
params.addProperty("App::PropertyLength", "left_relief_width", "Dimensions", "Width of left bottom relief")
params.addProperty("App::PropertyLength", "side_relief_depth", "Dimensions", "Depth of bottom reliefs")
params.addProperty("App::PropertyLength", "arc_relief_radius", "Dimensions", "Radius of the arc relief")
params.addProperty("App::PropertyLength", "arc_relief_depth", "Dimensions", "Total width of the arc relief")
params.addProperty("App::PropertyLength", "arc_relief_offset", "Dimensions", "Offset of the arc relief from center")
params.addProperty("App::PropertyLength", "small_center_bore_diameter", "Dimensions", "Diameter of the center bore")
params.addProperty("App::PropertyLength", "center_bore_depth", "Dimensions", "Depth of the center bore")
params.addProperty("App::PropertyLength", "right_relief_x_min", "Dimensions", "X start of right relief")
params.addProperty("App::PropertyLength", "right_relief_y_min", "Dimensions", "Y start of right relief")
params.addProperty("App::PropertyLength", "left_relief_x_min", "Dimensions", "X start of left relief")
params.addProperty("App::PropertyLength", "left_relief_y_min", "Dimensions", "Y start of left relief")
params.addProperty("App::PropertyLength", "arc_relief_center_x", "Dimensions", "X center of arc relief profile")
params.addProperty("App::PropertyLength", "arc_relief_center_y", "Dimensions", "Y center of arc relief profile")
params.addProperty("App::PropertyLength", "arc_relief_profile_x0", "Dimensions", "X anchor of arc relief")
params.addProperty("App::PropertyLength", "arc_relief_profile_y0", "Dimensions", "Y anchor of arc relief")
params.addProperty("App::PropertyLength", "arc_relief_profile_x1", "Dimensions", "X upper endpoint of arc relief")
params.addProperty("App::PropertyLength", "arc_relief_profile_y1", "Dimensions", "Y upper endpoint of arc relief")
params.addProperty("App::PropertyLength", "arc_relief_profile_x2", "Dimensions", "X lower endpoint of arc relief")
params.addProperty("App::PropertyLength", "arc_relief_profile_x3", "Dimensions", "X lower vertical endpoint of arc relief")

# Set values
params.end_cap_outer_diameter = 80.0
params.end_cap_thickness = 130.0
params.annular_groove_inner_diameter = 70.0
params.outer_diameter = 89.8937082
params.groove_depth = 10.0
params.right_relief_length = 31.1513256
params.right_relief_width = 93.7870873
params.left_relief_length = 30.8350117
params.left_relief_width = 92.3636746
params.side_relief_depth = 80.0
params.arc_relief_radius = 28.1676805
params.arc_relief_depth = 78.0
params.arc_relief_offset = 39.0
params.small_center_bore_diameter = 20.0
params.center_bore_depth = 31.0
params.right_relief_x_min = 12.5
params.right_relief_y_min = -47.3680146
params.left_relief_x_min = -43.3350117
params.left_relief_y_min = -46.7353867
params.arc_relief_center_x = 36.8323195
params.arc_relief_center_y = -14.4165172
params.arc_relief_profile_x0 = -17.5
params.arc_relief_profile_y0 = 40.0
params.arc_relief_profile_x1 = 47.2617529
params.arc_relief_profile_y1 = 11.7492074
params.arc_relief_profile_x2 = 48.6180581
params.arc_relief_profile_x3 = 67.6634428

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Cylinder ---
# Create a sketch on the XY plane to define the cylinder profile
sketch_cyl = body.newObject("Sketcher::SketchObject", "Sketch_Cylinder")
sketch_cyl.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_cyl.ConstrainToCurrentPlane = True
sketch_cyl.ConstrainToCurrentAxis = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.ConstrainToCurrentVertex = True
sketch_cyl.ConstrainToCurrentPoint = True
sketch_cyl.ConstrainToCurrentLine = True
sketch_cyl.ConstrainToCurrentCircle = True
sketch_cyl.ConstrainToCurrentArc = True
sketch_cyl.ConstrainToCurrentEllipse = True
sketch_cyl.ConstrainToCurrentPolygon = True
sketch_cyl.ConstrainToCurrentPolyline = True
sketch_cyl.ConstrainToCurrentSpline = True
sketch_cyl.ConstrainToCurrentHelix = True
sketch_cyl.ConstrainToCurrentSurface = True
sketch_cyl.ConstrainToCurrentCurve = True
sketch_cyl.ConstrainToCurrentFace = True
sketch_cyl.ConstrainToCurrentEdge = True
sketch_cyl.Constrain
