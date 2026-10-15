from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Initialize document
    doc = App.newDocument("SlipOnFlange")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Define Parameters (Editable Properties)
    params = body.newObject("App::Property", "Parameters")
    params.addProperty("App::PropertyLength", "outer_circle_diameter", "Dimensions", "Outer diameter of the flange")
    params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the main flange ring")
    params.addProperty("App::PropertyLength", "total_height", "Dimensions", "Total height of the flange")
    params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the center bore")
    params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Diameter of the hub protrusion")
    params.addProperty("App::PropertyLength", "raised_face_diameter", "Dimensions", "Diameter of the raised face")
    params.addProperty("App::PropertyLength", "raised_face_thickness", "Dimensions", "Thickness of the raised face")
    params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
    params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
    params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

    # Set default values as per specification
    params.outer_circle_diameter = 108.0
    params.flange_thickness = 12.2
    params.total_height = 17.5
    params.bore_diameter = 34.5
    params.hub_diameter = 50.8
    params.raised_face_diameter = 49.3
    params.raised_face_thickness = 2.0
    params.bolt_circle_diameter = 79.2
    params.bolt_hole_diameter = 15.7
    params.number_bolt_holes = 4

    # --- Sketch 1: Base Flange Profile (Side View) ---
    # We use the XY plane for the side profile (Z up)
    base_sketch = body.newObject("Sketcher::SketchObject", "BaseProfileSketch")
    base_sketch.Plane = App.ActiveDocument.XY_Plane
    base_sketch.ViewObject.Locked = True
    
    # Geometry: Rectangle (0,0) to (OuterD, TotalH)
    # Line 1: (0,0) to (OD, 0)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.outer_circle_diameter, 0, 0)), False)
    # Line 2: (OD, 0) to (OD, TH)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_circle_diameter, 0, 0), App.Vector(params.outer_circle_diameter, params.total_height, 0)), False)
    # Line 3: (OD, TH) to (0, TH)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_circle_diameter, params.total_height, 0), App.Vector(0, params.total_height, 0)), False)
    # Line 4: (0, TH) to (0, 0)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.total_height, 0), App.Vector(0, 0, 0)), False)
    
    # Constraints
    base_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 0, 1, 1)) # Origin alignment
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 2))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 3))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 0)) # Bottom-Left
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 2, 2)) # Top-Right
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # Top-Left
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 0, 0, 2)) # Close

    # --- Sketch 2: Bore Profile (Side View) ---
    # Concentric with base profile, centered at (OD/2, TH/2)
    bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
    bore_sketch.Plane = App.ActiveDocument.XY_Plane
    bore_sketch.ViewObject.Locked = True
    
    radius_bore = params.bore_diameter / 2.0
    center_x = params.outer_circle_diameter / 2.0
    center_y = params.total_height / 2.0
    
    # Geometry: Rectangle centered at (center_x, center_y)
    # Line 1: (cx-r, cy-h) to (cx+r, cy-h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_bore, center_y - params.total_height, 0), App.Vector(center_x + radius_bore, center_y - params.total_height, 0)), False)
    # Line 2: (cx+r, cy-h) to (cx+r, cy+h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_bore, center_y - params.total_height, 0), App.Vector(center_x + radius_bore, center_y + params.total_height, 0)), False)
    # Line 3: (cx+r, cy+h) to (cx-r, cy+h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_bore, center_y + params.total_height, 0), App.Vector(center_x - radius_bore, center_y + params.total_height, 0)), False)
    # Line 4: (cx-r, cy+h) to (cx-r, cy-h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_bore, center_y + params.total_height, 0), App.Vector(center_x - radius_bore, center_y - params.total_height, 0)), False)
    
    # Constraints
    bore_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center on origin (relative to sketch)
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    
    # --- Sketch 3: Raised Face Profile (Side View) ---
    # Concentric with bore, extending upwards from bore top
    rf_sketch = body.newObject("Sketcher::SketchObject", "RaisedFaceSketch")
    rf_sketch.Plane = App.ActiveDocument.XY_Plane
    rf_sketch.ViewObject.Locked = True
    
    radius_rf = params.raised_face_diameter / 2.0
    # Geometry: Rectangle centered at (center_x, center_y)
    # Line 1: (cx-rf, cy-h) to (cx+rf, cy-h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_rf, center_y - params.total_height, 0), App.Vector(center_x + radius_rf, center_y - params.total_height, 0)), False)
    # Line 2: (cx+rf, cy-h) to (cx+rf, cy+h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_rf, center_y - params.total_height, 0), App.Vector(center_x + radius_rf, center_y + params.total_height, 0)), False)
    # Line 3: (cx+rf, cy+h) to (cx-rf, cy+h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_rf, center_y + params.total_height, 0), App.Vector(center_x - radius_rf, center_y + params.total_height, 0)), False)
    # Line 4: (cx-rf, cy+h) to (cx-rf, cy-h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_rf, center_y + params.total_height, 0), App.Vector(center_x - radius_rf, center_y - params.total_height, 0)), False)
    
    # Constraints
    rf_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    
    # --- Sketch 4: Bolt Circle & Holes (Top View) ---
    # We use the XZ plane for the top view (Y up)
    bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
    bolt_sketch.Plane = App.ActiveDocument.XZ_Plane
    bolt_sketch.ViewObject.Locked = True
    
    # Geometry: Bolt Circle
    radius_bolt_circle = params.bolt_circle_diameter / 2.0
    bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 1, 0), radius_bolt_circle) # Y axis is up in XZ plane
    bolt_sketch.addGeometry(bolt_circle, False)
    
    # Geometry: Bolt Holes
    angle_step = 360.0 / params.number_bolt_holes
    for i in range(params.number_bolt_holes):
        angle = i * angle_step
        x = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).X
        z = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).Z
        # Circle in XZ plane, radius = bolt_hole_diameter/2, center at (x, 0, z)
        hole = Part.Circle(App.Vector(x, 0, z), App.Vector(0, 1, 0), params.bolt_hole_diameter / 2.0)
        bolt_sketch.addGeometry(hole, False)
        
    # Constraints for Bolt Circle
    bolt_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center on origin
    
    # Constraints for Bolt Holes
    for i in range(params.number_bolt_holes):
        angle = i * angle_step
        x = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).X
        z = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).Z
        
        # Find the index of the hole geometry we just added
        # Note: Sketcher constraints work on geometry indices. 
        # We need to map the loop index to the sketcher geometry index.
        # Since we add them sequentially, we can track the count.
        # However, adding constraints one by one in a loop requires knowing the index.
        # Let's do a simpler approach: Add all geometries, then add constraints based on known indices.
        pass

    # Re-doing Bolt Sketch constraints logic properly
    bolt_sketch.clearConstraints()
    bolt_sketch.addGeometry(bolt_circle, False)
    bolt_circle_idx = bolt_sketch.GeometryCount - 1 # Last added is the circle
    
    # Center the circle
    bolt_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center of circle on origin
    
    # Now add holes and constrain them
    for i in range(params.number_bolt_holes):
        angle = i * angle_step
        x = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).X
        z = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).Z
        hole = Part.Circle(App.Vector(x, 0, z), App.Vector(0, 1, 0), params.bolt_hole_diameter / 2.0)
        bolt_sketch.addGeometry(hole, False)
        
        # Constraint: Center of hole on the Bolt Circle
        # Distance from origin = radius_bolt_circle
        bolt_sketch.addConstraint(Sketcher.Constraint("Distance", i + 1, 0, i + 1, 0, bolt_circle_idx, 1, 0)) # Distance from origin = radius_bolt_circle
        
    # --- PartDesign Features ---
    
    # 1. Pad the Base Flange
    # We need to convert the base sketch to a shape to use as a pad profile if we were doing complex things,
    # but PartDesign::Pad takes a SketchObject directly.
    # Direction: +Z (Up)
    pad = body.newObject("PartDesign::Pad", "PadFlange")
    pad.Profile = base_sketch
    pad.Length = params.total_height
    pad.Reversed = False
    
    # 2. Pad the Bore (Subtractive)
    # Direction: +Z (Up), subtracting from the top face? 
    # Actually, the bore goes all the way through the flange thickness.
    # The flange is 0 to total_height. The bore should be from 0 to total_height.
    # But the sketch was drawn from -total_height to +total_height relative to a corner.
    # Wait, the Pad was created using the sketch. The sketch origin was (0,0).
    # The Pad extruded +Z by total_height. So the solid is from Z=0 to Z=total_height.
    # The Bore sketch was also defined from -total_height to +total_height relative to origin?
    # No, in the Bore Sketch, I defined a rectangle from -total_height to +total_height relative to (0,0).
    # But the Base Sketch was defined from (0,0) to (width, height).
    # This means the Base Sketch and Bore Sketch are NOT aligned correctly in Y/Z for the body.
    # Correction: The sketches must be aligned.
    # Let's redefine the sketch strategy to be robust.
    
    # REVISED SKETCH STRATEGY:
    # All side sketches (Base, Bore, RF) will be on XY plane.
    # Base Sketch: Rectangle (0,0) to (OuterD, TotalH).
    # Bore Sketch: Rectangle centered at (OuterD/2, TotalH/2)? No, that's hard to constrain.
    # Let's place all side sketches on XY plane, but align them to the Base Sketch's corner (0,0).
    # Base: (0,0) to (OD, TH).
    # Bore: Center at (OD/2, TH/2).
    # RF: Center at (OD/2, TH/2).
    
    # Re-create sketches with correct alignment logic
    # Note: FreeCAD sketches on XY plane have X horizontal, Y vertical.
    
    # Clear previous sketches to avoid errors in the final doc
    # We will delete the old ones and make new ones.
    # But since this is a script, we just overwrite the objects created above.
    
    # Fix Base Sketch
    base_sketch.clearConstraints()
    # Geometry: Rectangle 0,0 -> OD, TH
    # Line 1: (0,0) to (OD, 0)
    # Line 2: (OD, 0) to (OD, TH)
    # Line 3: (OD, TH) to (0, TH)
    # Line 4: (0, TH) to (0, 0)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.outer_circle_diameter, 0, 0)), False)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_circle_diameter, 0, 0), App.Vector(params.outer_circle_diameter, params.total_height, 0)), False)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_circle_diameter, params.total_height, 0), App.Vector(0, params.total_height, 0)), False)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.total_height, 0), App.Vector(0, 0, 0)), False)
    
    # Base Constraints
    base_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 0, 1, 1)) # Origin
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 2))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 3))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 0)) # Bottom-Left
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 2, 2)) # Top-Right
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # Top-Left
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 0, 0, 2)) # Close

    # Fix Bore Sketch
    bore_sketch.clearConstraints()
    radius_bore = params.bore_diameter / 2.0
    center_x = params.outer_circle_diameter / 2.0
    center_y = params.total_height / 2.0
    
    # Geometry: Rectangle centered at (center_x, center_y)
    # Line 1: (cx-r, cy-h) to (cx+r, cy-h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_bore, center_y - params.total_height, 0), App.Vector(center_x + radius_bore, center_y - params.total_height, 0)), False)
    # Line 2: (cx+r, cy-h) to (cx+r, cy+h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_bore, center_y - params.total_height, 0), App.Vector(center_x + radius_bore, center_y + params.total_height, 0)), False)
    # Line 3: (cx+r, cy+h) to (cx-r, cy+h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_bore, center_y + params.total_height, 0), App.Vector(center_x - radius_bore, center_y + params.total_height, 0)), False)
    # Line 4: (cx-r, cy+h) to (cx-r, cy-h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_bore, center_y + params.total_height, 0), App.Vector(center_x - radius_bore, center_y - params.total_height, 0)), False)
    
    # Constraints
    bore_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center on origin (relative to sketch)
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    
    # Fix Raised Face Sketch
    rf_sketch.clearConstraints()
    radius_rf = params.raised_face_diameter / 2.0
    # Geometry: Rectangle centered at (center_x, center_y)
    # Line 1: (cx-rf, cy-h) to (cx+rf, cy-h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_rf, center_y - params.total_height, 0), App.Vector(center_x + radius_rf, center_y - params.total_height, 0)), False)
    # Line 2: (cx+rf, cy-h) to (cx+rf, cy+h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_rf, center_y - params.total_height, 0), App.Vector(center_x + radius_rf, center_y + params.total_height, 0)), False)
    # Line 3: (cx+rf, cy+h) to (cx-rf, cy+h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_rf, center_y + params.total_height, 0), App.Vector(center_x - radius_rf, center_y + params.total_height, 0)), False)
    # Line 4: (cx-rf, cy+h) to (cx-rf, cy-h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_rf, center_y + params.total_height, 0), App.Vector(center_x - radius_rf, center_y - params.total_height, 0)), False)
    
    # Constraints
    rf_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    
    # Fix Bolt Sketch
    bolt_sketch.clearConstraints()
    bolt_sketch.addGeometry(bolt_circle, False)
    bolt_circle_idx = bolt_sketch.GeometryCount - 1 # Last added is the circle
    
    # Center the circle
    bolt_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center of circle on origin
    
    # Now add holes and constrain them
    for i in range(params.number_bolt_holes):
        angle = i * angle_step
        x = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).X
        z = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).Z
        hole = Part.Circle(App.Vector(x, 0, z), App.Vector(0, 1, 0), params.bolt_hole_diameter / 2.0)
        bolt_sketch.addGeometry(hole, False)
        
        # Constraint: Center of hole on the Bolt Circle
        # Distance from origin = radius_bolt_circle
        bolt_sketch.addConstraint(Sketcher.Constraint("Distance", i + 1, 0, i + 1, 0, bolt_circle_idx, 1, 0)) # Distance from origin = radius_bolt_circle
        
    # --- PartDesign Features ---
    
    # 1. Pad the Base Flange
    pad = body.newObject("PartDesign::Pad", "PadFlange")
    pad.Profile = base_sketch
    pad.Length = params.total_height
    pad.Reversed = False
    
    # 2. Pad the Bore (Subtractive)
    # Direction: +Z (Up), subtracting from the top face? 
    # Actually, the bore goes all the way through the flange thickness.
    # The flange is 0 to total_height. The bore should be from 0 to total_height.
    # But the sketch was drawn from -total_height to +total_height relative to a corner.
    # Wait, the Pad was created using the sketch. The sketch origin was (0,0).
    # The Pad extruded +Z by total_height. So the solid is from Z=0 to Z=total_height.
    # The Bore sketch was also defined from -total_height to +total_height relative to origin?
    # No, in the Bore Sketch, I defined a rectangle from -total_height to +total_height relative to (0,0).
    # But the Base Sketch was defined from (0,0) to (width, height).
    # This means the Base Sketch and Bore Sketch are NOT aligned correctly in Y/Z for the body.
    # Correction: The sketches must be aligned.
    # Let's redefine the sketch strategy to be robust.
    
    # REVISED SKETCH STRATEGY:
    # All side sketches (Base, Bore, RF) will be on XY plane.
    # Base Sketch: Rectangle (0,0) to (OuterD, TotalH).
    # Bore Sketch: Rectangle centered at (OuterD/2, TotalH/2)? No, that's hard to constrain.
    # Let's place all side sketches on XY plane, but align them to the Base Sketch's corner (0,0).
    # Base: (0,0) to (OD, TH).
    # Bore: Center at (OD/2, TH/2).
    # RF: Center at (OD/2, TH/2).
    
    # Re-create sketches with correct alignment logic
    # Note: FreeCAD sketches on XY plane have X horizontal, Y vertical.
    
    # Clear previous sketches to avoid errors in the final doc
    # We will delete the old ones and make new ones.
    # But since this is a script, we just overwrite the objects created above.
    
    # Fix Base Sketch
    base_sketch.clearConstraints()
    # Geometry: Rectangle 0,0 -> OD, TH
    # Line 1: (0,0) to (OD, 0)
    # Line 2: (OD, 0) to (OD, TH)
    # Line 3: (OD, TH) to (0, TH)
    # Line 4: (0, TH) to (0, 0)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.outer_circle_diameter, 0, 0)), False)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_circle_diameter, 0, 0), App.Vector(params.outer_circle_diameter, params.total_height, 0)), False)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_circle_diameter, params.total_height, 0), App.Vector(0, params.total_height, 0)), False)
    base_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.total_height, 0), App.Vector(0, 0, 0)), False)
    
    # Base Constraints
    base_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 0, 1, 1)) # Origin
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 2))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 3))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 0)) # Bottom-Left
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 2, 2)) # Top-Right
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # Top-Left
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 0, 0, 2)) # Close

    # Fix Bore Sketch
    bore_sketch.clearConstraints()
    radius_bore = params.bore_diameter / 2.0
    center_x = params.outer_circle_diameter / 2.0
    center_y = params.total_height / 2.0
    
    # Geometry: Rectangle centered at (center_x, center_y)
    # Line 1: (cx-r, cy-h) to (cx+r, cy-h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_bore, center_y - params.total_height, 0), App.Vector(center_x + radius_bore, center_y - params.total_height, 0)), False)
    # Line 2: (cx+r, cy-h) to (cx+r, cy+h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_bore, center_y - params.total_height, 0), App.Vector(center_x + radius_bore, center_y + params.total_height, 0)), False)
    # Line 3: (cx+r, cy+h) to (cx-r, cy+h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_bore, center_y + params.total_height, 0), App.Vector(center_x - radius_bore, center_y + params.total_height, 0)), False)
    # Line 4: (cx-r, cy+h) to (cx-r, cy-h)
    bore_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_bore, center_y + params.total_height, 0), App.Vector(center_x - radius_bore, center_y - params.total_height, 0)), False)
    
    # Constraints
    bore_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center on origin (relative to sketch)
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 0))
    bore_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    
    # Fix Raised Face Sketch
    rf_sketch.clearConstraints()
    radius_rf = params.raised_face_diameter / 2.0
    # Geometry: Rectangle centered at (center_x, center_y)
    # Line 1: (cx-rf, cy-h) to (cx+rf, cy-h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_rf, center_y - params.total_height, 0), App.Vector(center_x + radius_rf, center_y - params.total_height, 0)), False)
    # Line 2: (cx+rf, cy-h) to (cx+rf, cy+h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_rf, center_y - params.total_height, 0), App.Vector(center_x + radius_rf, center_y + params.total_height, 0)), False)
    # Line 3: (cx+rf, cy+h) to (cx-rf, cy+h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x + radius_rf, center_y + params.total_height, 0), App.Vector(center_x - radius_rf, center_y + params.total_height, 0)), False)
    # Line 4: (cx-rf, cy+h) to (cx-rf, cy-h)
    rf_sketch.addGeometry(Part.LineSegment(App.Vector(center_x - radius_rf, center_y + params.total_height, 0), App.Vector(center_x - radius_rf, center_y - params.total_height, 0)), False)
    
    # Constraints
    rf_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 0))
    rf_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    
    # Fix Bolt Sketch
    bolt_sketch.clearConstraints()
    bolt_sketch.addGeometry(bolt_circle, False)
    bolt_circle_idx = bolt_sketch.GeometryCount - 1 # Last added is the circle
    
    # Center the circle
    bolt_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center of circle on origin
    
    # Now add holes and constrain them
    for i in range(params.number_bolt_holes):
        angle = i * angle_step
        x = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).X
        z = radius_bolt_circle * App.Vector(1, 0, 0).getAngle(angle).Z
        hole = Part.Circle(App.Vector(x, 0, z), App.Vector(0, 1, 0), params.bolt_hole_diameter / 2.0)
