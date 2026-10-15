import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("ForkedMountingBracket")
    
    # Create a PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Create a VarSet for parameters (optional but good practice for editability)
    params = body.newObject("App::VarSet", "Parameters")
    
    # --- Part 1: The Main Forked Plate ---
    
    # Sketch 1: Main Profile
    sketch1 = body.newObject("Sketcher::SketchObject", "MainProfile")
    sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch1.Support = [doc.getObject("XY_Plane")]
    sketch1.MapMode = "FlatFace"
    
    # Points (0,0) is bottom-left of the bounding box
    # Y is up, X is right
    
    # Main bottom horizontal edge
    sketch1.addGeometry(Part.LineSegment(App.Vector(10, 25, 0), App.Vector(140, 25, 0)), False)
    
    # Left vertical edge (Height 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(10, 25, 0), App.Vector(10, 73, 0)), False)
    
    # Right vertical edge (Height 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(140, 25, 0), App.Vector(140, 73, 0)), False)
    
    # Top horizontal edge (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(10, 73, 0), App.Vector(140, 73, 0)), False)
    
    # Center vertical spine (Width 126)
    sketch1.addGeometry(Part.LineSegment(App.Vector(63, 25, 0), App.Vector(63, 73, 0)), False)
    
    # Horizontal offset for the "fork" connection (Width 46.39)
    # The fork is centered on the main body, so it goes from 63 - 23.195 to 63 + 23.195
    # Let's just add the two horizontal lines for the fork opening
    sketch1.addGeometry(Part.LineSegment(App.Vector(39.805, 25, 0), App.Vector(39.805, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(86.195, 25, 0), App.Vector(86.195, 73, 0)), False)
    
    # Horizontal offset for the lower fork connection (Width 50.39)
    sketch1.addGeometry(Part.LineSegment(App.Vector(36.805, 25, 0), App.Vector(36.805, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(89.195, 25, 0), App.Vector(89.195, 73, 0)), False)
    
    # Horizontal offset for the lowest fork connection (Width 70.39)
    sketch1.addGeometry(Part.LineSegment(App.Vector(32.805, 25, 0), App.Vector(32.805, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(93.195, 25, 0), App.Vector(93.195, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch1.addGeometry(Part.LineSegment(App.Vector(15, 25, 0), App.Vector(15, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(135, 25, 0), App.Vector(135, 73, 0)), False)
    
    # Horizontal offset for the upper fork connection (Width 48)
    sketch1.addGeometry(Part.LineSegment(App.Vector(51, 25, 0), App.Vector(51, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(129, 25, 0), App.Vector(129, 73, 0)), False)
    
    # Horizontal offset for the middle fork connection (Width 90)
    sketch1.addGeometry(Part.LineSegment(App.Vector(52.5, 25, 0), App.Vector(52.5, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(127.5, 25, 0), App.Vector(127.5, 73, 0)), False)
    
    # Horizontal offset for the main body width (Width 138)
    sketch1.addGeometry(Part.LineSegment(App.Vector(26, 25, 0), App.Vector(26, 73, 0)), False)
    sketch1.addGeometry(Part.LineSegment(App.Vector(112, 25, 0), App.Vector(112, 73, 0)), False)
    
    # Horizontal offset for the widest point (Width 150)
    sketch
