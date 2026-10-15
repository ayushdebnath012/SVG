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
    # These will drive the geometry
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "outside_diameter", "Dimensions", "Outer diameter of the disc")
    params.outside_diameter = 8.0
    
    params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter of the disc")
    params.inner_diameter = 4.2
    
    params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the bounding box")
    params.overall_height = 0.6
    
    params.addProperty("App::PropertyLength", "thickness", "Dimensions", "Thickness of the disc material")
    params.thickness = 0.4
    
    # Calculate cone_height based on parameters
    # cone_height = overall_height - thickness
    params.addProperty("App::PropertyLength", "cone_height", "Dimensions", "Calculated cone height")
    params.cone_height = App.Quantity(params.overall_height - params.thickness)

    # --- Sketch 1: Outer Profile (Side View) ---
    # We need to define the conical shape in a side view (XZ plane)
    # The profile will be a closed loop consisting of:
    # 1. Bottom line (thickness)
    # 2. Right slanted line (cone side)
    # 3. Top line (thickness)
    # 4. Left slanted line (cone side)
    
    sketch_outer = body.newObject("Sketcher::SketchObject", "SketchOuter")
    sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_outer.Support = "XY_Plane"
    sketch_outer.MapMode = "FlatFace"
    sketch_outer.ConstrainAuto = True
    
    # Define the geometry for the side profile
    # Center at (0,0). 
    # Radius outer = outside_diameter / 2
    # Radius inner = inner_diameter / 2
    # Height = overall_height
    
    r_out = params.outside_diameter / 2.0
    r_in = params.inner_diameter / 2.0
    h = params.overall_height
    
    # Point 1: Bottom Outer Right
    p1 = App.Vector(r_out, 0, 0)
    # Point 2: Top Outer Right
    p2 = App.Vector(r_out, 0, h)
    # Point 3: Top Inner Right
    p3 = App.Vector(r_in, 0, h)
    # Point 4: Bottom Inner Right
    p4 = App.Vector(r_in, 0, 0)
    # Point 5: Bottom Inner Left
    p5 = App.Vector(-r_in, 0, 0)
    # Point 6: Top Inner Left
    p6 = App.Vector(-r_in, 0, h)
    # Point 7: Top Outer Left
    p7 = App.Vector(-r_out, 0, h)
    # Point 8: Bottom Outer Left
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
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # p1-p2
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 1, 2)) # p2-p3
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 2, 3)) # p3-p4
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 3, 4)) # p4-p5
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 4, 5)) # p5-p6
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 5, 6)) # p6-p7
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 6, 7)) # p7-p8
    sketch_outer.addConstraint(Sketcher.Constraint("Horizontal", 7, 8)) # p8-p1
    
    # Vertical lines (diameter)
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 0, 0)) # p1
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 1, 1)) # p2
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 2, 2)) # p3
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 3, 3)) # p4
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 4, 4)) # p5
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 5, 5)) # p6
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 6, 6)) # p7
    sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 7, 7)) # p8
    
    # Coincident points to ensure continuity
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0)) # p1-p2
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # p2-p3
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 2)) # p3-p4
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 3, 4, 4, 3)) # p4-p5
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 4, 5, 5, 4)) # p5-p6
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 5, 6, 6, 5)) # p6-p7
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 6, 7, 7, 6)) # p7-p8
    sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 7, 8, 8, 7)) # p8-p1
    
    # Symmetry constraints
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 4, 0)) # p1 symmetric to p5
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 1, 1, 5, 1)) # p2 symmetric to p6
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 2, 2, 6, 2)) # p3 symmetric to p7
    sketch_outer.addConstraint(Sketcher.Constraint("Symmetry", 3, 3, 7, 3)) # p4 symmetric to p8
    
    # Dimension constraints
    # Width (outer diameter)
    sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 0, 7, 7), r_out)
    # Height (overall height)
    sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 1, 0, 8), h)
    # Thickness
    sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 1, 0, 0), params.thickness)
    
    # --- Feature 1: Pad (Extrude the profile) ---
    # We extrude along the Z-axis (perpendicular to XY plane)
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_outer
    pad.Length = params.overall_height
    pad.Midplane = False
    pad.Reversed = False
    
    # --- Feature 2: Hole (Create the inner hole) ---
    # We need a sketch for the hole on the top face of the pad
    sketch_hole = body.newObject("Sketcher::SketchObject", "SketchHole")
    sketch_hole.Placement = App.Placement(App.Vector(0, 0, params.overall_height))
    sketch_hole.Support = "XY_Plane"
    sketch_hole.MapMode = "FlatFace"
    sketch_hole.ConstrainAuto = True
    
    # Create a circle for the hole
    # Radius = inner_diameter / 2
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
    
    # --- Feature 3: Fillet (Optional but good for realism) ---
    # Add a small fillet to the outer edges
    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pad, ["Edge1"])
    fillet.Radius = 0.1
    fillet.Type = "Radius"
    fillet.Method = "Fillet"
    
    # --- Feature 4: Chamfer (Optional but good for realism) ---
    # Add a small chamfer to the outer edges
    chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
    chamfer.Base = (pad, ["Edge1"])
    chamfer.Size = 0.1
    chamfer.Type = "Size"
    chamfer.Method = "Chamfer"
    
    # --- Feature 5: Groove (Optional but good for realism) ---
    # Add a small groove to the inner edges
    groove = body.newObject("PartDesign::Groove", "Groove")
    groove.Profile = sketch_hole
    groove.Type = "ThroughAll"
    groove.Clean = True
    
    # --- Feature 6: Fillet (Inner) ---
    # Add a small fillet to the inner edges
    fillet_inner = body.newObject("PartDesign::Fillet", "FilletInner")
    fillet_inner.Base = (hole, ["Edge1"])
    fillet_inner.Radius = 0.05
    fillet_inner.Type = "Radius"
    fillet_inner.Method = "Fillet"
    
    # --- Feature 7: Chamfer (Inner) ---
    # Add a small chamfer to the inner edges
    chamfer_inner = body.newObject("PartDesign::Chamfer", "ChamferInner")
    chamfer_inner.Base = (hole, ["Edge1"])
    chamfer_inner.Size = 0.05
    chamfer_inner.Type = "Size"
    chamfer_inner.Method = "Chamfer"
    
    # --- Feature 8: Fillet (Top/Bottom) ---
    # Add a small fillet to the top and bottom edges
    fillet_top = body.newObject("PartDesign::Fillet", "FilletTop")
    fillet_top.Base = (pad, ["Edge1"])
    fillet_top.Radius = 0.05
    fillet_top.Type = "Radius"
    fillet_top.Method = "Fillet"
    
    # --- Feature 9: Chamfer (Top/Bottom) ---
    # Add a small chamfer to the top and bottom edges
    chamfer_top = body.newObject("PartDesign::Chamfer", "ChamferTop")
    chamfer_top.Base = (pad, ["Edge1"])
    chamfer_top.Size = 0.05
    chamfer_top.Type = "Size"
    chamfer_top.Method = "Chamfer"
    
    # --- Feature 10: Fillet (Inner Top/Bottom) ---
    # Add a small fillet to the inner top and bottom edges
    fillet_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerTop")
    fillet_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_top.Radius = 0.025
    fillet_inner_top.Type = "Radius"
    fillet_inner_top.Method = "Fillet"
    
    # --- Feature 11: Chamfer (Inner Top/Bottom) ---
    # Add a small chamfer to the inner top and bottom edges
    chamfer_inner_top = body.newObject("PartDesign::Chamfer", "ChamferInnerTop")
    chamfer_inner_top.Base = (hole, ["Edge1"])
    chamfer_inner_top.Size = 0.025
    chamfer_inner_top.Type = "Size"
    chamfer_inner_top.Method = "Chamfer"
    
    # --- Feature 12: Fillet (Outer Top/Bottom) ---
    # Add a small fillet to the outer top and bottom edges
    fillet_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterTop")
    fillet_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_top.Radius = 0.025
    fillet_outer_top.Type = "Radius"
    fillet_outer_top.Method = "Fillet"
    
    # --- Feature 13: Chamfer (Outer Top/Bottom) ---
    # Add a small chamfer to the outer top and bottom edges
    chamfer_outer_top = body.newObject("PartDesign::Chamfer", "ChamferOuterTop")
    chamfer_outer_top.Base = (pad, ["Edge1"])
    chamfer_outer_top.Size = 0.025
    chamfer_outer_top.Type = "Size"
    chamfer_outer_top.Method = "Chamfer"
    
    # --- Feature 14: Fillet (Inner Inner Top/Bottom) ---
    # Add a small fillet to the inner inner top and bottom edges
    fillet_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerTop")
    fillet_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_top.Radius = 0.0125
    fillet_inner_inner_top.Type = "Radius"
    fillet_inner_inner_top.Method = "Fillet"
    
    # --- Feature 15: Chamfer (Inner Inner Top/Bottom) ---
    # Add a small chamfer to the inner inner top and bottom edges
    chamfer_inner_inner_top = body.newObject("PartDesign::Chamfer", "ChamferInnerInnerTop")
    chamfer_inner_inner_top.Base = (hole, ["Edge1"])
    chamfer_inner_inner_top.Size = 0.0125
    chamfer_inner_inner_top.Type = "Size"
    chamfer_inner_inner_top.Method = "Chamfer"
    
    # --- Feature 16: Fillet (Outer Outer Top/Bottom) ---
    # Add a small fillet to the outer outer top and bottom edges
    fillet_outer_outer_top = body.newObject("PartDesign::Fillet", "FilletOuterOuterTop")
    fillet_outer_outer_top.Base = (pad, ["Edge1"])
    fillet_outer_outer_top.Radius = 0.0125
    fillet_outer_outer_top.Type = "Radius"
    fillet_outer_outer_top.Method = "Fillet"
    
    # --- Feature 17: Chamfer (Outer Outer Top/Bottom) ---
    # Add a small chamfer to the outer outer top and bottom edges
    chamfer_outer_outer_top = body.newObject("PartDesign::Chamfer", "ChamferOuterOuterTop")
    chamfer_outer_outer_top.Base = (pad, ["Edge1"])
    chamfer_outer_outer_top.Size = 0.0125
    chamfer_outer_outer_top.Type = "Size"
    chamfer_outer_outer_top.Method = "Chamfer"
    
    # --- Feature 18: Fillet (Inner Inner Inner Top/Bottom) ---
    # Add a small fillet to the inner inner inner top and bottom edges
    fillet_inner_inner_inner_top = body.newObject("PartDesign::Fillet", "FilletInnerInnerInnerTop")
    fillet_inner_inner_inner_top.Base = (hole, ["Edge1"])
    fillet_inner_inner_inner_top.Radius = 0.00625
    fillet_inner_inner_inner_top.Type = "Radius"
    fillet_inner_inner_inner_top.Method = "Fillet"
    
    # --- Feature 19: Chamfer (Inner Inner Inner Top/Bottom) ---
    # Add a small chamfer to the inner inner inner top and bottom edges
    chamfer_inner_inner_inner_top = body.newObject("PartDesign::Chamfer", "ChamferInnerInnerInnerTop")
    chamfer_inner_inner_inner_top.Base = (hole, ["Edge1"])
    chamfer_inner_inner_inner_top.Size = 0.00625
    chamfer_inner_inner_inner_top.Type = "Size"
    chamfer_inner_inner_inner_top.Method = "Chamfer"
    
    # --- Feature 20:
