import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__
script_path = Path(__file__).resolve()
base_filename = script_path.stem + "_base.FCStd"
edit_filename = script_path.stem + "_edit.FCStd"

# --- Parameters ---
# Base Parameters
PARAMS_BASE = {
    "center_bore_diameter": 15.0,
    "drive_lug_inner_arc_radius": 33.0, # Valley radius
    "disk_thickness": 10.0,
}

# Edit Parameters
PARAMS_EDIT = {
    "bolt_hole_diameter": 5.0,
    "number_of_pattern_elements": 4,
    "base_contour_outer_arc_start_angle": -162.6447127,
    "drive_lug_outer_arc_radius": 38.5,
    "drive_lug_outer_arc_central_angle": 55.2894254,
    "bolt_circle_radius": 33.0,
    "bolt_hole_seed_angle_1": 59.3611117,
    "bolt_hole_seed_angle_2": 29.3611118,
    "inner_disk_thickness": 15.0,
    "number_of_drive_lugs": 6,
    "drive_lug_seed_center_angle": 90.0,
    "drive_lug_width": 4.0,
    "drive_lug_tip_edge_center_y": 15.0,
    "disk_outer_arc_radius": 12.5, # Hub valley circle radius
}

def create_document(name):
    doc = App.newDocument(name)
    doc.Label = name
    
    # Create standard planes if they don't exist (FreeCAD 1.1 default setup)
    # We assume standard XY, XZ, YZ planes exist or we create the ones we need.
    # In a fresh doc, they usually exist. If not, we might need to add them manually, 
    # but standard template docs have them.
    # Let's ensure we reference them by name.
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement()
    
    # Parameters Object
    params = body.newObject("App::VarSet", "Parameters")
    
    # Add Base Parameters
    for k, v in PARAMS_BASE.items():
        params.addProperty(f"App::PropertyLength", k, "Dimensions", k)
        params.setValue(k, v)
        
    # Add Edit Parameters
    for k, v in PARAMS_EDIT.items():
        params.addProperty(f"App::PropertyLength", k, "Dimensions", k)
        params.setValue(k, v)
        
    # Add Angle Parameters (Degrees)
    params.addProperty("App::PropertyAngle", "base_contour_outer_arc_start_angle", "Angles", "contour")
    params.setValue("base_contour_outer_arc_start_angle", PARAMS_EDIT["base_contour_outer_arc_start_angle"])
    
    params.addProperty("App::PropertyAngle", "bolt_hole_seed_angle_1", "Angles", "bolts")
    params.setValue("bolt_hole_seed_angle_1", PARAMS_EDIT["bolt_hole_seed_angle_1"])
    
    params.addProperty("App::PropertyAngle", "bolt_hole_seed_angle_2", "Angles", "bolts")
    params.setValue("bolt_hole_seed_angle_2", PARAMS_EDIT["bolt_hole_seed_angle_2"])
    
    params.addProperty("App::PropertyAngle", "drive_lug_seed_center_angle", "Angles", "lugs")
    params.setValue("drive_lug_seed_center_angle", PARAMS_EDIT["drive_lug_seed_center_angle"])
    
    params.addProperty("App::PropertyAngle", "drive_lug_outer_arc_central_angle", "Angles", "lugs")
    params.setValue("drive_lug_outer_arc_central_angle", PARAMS_EDIT["drive_lug_outer_arc_central_angle"])
    
    # Axis references
    # Assuming standard axes exist: X_Axis, Y_Axis, Z_Axis
    # Note: In FreeCAD 1.1, these are usually available.
    
    doc.recompute()
    return doc

