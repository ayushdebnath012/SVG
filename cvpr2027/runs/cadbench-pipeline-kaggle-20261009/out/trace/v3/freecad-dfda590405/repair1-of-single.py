import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
P_ELbowCrossSectionLength = 40.39
P_ELbowCrossSectionWidth = 21.84
P_FullRevolutionAngle = 360.0
P_BilletOuterDiameter = 43.68
P_SemicircleArcRadius = 21.84
P_SemicircleCentralAngle = 180.0

# Edit Parameters
P_PipeInnerDiameter = 24.38
P_BoreOuterHeightAtElbowEnd = 16.7
P_BoreStepHeight = 16.07
P_BoreStepOffsetFromAxis = 20.04
P_BoreDiameterAtElbowFace = 33.4
P_SecondFaceBoreDiameter = 24.38
P_SecondFaceBoreArcCentralAngle = 180.0

# --- Helper Functions ---

def create_doc(name):
    """Creates a new FreeCAD document."""
    doc = App.newDocument(name)
    doc.Label = name
    return doc

def get_plane(doc, name):
    """Gets a standard plane object from the document."""
    return doc.getObject(name)

def create_sketch(body, name, plane_name, offset=0.0):
    """Creates a Sketcher::SketchObject attached to a plane."""
    plane = get_plane(doc, plane_name)
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane
    sketch.MapMode = "FlatFace"
    sketch.AttachmentOffset = offset
    sketch.ConstrainAuto = True
    sketch.ConstrainAuto2D = True
    return sketch

def add_line(sketch, p1, p2, is_constrained=True):
    """Adds a line segment to a sketch."""
    sketch.addGeometry(Part.LineSegment(p1, p2), is_constrained)

def add_circle(sketch, center, radius, is_constrained=True):
    """Adds a circle to a sketch."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constrained)

def add_constraint(sketch, constraint_type, *args):
    """Adds a constraint to a sketch."""
    sketch.addConstraint(constraint_type, *args)

def add_arc(sketch, center, radius, start_angle, end_angle, is_constrained=True):
    """Adds an arc to a sketch."""
    sketch.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), is_constrained)

def add_ellipse(sketch, center, major_axis, minor_axis, angle=0.0, is_constrained=True):
    """Adds an ellipse to a sketch."""
    sketch.addGeometry(Part.Ellipse(center, major_axis, minor_axis, angle), is_constrained)

def add_tangent_line(sketch, p1, p2, is_constrained=True):
    """Adds a line tangent to a circle at p1."""
    sketch.addGeometry(Part.LineSegment(p1, p2), is_constrained)

def add_tangent_circle(sketch, center, radius, is_constrained=True):
    """Adds a circle tangent to a line."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constrained)

def add_tangent_arc(sketch, center, radius, start_angle, end_angle, is_constrained=True):
    """Adds an arc tangent to a line."""
    sketch.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), is_constrained)

def add_tangent_ellipse(sketch, center, major_axis, minor_axis, angle=0.0, is_constrained=True):
    """Adds an ellipse tangent to a line."""
    sketch.addGeometry(Part.Ellipse(center, major_axis, minor_axis, angle), is_constrained)

def add_tangent_line_to_circle(sketch, circle, p1, p2, is_constrained=True):
    """Adds a line tangent to a circle at p1."""
    sketch.addGeometry(Part.LineSegment(p1, p2), is_constrained)

def add_tangent_circle_to_line(sketch, line, center, radius, is_constrained=True):
    """Adds a circle tangent to a line."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constrained)

def add_tangent_arc_to_line(sketch, line, center, radius, start_angle, end_angle, is_constrained=True):
    """Adds an arc tangent to a line."""
    sketch.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), is_constrained)

def add_tangent_ellipse_to_line(sketch, line, center, major_axis, minor_axis, angle=0.0, is_constrained=True):
    """Adds an ellipse tangent to a line."""
    sketch.addGeometry(Part.Ellipse(center, major_axis, minor_axis, angle), is_constrained)

def add_tangent_line_to_ellipse(sketch, ellipse, p1, p2, is_constrained=True):
    """Adds a line tangent to an ellipse at p1."""
    sketch.addGeometry(Part.LineSegment(p1, p2), is_constrained)

def add_tangent_circle_to_ellipse(sketch, ellipse, center, radius, is_constrained=True):
    """Adds a circle tangent to an ellipse."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constrained)

def add_tangent_arc_to_ellipse(sketch, ellipse, center, radius, start_angle, end_angle, is_constrained=True):
    """Adds an arc tangent to an ellipse."""
    sketch.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True):
    """Adds a line tangent to a line."""
    sketch.addGeometry(Part.LineSegment(line1, line2), is_constrained)

def add_tangent_circle_to_circle(sketch, circle1, circle2, is_constrained=True):
    """Adds a circle tangent to a circle."""
    sketch.addGeometry(Part.Circle(circle1, App.Vector(0, 0, 1), circle2), is_constrained)

def add_tangent_arc_to_arc(sketch, arc1, arc2, is_constrained=True):
    """Adds an arc tangent to an arc."""
    sketch.addGeometry(Part.Arc(arc1, App.Vector(0, 0, 1), arc2), is_constrained)

def add_tangent_ellipse_to_ellipse(sketch, ellipse1, ellipse2, is_constrained=True):
    """Adds an ellipse tangent to an ellipse."""
    sketch.addGeometry(Part.Ellipse(ellipse1, ellipse2), is_constrained)

def add_tangent_line_to_line(sketch, line1, line2, is_constrained=True
