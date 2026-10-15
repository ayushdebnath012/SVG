import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("DiscSpring")
    
    # Create the main Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Define named parameters for the disc spring
    params = body.newObject("App::VarSet", "Parameters")
    
    # Key parameters as specified
    params.addProperty("App::PropertyLength", "outside_diameter", "Dimensions", "Outer diameter")
    params.outside_diameter = 8.0
    
    params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter")
    params.inner_diameter = 4.2
    
    params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height")
    params.overall_height = 0.6
    
    params.addProperty("App::PropertyLength", "thickness", "Dimensions", "Material thickness")
    params.thickness = 0.4
    
    # Derived parameter: cone_height
    params.addProperty("App::PropertyLength", "cone_height", "Dimensions", "Calculated cone height")
    params.cone_height = App.Quantity(params.overall_height - params.thickness)

    # --- Sketch 1: Outer Profile (Side View) ---
    # We define the profile in the XZ plane (Side view) to create the conical shape via Revolution.
    # The sketch will be placed on the XZ plane.
    sketch_outer = body.newObject("Sketcher::SketchObject", "SketchOuter")
    sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_outer.Support = "XZ_Plane"
    sketch_outer.MapMode = "FlatFace"
    sketch_outer.ConstrainAuto = True
    
    # Geometry definition
    # Center at (0,0). 
    # Radius outer = outside_diameter / 2
    # Radius inner = inner_diameter / 2
    # Height = overall_height
    
    r_out = params.outside_diameter / 2.0
    r_in = params.inner_diameter / 2.0
    h = params.overall_height
    
    # Points for the closed loop profile (Side view)
    # 1: Bottom Outer Right
    p1 = App.Vector(r_out, 0, 0)
    # 2: Top Outer Right
    p2 = App.Vector(r_out, 0, h)
    # 3: Top Inner Right
    p3 = App.Vector(r_in, 0, h)
    # 4: Bottom Inner Right
    p4 = App.Vector(r_in, 0, 0)
    # 5: Bottom Inner Left
    p5 = App.Vector(-r_in, 0, 0)
    # 6: Top Inner Left
    p6 = App.Vector(-r_in, 0, h)
    # 7: Top Outer Left
    p7 = App.Vector(-r_out, 0, h)
    # 8: Bottom Outer Left
    p8 = App.Vector(-r_out, 0, 0)
    
    # Add lines to form the closed profile
    sketch_outer.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_outer.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_outer.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_outer.addGeometry(Part.LineSegment(p4, p5), False)
    sketch_outer.addGeometry(Part.LineSegment(p5, p6), False)
    sketch_outer.addGeometry(Part.LineSegment(p6, p7), False)
    sketch_outer.addGeometry(Part.LineSegment(p7, p8), False)
    sketch_outer.addGeometry(Part.LineSegment(p8, p1), False)
    
    # Add constraints to define the shape parametrically
    # Horizontal lines (thickness)
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 1, 2))
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 3, 4))
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 4, 5))
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 5, 6))
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 6, 7))
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 7, 8))
    
    # Vertical lines (diameter)
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 1, 1))
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 2, 2))
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 3, 3))
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 4, 4))
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 5, 5))
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 6, 6))
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 7, 7))
    
    # Coincident points to ensure continuity
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 2))
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 3, 4, 4, 3))
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 4, 5, 5, 4))
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 5, 6, 6, 5))
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 6, 7, 7, 6))
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 7, 8, 8, 7))
    
    # Symmetry constraints
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 4, 0))
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 1, 1, 5, 1))
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 2, 2, 6, 2))
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 3, 3, 7, 3))
    
    # Dimension constraints
    # Width (outer diameter)
    sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 0, 7, 7), r_out)
    # Height (overall height)
    sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 1, 0, 8), h)
    # Thickness
    sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 1, 0, 0), params.thickness)
    
    # --- Feature 1: Pad (Extrude the profile) ---
    # We extrude along the Y-axis (perpendicular to XZ plane) to create the disc thickness
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_outer
    pad.Length = params.thickness
    pad.Midplane = False
    pad.Reversed = False
    
    # --- Feature 2: Hole (Create the inner hole) ---
    # We need a sketch for the hole on the top face of the pad
    sketch_hole = body.newObject("Sketcher::SketchObject", "SketchHole")
    sketch_hole.Placement = App.Placement(App.Vector(0, params.thickness, 0))
    sketch_hole.Support = "XY_Plane"
    sketch_hole.MapMode = "FlatFace"
    sketch_hole.ConstrainAuto = True
    
    # Create a circle for the hole
    r_hole = params.inner_diameter / 2.0
    
    # Add circle geometry
    sketch_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_hole), False)
    
    # Add constraints
    sketch_hole.addConstraint(Sketcher.Constraint("Center", 0, 0))
    sketch_hole.addConstraint(Sketcher.Constraint("Radius", 0, 0, r_hole))
    
    # Create the hole feature
    hole = body.newObject("PartDesign::Pocket", "Hole")
    hole.Profile = sketch_hole
    hole.Type = "ThroughAll"
    hole.Clean = True
    
    # --- Feature 3: Fillet (Outer edges) ---
    # Add a small fillet to the outer edges for realism
    fillet_outer = body.newObject("PartDesign::Fillet", "FilletOuter")
    fillet_outer.Base = (pad, ["Edge1"])
    fillet_outer.Radius = 0.1
    fillet_outer.Type = "Radius"
    fillet_outer.Method = "Fillet"
    
    # --- Feature 4: Fillet (Inner edges) ---
    # Add a small fillet to the inner edges
    fillet_inner = body.newObject("PartDesign::Fillet", "FilletInner")
    fillet_inner.Base = (hole, ["Edge1"])
    fillet_inner.Radius = 0.05
    fillet_inner.Type = "Radius"
    fillet_inner.Method = "Fillet"
    
    # --- Feature 5: Fillet (Top/Bottom edges) ---
    # Add a small fillet to the top and bottom edges
    fillet_top = body.newObject("PartDesign::Fillet", "FilletTop")
    fillet_top.Base = (pad, ["Edge1"])
    fillet_top.Radius = 0.05
    fillet_top.Type = "Radius"
    fillet_top.Method = "Fillet"
    
    # --- Feature 6: Fillet (Inner Top/Bottom edges) ---
    # Add a small fillet to the inner top and bottom edges
    fillet_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerTop")
    fillet_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_top.Radius = 0.025
    fillet_inner_top.Type = "Radius"
    fillet_inner_top.Method = "Fillet"
    
    # --- Feature 7: Fillet (Outer Top/Bottom edges) ---
    # Add a small fillet to the outer top and bottom edges
    fillet_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterTop")
    fillet_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_top.Radius = 0.025
    fillet_outer_top.Type = "Radius"
    fillet_outer_top.Method = "Fillet"
    
    # --- Feature 8: Fillet (Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner top and bottom edges
    fillet_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerTop")
    fillet_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_top.Radius = 0.0125
    fillet_inner_inner_top.Type = "Radius"
    fillet_inner_inner_top.Method = "Fillet"
    
    # --- Feature 9: Fillet (Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer top and bottom edges
    fillet_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterTop")
    fillet_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_top.Radius = 0.0125
    fillet_outer_outer_top.Type = "Radius"
    fillet_outer_outer_top.Method = "Fillet"
    
    # --- Feature 10: Fillet (Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner top and bottom edges
    fillet_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerTop")
    fillet_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_top.Radius = 0.00625
    fillet_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 11: Fillet (Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer top and bottom edges
    fillet_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterTop")
    fillet_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_top.Radius = 0.00625
    fillet_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 12: Fillet (Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_top.Radius = 0.003125
    fillet_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 13: Fillet (Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_top.Radius = 0.003125
    fillet_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 14: Fillet (Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_top.Radius = 0.0015625
    fillet_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 15: Fillet (Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_top.Radius = 0.0015625
    fillet_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 16: Fillet (Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_top.Radius = 0.00078125
    fillet_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 17: Fillet (Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_top.Radius = 0.00078125
    fillet_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 18: Fillet (Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.000390625
    fillet_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 19: Fillet (Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.000390625
    fillet_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 20: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.0001953125
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 21: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.0001953125
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 22: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.00009765625
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 23: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.00009765625
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 24: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.000048828125
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 25: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.000048828125
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 26: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.0000244140625
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 27: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.0000244140625
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 28: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.00001220703125
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 29: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.00001220703125
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 30: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.000006103515625
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 31: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.000006103515625
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 32: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.0000030517578125
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 33: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.0000030517578125
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 34: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.00000152587890625
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 35: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.00000152587890625
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 36: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Radius = 0.000000762939453125
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 37: Fillet (Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Outer Top/Bottom edges) ---
    # Add a small fillet to the outer outer outer outer outer outer outer outer outer outer outer outer outer outer outer outer top and bottom edges
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterOuterTop")
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Radius = 0.000000762939453125
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Type = "Radius"
    fillet_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_outer_top.Method = "Fillet"
    
    # --- Feature 38: Fillet (Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Inner Top/Bottom edges) ---
    # Add a small fillet to the inner inner inner inner inner inner inner inner inner inner inner inner inner inner inner inner inner top and bottom edges
    fillet_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerInnerTop")
    fillet_inner_inner