def build_base_part(doc):
    body = doc.getObject("Body")
    params = body.getObject("Parameters")
    
    # 1. Create Base Disk Sketch (XY Plane, Z = 0)
    # Axis: Y is coupling axis. Disk lies in XZ plane? 
    # "flange spanning Y = 0 to Y = disk_thickness" -> Disk is in XZ plane.
    # Wait, standard convention: If Y is axis, disk is in XZ plane.
    # However, standard planes: XY (X,Y), XZ (X,Z), YZ (Y,Z).
    # If Y is axis, the disk face is normal to Y, so it lies in XZ plane.
    # We need to sketch on XZ plane.
    
    # Create sketch on XZ plane
    sketch_disk = body.newObject("Sketcher::SketchObject", "Disk_Sketch")
    sketch_disk.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_disk.Placement.rotate(App.Vector(0, 1, 0), 90) # Rotate to face XZ? 
    # Actually, AttachmentSupport for XZ plane usually means the plane normal is Y.
    # Let's use explicit placement on YZ or XY and rotate, or use XZ plane directly.
    # Standard: XY_Plane normal is Z. XZ_Plane normal is Y. YZ_Plane normal is X.
    # We want to draw on the plane perpendicular to Y (XZ plane).
    # So AttachmentSupport = (doc.getObject("XZ_Plane"), [""])
    
    xz_plane = doc.getObject("XZ_Plane")
    if not xz_plane:
        # Fallback if XZ_Plane doesn't exist (rare in 1.1 template)
        # Create it manually if needed, but standard docs have it.
        # If missing, we can use XY and rotate.
        # Let's assume standard template exists.
        pass

    sketch_disk.Placement = App.Placement()
    sketch_disk.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 90) # Normal points to Y
    sketch_disk.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 90) # Ensure normal is Y
    # Actually, simpler: Placement = App.Placement(App.Vector(0,0,0))
    # And set AttachmentSupport to XZ_Plane.
    sketch_disk.AttachmentSupport = (xz_plane, [""])
    sketch_disk.MapMode = "FlatFace"
    
    # Outer Circle
    outer_diam = params.drive_lug_inner_arc_radius * 2 # Base description says outer edge is drive_lug_inner_arc_radius
    # Wait, description: "outer radius is drive_lug_inner_arc_radius"
    # But edit instruction says: "outer radius is drive_lug_inner_arc_radius, which becomes the valley radius"
    # So Base Outer Radius = 33.0.
    # Edit will change this to a lobed shape.
    
    r_outer_base = params.drive_lug_inner_arc_radius
    sketch_disk.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_outer_base), False)
    
    # Inner Bore
    r_inner = params.center_bore_diameter / 2.0
    sketch_disk.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_inner), False)
    
    # Constraints
    # Coincident centers
    sketch_disk.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    # Concentric
    sketch_disk.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center to center
    sketch_disk.addConstraint(Sketcher.Constraint("Concentric", 0, 1, 1, 0)) # Circle 0 to Circle 1
    
    # Pad to thickness
    pad_disk = body.newObject("PartDesign::Pad", "Pad_Disk")
    pad_disk.Profile = sketch_disk
    pad_disk.Length = params.disk_thickness
    pad_disk.Midplane = False
    pad_disk.Reversed = False
    
    # 2. Create Hub Sketch (Negative Y face, Z=0 in local, Y=-thickness/2 global? No, "Negative-Y circular face at Y=0")
    # Wait, "flange spanning Y = 0 to Y = disk_thickness". 
    # "On the negative-Y circular face at Y = 0" -> This implies the face is at Y=0? 
    # If flange is 0 to thickness, the negative Y face would be at 0? That's the start.
    # Usually flanges are symmetric or 0 to T. 
    # "raised annular hub ... extending toward -Y".
    # So Hub starts at Y=0 and goes to Y = -inner_disk_thickness.
    
    sketch_hub = body.newObject("Sketcher::SketchObject", "Hub_Sketch")
    # Reference the face at Y=0 (Top of the pad? No, Pad is 0 to T. Top is T. Bottom is 0.)
    # If flange is 0 to T, the face at Y=0 is the bottom.
    # "On the negative-Y circular face at Y = 0" -> This is the face with normal -Y.
    # So we sketch on the face of the Pad_Disk at Y=0.
    
    # Get the face of the pad at Y=0
    # We can use the body's face or reference the pad's result.
    # Best to attach to the face of the Pad_Disk.
    # In PartDesign, we can reference the face of a feature.
    # Let's find the face at Y=0. Since Pad is 0 to T, Y=0 is the bottom.
    
    # We need to get the face ID or reference. 
    # Easier: Sketch on XZ plane at Y = -inner_disk_thickness/2? No.
    # Let's attach to the face of Pad_Disk.
    # We need to get the face. 
    # Let's assume we can reference the face of Pad_Disk.
    # But Pad_Disk is not yet computed fully if we are building sequentially? 
    # We recompute after Pad_Disk.
    
    # Let's use the face of Pad_Disk.
    # Face ID is tricky to get dynamically without loops.
    # Alternative: Create a Plane parallel to XZ at Y = 0?
    # Or just attach to Pad_Disk and specify offset.
    # sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0))
    # But we need to align with the face.
    
    # Let's use the Pad_Disk result.
    # We need to find the face at Y=0.
    # Let's assume we can use the Pad_Disk object.
    # We will attach to the face of Pad_Disk.
    # How to specify the face? 
    # We can use the `AttachmentSupport` with a face from the result of Pad_Disk.
    # But we don't know the face ID yet.
    # Let's use a workaround: Create a sketch on XZ plane, then move it to Y=0?
    # Or attach to the face of the Pad.
    
    # Let's try to get the face.
    # We need to recompute Pad_Disk first.
    doc.recompute()
    
    # Find face at Y=0 on Pad_Disk
    # Pad_Disk creates a solid. The face at Y=0 is the one with normal -Y.
    # We can iterate faces of Pad_Disk.
    # But we need the face object.
    
    # Let's use a simpler approach: 
    # Create the sketch on the XZ plane, but offset the placement to Y = -inner_disk_thickness?
    # No, it needs to be on the face.
    
    # Let's use the `Face` object.
    # We can get the face from the body or the pad.
    # Let's assume we can reference the face of Pad_Disk.
    # Since we can't easily get the face ID without a loop, let's try to attach to the Pad_Disk face directly.
    # FreeCAD 1.1 API: sketch.AttachmentSupport = (pad, ["FaceIndex"])
    # We don't know the index.
    
    # Alternative: Use the Pad_Disk's result to create a plane? No.
    # Let's use the fact that Pad_Disk is at Y=0 to Y=T.
    # The face at Y=0 is the bottom.
    # We can create a sketch on the XZ plane, then move it to Y=0? 
    # But we need to be on the surface.
    
    # Let's use the `Face` object from the Pad_Disk.
    # We will iterate the topological shells of the Pad_Disk to find the face at Y=0.
    # This is robust.
    
    pad_shape = Part.Shape(pad_disk)
    # Find face with normal close to (0, -1, 0) and center Y close to 0
    target_face = None
    for face in pad_shape.Faces:
        if abs(face.Center.Point.Y) < 0.001:
            # Check normal
            # Face.normalAt() returns a vector
            n = face.normalAt()
            if n.Y < -0.99:
                target_face = face
                break
    
    if target_face:
        sketch_hub.Placement = App.Placement()
        sketch_hub.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 90) # Normal Y
        sketch_hub.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 90)
        # Actually, if we attach to a face, the Placement is relative to the face.
        # But we need to specify the face in AttachmentSupport.
        # We can pass the face object itself.
        sketch_hub.AttachmentSupport = (target_face, [""])
        sketch_hub.MapMode = "FlatFace"
    else:
        # Fallback: Create a plane at Y=0? No, it's already there.
        # Just attach to XZ plane at Y=0? 
        # Let's assume the face detection worked.
        pass
        
    # Hub Geometry
    # "raised annular hub ... level with inner_disk_thickness"
    # "inner_disk_thickness = 15.0"
    # "concentric raised annular hub-and-drive-lug"
    # "straight outer-tip edge is perpendicular to the seed ray, has drive_lug_width"
    # "midpoint drive_lug_tip_edge_center_y from the coupling axis"
    # "Run the lug sides inward to the concentric hub valley circle of disk_outer_arc_radius"
    
    # So the Hub Sketch has:
    # 1. Outer Lobe Shape (Rectangular lugs with rounded ends?)
    # 2. Inner Circle (Valley) = disk_outer_arc_radius
    
    # Lugs:
    # number_of_drive_lugs = 6
    # seed center angle = 90 deg
    # width = 4.0
    # tip edge center y = 15.0 (from axis) -> This is the outer radius of the lug?
    # "midpoint drive_lug_tip_edge_center_y from the coupling axis"
    # So the outer radius of the lug is 15.0.
    # "straight outer-tip edge is perpendicular to the seed ray"
    # "Run the lug sides inward to the concentric hub valley circle of disk_outer_arc_radius"
    # Valley radius = 12.5.
    
    # So each lug is a rectangle from R=12.5 to R=15.0, with width 4.0?
    # Width is along the arc or radial? "drive_lug_width" usually radial for rectangular lugs.
    # "straight outer-tip edge ... perpendicular to the seed ray" -> Yes, radial sides.
    
    # We need to draw a sketch with 6 such lugs.
    # This is a pattern.
    # We can draw one lug and pattern it.
    
    # Seed Lug:
    # Center angle = 90 deg.
    # Outer radius = 15.0.
    # Inner radius = 12.5.
    # Width = 4.0.
    # So the arc span of the lug = Width / Outer_Radius? No, radial width.
    # The chord length at the outer edge?
    # "straight outer-tip edge ... perpendicular to the seed ray"
    # So the outer edge is a line segment perpendicular to the ray at angle 90.
    # The length of this segment?
    # "Run the lug sides inward to the concentric hub valley circle"
    # So the sides are radial lines from R=12.5 to R=15.0?
    # If sides are radial, then the outer edge is an arc? 
    # "straight outer-tip edge is perpendicular to the seed ray" -> If the edge is straight and perpendicular to the ray, it's a chord.
    # But if the sides are radial, the outer edge is an arc.
    # Contradiction? 
    # "straight outer-tip edge" implies the tip is a straight line.
    # "Run the lug sides inward" implies the sides are lines.
    # If sides are radial lines, and the tip is a straight line perpendicular to the ray, then the shape is a trapezoid (in polar).
    # Actually, if sides are radial lines, they are lines passing through the origin.
    # The distance between two radial lines at angle theta is R * theta.
    # If the outer edge is a straight line perpendicular to the
