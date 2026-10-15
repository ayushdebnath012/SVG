from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# Create a new document
doc = App.newDocument("FPV_Mount")
doc.Label = "FPV_Receiver_Mount_Bracket"

# Create a body
body = doc.addObject("PartDesign::Body", "Body")

# Add parameters
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Total length")
params.length = 42.34
params.addProperty("App::PropertyLength", "width", "Dimensions", "Width")
params.width = 20.0
params.addProperty("App::PropertyLength", "height", "Dimensions", "Height")
params.height = 2.0
params.addProperty("App::PropertyLength", "arm_length", "Dimensions", "Arm length")
params.arm_length = 19.85
params.addProperty("App::PropertyLength", "arm_width", "Dimensions", "Arm width")
params.arm_width = 16.0
params.addProperty("App::PropertyLength", "base_radius", "Dimensions", "Base radius")
params.base_radius = 6.5
params.addProperty("App::PropertyLength", "arm_radius", "Dimensions", "Arm radius")
params.arm_radius = 5.0
params.addProperty("App::PropertyLength", "hole_dia", "Dimensions", "Hole diameter")
params.hole_dia = 4.0
params.addProperty("App::PropertyLength", "mount_hole_dia", "Dimensions", "Mount hole diameter")
params.mount_hole_dia = 3.0
params.addProperty("App::PropertyLength", "fillet_r", "Dimensions", "Fillet radius")
params.fillet_r = 2.5
params.addProperty("App::PropertyLength", "chamfer_d", "Dimensions", "Chamfer distance")
params.chamfer_d = 0.7
params.addProperty("App::PropertyLength", "chamfer_h", "Dimensions", "Chamfer height")
params.chamfer_h = 1.2
params.addProperty("App::PropertyLength", "tube_dia", "Dimensions", "Tube diameter")
params.tube_dia = 3.0
params.addProperty("App::PropertyLength", "tube_wall", "Dimensions", "Tube wall thickness")
params.tube_wall = 1.5
params.addProperty("App::PropertyLength", "tube_length", "Dimensions", "Tube length")
params.tube_length = 4.0
params.addProperty("App::PropertyLength", "tube_offset", "Dimensions", "Tube offset")
params.tube_offset = 5.0
params.addProperty("App::PropertyLength", "tube_mount_dia", "Dimensions", "Mount hole in tube")
params.tube_mount_dia = 2.0
params.addProperty("App::PropertyLength", "tube_wall_offset", "Dimensions", "Wall offset")
params.tube_wall_offset = 2.0
params.addProperty("App::PropertyLength", "tube_mount_offset", "Dimensions", "Mount offset")
params.tube_mount_offset = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia", "Dimensions", "Mount hole in tube")
params.tube_mount_hole_dia = 3.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth", "Dimensions", "Mount hole depth")
params.tube_mount_hole_depth = 3.0
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_2", "Dimensions", "Mount hole diameter 2")
params.tube_mount_hole_dia_2 = 4.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_2", "Dimensions", "Mount hole depth 2")
params.tube_mount_hole_depth_2 = 2.0
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_3", "Dimensions", "Mount hole diameter 3")
params.tube_mount_hole_dia_3 = 5.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_3", "Dimensions", "Mount hole depth 3")
params.tube_mount_hole_depth_3 = 1.0
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_4", "Dimensions", "Mount hole diameter 4")
params.tube_mount_hole_dia_4 = 6.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_4", "Dimensions", "Mount hole depth 4")
params.tube_mount_hole_depth_4 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_5", "Dimensions", "Mount hole diameter 5")
params.tube_mount_hole_dia_5 = 7.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_5", "Dimensions", "Mount hole depth 5")
params.tube_mount_hole_depth_5 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_6", "Dimensions", "Mount hole diameter 6")
params.tube_mount_hole_dia_6 = 8.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_6", "Dimensions", "Mount hole depth 6")
params.tube_mount_hole_depth_6 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_7", "Dimensions", "Mount hole diameter 7")
params.tube_mount_hole_dia_7 = 9.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_7", "Dimensions", "Mount hole depth 7")
params.tube_mount_hole_depth_7 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_8", "Dimensions", "Mount hole diameter 8")
params.tube_mount_hole_dia_8 = 10.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_8", "Dimensions", "Mount hole depth 8")
params.tube_mount_hole_depth_8 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_9", "Dimensions", "Mount hole diameter 9")
params.tube_mount_hole_dia_9 = 11.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_9", "Dimensions", "Mount hole depth 9")
params.tube_mount_hole_depth_9 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_10", "Dimensions", "Mount hole diameter 10")
params.tube_mount_hole_dia_10 = 12.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_10", "Dimensions", "Mount hole depth 10")
params.tube_mount_hole_depth_10 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_11", "Dimensions", "Mount hole diameter 11")
params.tube_mount_hole_dia_11 = 13.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_11", "Dimensions", "Mount hole depth 11")
params.tube_mount_hole_depth_11 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_12", "Dimensions", "Mount hole diameter 12")
params.tube_mount_hole_dia_12 = 14.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_12", "Dimensions", "Mount hole depth 12")
params.tube_mount_hole_depth_12 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_13", "Dimensions", "Mount hole diameter 13")
params.tube_mount_hole_dia_13 = 15.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_13", "Dimensions", "Mount hole depth 13")
params.tube_mount_hole_depth_13 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_14", "Dimensions", "Mount hole diameter 14")
params.tube_mount_hole_dia_14 = 16.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_14", "Dimensions", "Mount hole depth 14")
params.tube_mount_hole_depth_14 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_15", "Dimensions", "Mount hole diameter 15")
params.tube_mount_hole_dia_15 = 17.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_15", "Dimensions", "Mount hole depth 15")
params.tube_mount_hole_depth_15 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_16", "Dimensions", "Mount hole diameter 16")
params.tube_mount_hole_dia_16 = 18.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_16", "Dimensions", "Mount hole depth 16")
params.tube_mount_hole_depth_16 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_17", "Dimensions", "Mount hole diameter 17")
params.tube_mount_hole_dia_17 = 19.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_17", "Dimensions", "Mount hole depth 17")
params.tube_mount_hole_depth_17 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_18", "Dimensions", "Mount hole diameter 18")
params.tube_mount_hole_dia_18 = 20.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_18", "Dimensions", "Mount hole depth 18")
params.tube_mount_hole_depth_18 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_19", "Dimensions", "Mount hole diameter 19")
params.tube_mount_hole_dia_19 = 21.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_19", "Dimensions", "Mount hole depth 19")
params.tube_mount_hole_depth_19 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_20", "Dimensions", "Mount hole diameter 20")
params.tube_mount_hole_dia_20 = 22.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_20", "Dimensions", "Mount hole depth 20")
params.tube_mount_hole_depth_20 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_21", "Dimensions", "Mount hole diameter 21")
params.tube_mount_hole_dia_21 = 23.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_21", "Dimensions", "Mount hole depth 21")
params.tube_mount_hole_depth_21 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_22", "Dimensions", "Mount hole diameter 22")
params.tube_mount_hole_dia_22 = 24.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_22", "Dimensions", "Mount hole depth 22")
params.tube_mount_hole_depth_22 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_23", "Dimensions", "Mount hole diameter 23")
params.tube_mount_hole_dia_23 = 25.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_23", "Dimensions", "Mount hole depth 23")
params.tube_mount_hole_depth_23 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_24", "Dimensions", "Mount hole diameter 24")
params.tube_mount_hole_dia_24 = 26.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_24", "Dimensions", "Mount hole depth 24")
params.tube_mount_hole_depth_24 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_25", "Dimensions", "Mount hole diameter 25")
params.tube_mount_hole_dia_25 = 27.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_25", "Dimensions", "Mount hole depth 25")
params.tube_mount_hole_depth_25 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_26", "Dimensions", "Mount hole diameter 26")
params.tube_mount_hole_dia_26 = 28.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_26", "Dimensions", "Mount hole depth 26")
params.tube_mount_hole_depth_26 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_27", "Dimensions", "Mount hole diameter 27")
params.tube_mount_hole_dia_27 = 29.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_27", "Dimensions", "Mount hole depth 27")
params.tube_mount_hole_depth_27 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_28", "Dimensions", "Mount hole diameter 28")
params.tube_mount_hole_dia_28 = 30.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_28", "Dimensions", "Mount hole depth 28")
params.tube_mount_hole_depth_28 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_29", "Dimensions", "Mount hole diameter 29")
params.tube_mount_hole_dia_29 = 31.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_29", "Dimensions", "Mount hole depth 29")
params.tube_mount_hole_depth_29 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_30", "Dimensions", "Mount hole diameter 30")
params.tube_mount_hole_dia_30 = 32.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_30", "Dimensions", "Mount hole depth 30")
params.tube_mount_hole_depth_30 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_31", "Dimensions", "Mount hole diameter 31")
params.tube_mount_hole_dia_31 = 33.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_31", "Dimensions", "Mount hole depth 31")
params.tube_mount_hole_depth_31 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_32", "Dimensions", "Mount hole diameter 32")
params.tube_mount_hole_dia_32 = 34.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_32", "Dimensions", "Mount hole depth 32")
params.tube_mount_hole_depth_32 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_33", "Dimensions", "Mount hole diameter 33")
params.tube_mount_hole_dia_33 = 35.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_33", "Dimensions", "Mount hole depth 33")
params.tube_mount_hole_depth_33 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_34", "Dimensions", "Mount hole diameter 34")
params.tube_mount_hole_dia_34 = 36.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_34", "Dimensions", "Mount hole depth 34")
params.tube_mount_hole_depth_34 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_35", "Dimensions", "Mount hole diameter 35")
params.tube_mount_hole_dia_35 = 37.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_35", "Dimensions", "Mount hole depth 35")
params.tube_mount_hole_depth_35 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_36", "Dimensions", "Mount hole diameter 36")
params.tube_mount_hole_dia_36 = 38.0
params.addProperty("App::PropertyLength", "tube_mount_hole_depth_36", "Dimensions", "Mount hole depth 36")
params.tube_mount_hole_depth_36 = 0.5
params.addProperty("App::PropertyLength", "tube_mount_hole_dia_37", "Dimensions", "Mount hole diameter 37")
params.tube_mount_hole_dia_37 = 39.0
params.addProperty("App::PropertyLength", "
