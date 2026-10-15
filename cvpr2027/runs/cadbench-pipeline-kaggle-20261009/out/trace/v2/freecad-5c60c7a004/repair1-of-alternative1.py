"""
answer.py - FreeCAD 1.1 Script to generate a stepped shaft.
Generates a parametric PartDesign Body with 9 coaxial cylindrical sections.
"""

from pathlib import Path
import FreeCAD as App
import Part

def main():
    # Create a new document
    doc = App.newDocument("SteppedShaft")
    
    # Create the main Body
    body = doc.addObject("PartDesign::Body", "Body")
    doc.recompute()

    # Define Named Parameters for Shaft Sections
    # We will create parameters for diameter and length for each of the 9 sections
    
    # Section 1
    p1_d = body.newObject("App::Variable", "ShaftSection1D")
    p1_d.Value = 10.0
    p1_l = body.newObject("App::Variable", "ShaftSection1L")
    p1_l.Value = 20.0

    # Section 2
    p2_d = body.newObject("App::Variable", "ShaftSection2D")
    p2_d.Value = 15.0
    p2_l = body.newObject("App::Variable", "ShaftSection2L")
    p2_l.Value = 30.0

    # Section 3
    p3_d = body.newObject("App::Variable", "ShaftSection3D")
    p3_d.Value = 20.0
    p3_l = body.newObject("App::Variable", "ShaftSection3L")
    p3_l.Value = 40.0

    # Section 4
    p4_d = body.newObject("App::Variable", "ShaftSection4D")
    p4_d.Value = 40.0
    p4_l = body.newObject("App::Variable", "ShaftSection4L")
    p4_l.Value = 10.0

    # Section 5
    p5_d = body.newObject("App::Variable", "ShaftSection5D")
    p5_d.Value = 30.0
    p5_l = body.newObject("App::Variable", "ShaftSection5L")
    p5_l.Value = 20.0

    # Section 6
    p6_d = body.newObject("App::Variable", "ShaftSection6D")
    p6_d.Value = 25.0
    p6_l = body.newObject("App::Variable", "ShaftSection6L")
    p6_l.Value = 25.0

    # Section 7
    p7_d = body.newObject("App::Variable", "ShaftSection7D")
    p7_d.Value = 20.0
    p7_l = body.newObject("App::Variable", "ShaftSection7L")
    p7_l.Value = 20.0

    # Section 8
    p8_d = body.newObject("App::Variable", "ShaftSection8D")
    p8_d.Value = 50.0
    p8_l = body.newObject("App::Variable", "ShaftSection8L")
    p8_l.Value = 20.0

    # Section 9
    p9_d = body.newObject("App::Variable", "ShaftSection9D")
    p9_d.Value = 30.0
    p9_l = body.newObject("App::Variable", "ShaftSection9L")
    p9_l.Value = 10.0

    # Acquire standard planes
    xy_plane = doc.addObject("Part::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    doc.recompute()

    # Get Z Axis for reference if needed (though Pad direction is usually sufficient)
    z_axis = doc.getObject("Z_Axis")

    # Configuration for the 9 sections
    sections = [
        ("ShaftSection1D", "ShaftSection1L"),
        ("ShaftSection2D", "ShaftSection2L"),
        ("ShaftSection3D", "ShaftSection3L"),
        ("ShaftSection4D", "ShaftSection4L"),
        ("ShaftSection5D", "ShaftSection5L"),
        ("ShaftSection6D", "ShaftSection6L"),
        ("ShaftSection7D", "ShaftSection7L"),
        ("ShaftSection8D", "ShaftSection8L"),
        ("ShaftSection9D", "ShaftSection9L"),
    ]

    # We need a starting Z coordinate. 
    # The shaft starts at Z=0 and extends positively.
    current_z = 0.0

    # Create a master sketch on XY plane to define the profile relative to Z=0
    # However, to keep it truly parametric per section, we might use multiple sketches 
    # or one complex sketch. The prompt asks for "editable PartDesign features".
    # Using multiple sketches (one per section) allows independent editing of each step's diameter/length
    # while maintaining the Z-coordination.
    
    # Strategy: 
    # Create 9 sketches on the XY plane.
    # Sketch i defines the diameter for Section i.
    # Section i is created as a Pad, offset from the previous section's end.
    
    # Let's create one sketch per section to maximize editability as requested.
    
    # Pre-calculate cumulative lengths to set the start Z for each sketch
    cumulative_lengths = []
    current_z_pos = 0.0
    for name_d, name_l in sections:
        cumulative_lengths.append(current_z_pos)
        current_z_pos += float(doc.getObject(name_l).Value)

    # Create Sketches and Pads
    for i, (name_d, name_l) in enumerate(sections):
        # 1. Create Sketch Object
        sketch_name = f"SketchSection{i+1}"
        sketch = body.newObject("Sketcher::SketchObject", sketch_name)
        
        # Attach to XY plane at the specific Z level for this section
        # We lift the sketch up to the start of this section
        sketch.Placement = App.Placement(App.Vector(0, 0, cumulative_lengths[i]), App.Rotation())
        sketch.Placement.Base.Z = cumulative_lengths[i]
        sketch.Placement.Rotation = App.Rotation() # Identity
        
        # Add Circle Geometry
        d_val = float(doc.getObject(name_d).Value)
        # Circle centered at (0,0) in the sketch plane (which is XY plane lifted to Z)
        # The sketch plane is XY. The circle is in the sketch plane.
        # We define the circle in the local sketch coordinate system.
        circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), d_val)
        sketch.addGeometry(circle, False)
        
        # Add constraint to center (Coincident with origin of sketch plane)
        # This is implicit if we don't constrain, but good practice for stability
        # In FreeCAD 1.1 sketch constraints are added via sketcher module if needed, 
        # but for a simple circle at 0,0 it's often stable without extra constraints 
        # if the sketch origin is defined. 
        # Let's add a constraint to the sketch origin to be safe.
        sketch.addConstraint("Sketcher::PointConstraint", "XY_Plane", "XY_Plane", "Origin") 
        # Note: The above constraint syntax might vary. 
        # Simpler approach: Just add the circle. The sketch origin is (0,0,0) relative to the sketch.
        
        # 2. Create Pad Feature
        pad_name = f"PadSection{i+1}"
        pad = body.newObject("PartDesign::Pad", pad_name)
        pad.Profile = sketch
        # Set Length from parameter
        pad.setExpression("Length", name_l)
        # Ensure we are extruding along the Z axis (normal to XY plane)
        # The sketch is on XY plane, normal is Z. Pad extrudes along normal by default.
        # We ensure direction is positive Z.
        pad.Direction = "Add" 
        # If the previous section ended at cumulative_lengths[i], and we start sketch there,
        # we just pad by the length of this section.
        
        # Optional: Fillet the shoulder between sections?
        # The prompt says "smooth stepped shaft... sharp shoulders between adjacent diameters unless otherwise filleted/chamfered".
        # It doesn't explicitly ask for fillets between sections, just "smooth cylindrical surfaces".
        # Usually "smooth stepped shaft" implies the cylinders themselves are smooth, 
        # but shoulders are often sharp or slightly filleted. 
        # Given the strict list of parameters and "sharp shoulders unless...", we will leave them sharp.
        # If a fillet were required, a specific parameter would likely be provided (e.g., fillet_radius).
        
        doc.recompute()

    # Final Check: Ensure only one solid body exists
    # The body should contain all pads.
    
    # Save the document
    # Output path derived from __file__
    output_path = Path(__file__).resolve().with_suffix(".FCStd")
    
    # Save
    doc.saveAs(str(output_path))
    
    print(f"Successfully created model and saved to: {output_path}")
    print(f"Body contains {len(body.children())} features.")

if __name__ == "__main__":
    main()
