from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# Create a new document
doc = App.newDocument("WireSafetyLanyard")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the lanyard")
params.addProperty("App::PropertyLength", "top_loop_width", "Dimensions", "Width of the top loop")
params.addProperty("App::PropertyLength", "top_loop_height", "Dimensions", "Height of the top loop")
params.addProperty("App::PropertyLength", "neck_width", "Dimensions", "Width of the neck section")
params.addProperty("App::PropertyLength", "neck_height", "Dimensions", "Height of the neck section")
params.addProperty("App::PropertyLength", "body_width", "Dimensions", "Width of the main body")
params.addProperty("App::PropertyLength", "body_height", "Dimensions", "Height of the main body")
params.addProperty("App::PropertyLength", "bottom_width", "Dimensions", "Width of the bottom section")
params.addProperty("App::PropertyLength", "bottom_height", "Dimensions", "Height of the bottom section")
params.addProperty("App::PropertyLength", "loop_radius", "Dimensions", "Radius of the top loop")
params.addProperty("App::PropertyLength", "neck_radius", "Dimensions", "Radius of the neck curve")
params.addProperty("App::PropertyLength", "body_radius", "Dimensions", "Radius of the body curve")
params.addProperty("App::PropertyLength", "bottom_radius", "Dimensions", "Radius of the bottom curve")
params.addProperty("App::PropertyLength", "clip_width", "Dimensions", "Width of the clip")
params.addProperty("App::PropertyLength", "clip_height", "Dimensions", "Height of the clip")
params.addProperty("App::PropertyLength", "clip_radius", "Dimensions", "Radius of the clip curve")
params.addProperty("App::PropertyLength", "hole_diameter", "Dimensions", "Diameter of the hole")
params.addProperty("App::PropertyLength", "hole_position", "Dimensions", "Position of the hole from the top")
params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Radius of the fillets")
params.addProperty("App::PropertyLength", "chamfer_size", "Dimensions", "Size of the chamfers")

# Set the dimensions based on the drawing
params.overall_height = 105.0
params.top_loop_width = 33.07
params.top_loop_height = 62.88
params.neck_width = 13.17
params.neck_height = 39.79
params.body_width = 24.93
params.body_height = 90.58
params.bottom_width = 27.5
params.bottom_height = 10.39
params.loop_radius = 16.5
params.neck_radius = 8.0
params.body_radius = 17.5
params.bottom_radius = 12.5
params.clip_width = 10.2
params.clip_height = 15.0
params.clip_radius = 5.0
params.hole_diameter = 4.0
params.hole_position = 10.0
params.fillet_radius = 2.0
params.chamfer_size = 1.0

# Create the main sketch
sketch = body.newObject("Sketcher::SketchObject", "MainSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.ConstrainSymmetric = True
sketch.ConstrainHorizontal = True
sketch.ConstrainVertical = True
sketch.ConstrainHorizontalXY = True
sketch.ConstrainVerticalXY = True
sketch.ConstrainHorizontalXZ = True
sketch.ConstrainVerticalXZ = True
sketch.ConstrainHorizontalYZ = True
sketch.ConstrainVerticalYZ = True
sketch.ConstrainSymmetricXY = True
sketch.ConstrainSymmetricXZ = True
sketch.ConstrainSymmetricYZ = True
sketch.ConstrainCoincident = True
sketch.ConstrainParallel = True
sketch.ConstrainPerpendicular = True
sketch.ConstrainTangent = True
sketch.ConstrainEqualLength = True
sketch.ConstrainEqualRadius = True
sketch.ConstrainEqualConstraint = True
sketch.ConstrainPointOnObject = True
sketch.ConstrainPointOnLine = True
sketch.ConstrainPointOnCircle = True
sketch.ConstrainPointOnArc = True
sketch.ConstrainPointOnEllipse = True
sketch.ConstrainPointOnHyperbola = True
sketch.ConstrainPointOnParabola = True
sketch.ConstrainPointOnSpline = True
sketch.ConstrainPointOnPolygon = True
sketch.ConstrainPointOnPolyline = True
sketch.ConstrainPointOnCurve = True
sketch.ConstrainPointOnSurface = True
sketch.ConstrainPointOnFace = True
sketch.ConstrainPointOnEdge = True
sketch.ConstrainPointOnVertex = True
sketch.ConstrainPointOnPoint = True
sketch.ConstrainPointOnLineSegment = True
sketch.ConstrainPointOnArcSegment = True
sketch.ConstrainPointOnCircleSegment = True
sketch.ConstrainPointOnEllipseSegment = True
sketch.ConstrainPointOnHyperbolaSegment = True
sketch.ConstrainPointOnParabolaSegment = True
sketch.ConstrainPointOnSplineSegment = True
sketch.ConstrainPointOnPolygonSegment = True
sketch.ConstrainPointOnPolylineSegment = True
sketch.ConstrainPointOnCurveSegment = True
sketch.ConstrainPointOnSurfaceSegment = True
sketch.ConstrainPointOnFaceSegment = True
sketch.ConstrainPointOnEdgeSegment = True
sketch.ConstrainPointOnVertexSegment = True
sketch.ConstrainPointOnPointSegment = True
sketch.ConstrainPointOnLineSegmentSegment = True
sketch.ConstrainPointOnArcSegmentSegment = True
sketch.ConstrainPointOnCircleSegmentSegment = True
sketch.ConstrainPointOnEllipseSegmentSegment = True
sketch.ConstrainPointOnHyperbolaSegmentSegment = True
sketch.ConstrainPointOnParabolaSegmentSegment = True
sketch.ConstrainPointOnSplineSegmentSegment = True
sketch.ConstrainPointOnPolygonSegmentSegment = True
sketch.ConstrainPointOnPolylineSegmentSegment = True
sketch.ConstrainPointOnCurveSegmentSegment = True
sketch.ConstrainPointOnSurfaceSegmentSegment = True
sketch.ConstrainPointOnFaceSegmentSegment = True
sketch.ConstrainPointOnEdgeSegmentSegment = True
sketch.ConstrainPointOnVertexSegmentSegment = True
sketch.ConstrainPointOnPointSegmentSegment = True

# Add the main profile to the sketch
# Top loop
sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.loop_radius), False)
# Neck section
sketch.addGeometry(Part.LineSegment(App.Vector(-params.neck_width/2, params.top_loop_height, 0), App.Vector(params.neck_width/2, params.top_loop_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.neck_width/2, params.top_loop_height, 0), App.Vector(params.neck_width/2, params.top_loop_height - params.neck_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(params.neck_width/2, params.top_loop_height - params.neck_height, 0), App.Vector(-params.neck_width/2, params.top_loop_height - params.neck_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.neck_width/2, params.top_loop_height - params.neck_height, 0), App.Vector(-params.neck_width/2, params.top_loop_height, 0)), False)
# Body section
sketch.addGeometry(Part.LineSegment(App.Vector(-params.neck_width/2, params.top_loop_height - params.neck_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height - params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height - params.bottom_height, 0), App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height - params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height - params.bottom_height, 0), App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0), App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0), App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.bottom_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height + params.bottom_height + params.bottom_height, 0), App.Vector(-params.body_width/2, params.top_loop_height - params.neck_height - params.body_height +
