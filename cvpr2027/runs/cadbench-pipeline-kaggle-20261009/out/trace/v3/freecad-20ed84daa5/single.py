import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Define parameters as document objects to ensure editability
params = App.ActiveDocument.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "driver_bit_overall_length", "Dimensions", "Total length")
params.driver_bit_overall_length = 40.13
params.addProperty("App::PropertyLength", "rear_section_radius", "Dimensions", "Rear radius")
params.rear_section_radius = 1.75
params.addProperty("App::PropertyLength", "rear_taper_axial_length", "Dimensions", "Rear taper length")
params.rear_taper_axial_length = 0.38
params.addProperty("App::PropertyLength", "main_shank_radius", "Dimensions", "Main shank radius")
params.main_shank_radius = 1.98
params.addProperty("App::PropertyLength", "main_shank_length", "Dimensions", "Main shank length")
params.main_shank_length = 20.32
params.addProperty("App::PropertyLength", "reduced_shank_transition_length", "Dimensions", "Transition length")
params.reduced_shank_transition_length = 0.99
params.addProperty("App::PropertyLength", "reduced_shank_radius", "Dimensions", "Reduced shank radius")
params.reduced_shank_radius = 0.99
params.addProperty("App::PropertyLength", "tip_taper_axial_length", "Dimensions", "Tip taper length")
params.tip_taper_axial_length = 5.08
params.addProperty("App::PropertyInteger", "ring_groove_count", "Dimensions", "Number of grooves")
params.ring_groove_count = 2
params.addProperty("App::PropertyLength", "ring_groove_arc_radius", "Dimensions", "Groove arc radius")
params.ring_groove_arc_radius = 0.64
params.addProperty("App::PropertyLength", "first_ring_groove_axial_offset", "Dimensions", "First groove offset")
params.first_ring_groove_axial_offset = 6.40
params.addProperty("App::PropertyLength", "ring_groove_pitch", "Dimensions", "Groove pitch")
params.ring_groove_pitch = 3.10
params.addProperty("App::PropertyAngle", "ring_groove_half_angle", "Dimensions", "Groove half angle")
params.ring_groove_half_angle = 36.8698976
params.addProperty("App::PropertyInteger", "driver_lobe_count", "Dimensions", "Lobe count")
params.driver_lobe_count = 5
params.addProperty("App::PropertyLength", "driver_lobe_root_arc_radius", "Dimensions", "Lobe root radius")
params.driver_lobe_root_arc_radius = 0.05
params.addProperty("App::PropertyLength", "driver_lobe_root_center_radial_offset", "Dimensions", "Root center offset")
params.driver_lobe_root_center_radial_offset = 0.38
params.addProperty("App::PropertyLength", "driver_lobe_outer_arc_radius", "Dimensions", "Lobe outer radius")
params.driver_lobe_outer_arc_radius = 0.61
params.addProperty("App::PropertyAngle", "driver_lobe_outer_half_angle", "Dimensions", "Lobe outer half angle")
params.driver_lobe_outer_half_angle = 19.4989779
params.addProperty("App::PropertyLength", "driver_lobe_sweep_path_arc_radius", "Dimensions", "Sweep path radius")
params.driver_lobe_sweep_path_arc_radius = 25.40
params.addProperty("App::PropertyLength", "driver_lobe_sweep_path_center_x", "Dimensions", "Sweep path center X")
params.driver_lobe_sweep_path_center_x = 42.91
params.addProperty("App::PropertyLength", "driver_lobe_sweep_path_center_y", "Dimensions", "Sweep path center Y")
params.driver_lobe_sweep_path_center_y = 25.63
params.addProperty("App::PropertyAngle", "driver_lobe_sweep_path_start_angle", "Dimensions", "Sweep path start angle")
params.driver_lobe_sweep_path_start_angle = -108.5085355
params.addProperty("App::PropertyAngle", "driver_lobe_sweep_path_end_angle", "Dimensions", "Sweep path end angle")
params.driver_lobe_sweep_path_end_angle = -96.2678608
params.addProperty("App::PropertyLength", "driver_profile_extrusion_height", "Dimensions", "Crown height")
params.driver_profile_extrusion_height = 1.52
params.addProperty("App::PropertyLength", "driver_profile_z_offset", "Dimensions", "Crown Z offset")
params.driver_profile_z_offset = -0.76
params.addProperty("App::PropertyLength", "driver_crown_axial_center", "Dimensions", "Crown axial center")
params.driver_crown_axial_center = 12.98
params.addProperty("App::PropertyLength", "driver_crown_half_width", "Dimensions", "Crown half width")
params.driver_crown_half_width = 2.06
params.addProperty("App::PropertyLength", "driver_crown_arc_radius", "Dimensions", "Crown arc radius")
params.driver_crown_arc_radius = 4.42
params.addProperty("App::PropertyLength", "driver_crown_base_radius", "Dimensions", "Crown base radius")
params.driver_crown_base_radius = 1.44
params.addProperty("App::PropertyLength", "driver_lobe_cutout_arc_radius", "Dimensions", "Cutout arc radius")
params.driver_lobe_cutout_arc_radius = 2.72
params.addProperty("App::PropertyAngle", "driver_lower_lobe_cutout_half_angle", "Dimensions", "Lower cutout half angle")
params.driver_lower_lobe_cutout_half_angle = 44.71061805

# Create Document
doc = App.newDocument("DriverBit")
doc.Label = "DriverBit"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Helper to create sketches
def create_sketch(name, plane, offset=0):
    s = body.newObject("Sketcher::SketchObject", name)
    s.Placement = App.Placement(App.Vector(0, 0, offset))
    s.Placement.Rotation = App.Rotation()
    s.Placement.Rotation.X = 0
    s.Placement.Rotation.Y = 0
    s.Placement.Rotation.Z = 0
    s.Placement.Rotation.Angle = 0
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
    s.Placement.Rotation.Q.Z = 0
    s.Placement.Rotation.Q.W = 1
    s.Placement.Rotation.Q = App.Rotation()
    s.Placement.Rotation.Q.X = 0
    s.Placement.Rotation.Q.Y = 0
