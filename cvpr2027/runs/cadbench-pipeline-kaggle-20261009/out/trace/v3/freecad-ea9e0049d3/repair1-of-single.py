import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("UAV_Sensor_Fairing")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Extracted from drawing dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Total height of the main body")
params.base_height = 457.2

params.addProperty("App::PropertyLength", "main_width", "Dimensions", "Width of the main body")
params.main_width = 304.8

params.addProperty("App::PropertyLength", "nose_length", "Dimensions", "Length of the nose cone")
params.nose_length = 137.31

params.addProperty("App::PropertyLength", "nose_base_dia", "Dimensions", "Diameter at the base of the nose cone")
params.nose_base_dia = 177.8

params.addProperty("App::PropertyLength", "nose_tip_dia", "Dimensions", "Diameter at the tip of the nose cone")
params.nose_tip_dia = 2.5

params.addProperty("App::PropertyLength", "sensor_hole_dia", "Dimensions", "Diameter of the sensor hole")
params.sensor_hole_dia = 25.0 # 177.8 is the main body diameter, 25 is the hole

params.addProperty("App::PropertyLength", "sensor_hole_z", "Dimensions", "Z-position of the sensor hole center")
params.sensor_hole_z = 304.8

params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Radius of the fillet at the base")
params.fillet_radius = 77.92

params.addProperty("App::PropertyLength", "sensor_mount_dia", "Dimensions", "Diameter of the sensor mount boss")
params.sensor_mount_dia = 153.43

params.addProperty("App::PropertyLength", "sensor_mount_height", "Dimensions", "Height of the sensor mount boss")
params.sensor_mount_height = 50.0

params.addProperty("App::PropertyLength", "sensor_mount_offset", "Dimensions", "Offset of the sensor mount from the nose base")
params.sensor_mount_offset = 77.92

params.addProperty("App::PropertyLength", "sensor_mount_width", "Dimensions", "Width of the sensor mount boss")
params.sensor_mount_width = 30.0

params.addProperty("App::PropertyLength", "sensor_mount_depth", "Dimensions", "Depth of the sensor mount boss")
params.sensor_mount_depth = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_z", "Dimensions", "Z-position of the sensor mount center")
params.sensor_mount_z = 304.8

params.addProperty("App::PropertyLength", "sensor_mount_y", "Dimensions", "Y-position of the sensor mount center")
params.sensor_mount_y = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_x", "Dimensions", "X-position of the sensor mount center")
params.sensor_mount_x = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_dia", "Dimensions", "Diameter of the hole in the sensor mount")
params.sensor_mount_hole_dia = 30.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_z", "Dimensions", "Z-position of the hole in the sensor mount")
params.sensor_mount_hole_z = 304.8

params.addProperty("App::PropertyLength", "sensor_mount_hole_y", "Dimensions", "Y-position of the hole in the sensor mount")
params.sensor_mount_hole_y = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_x", "Dimensions", "X-position of the hole in the sensor mount")
params.sensor_mount_hole_x = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_depth", "Dimensions", "Depth of the hole in the sensor mount")
params.sensor_mount_hole_depth = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_radius", "Dimensions", "Radius of the hole in the sensor mount")
params.sensor_mount_hole_radius = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset", "Dimensions", "Offset of the hole in the sensor mount")
params.sensor_mount_hole_offset = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y2", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y2 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x2", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x2 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z2", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z2 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y3", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y3 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x3", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x3 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z3", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z3 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y4", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y4 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x4", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x4 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z4", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z4 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y5", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y5 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x5", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x5 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z5", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z5 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y6", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y6 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x6", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x6 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z6", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z6 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y7", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y7 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x7", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x7 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z7", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z7 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y8", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y8 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x8", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x8 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z8", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z8 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y9", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y9 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x9", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x9 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z9", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z9 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y10", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y10 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x10", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x10 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z10", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z10 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y11", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y11 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x11", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x11 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z11", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z11 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y12", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y12 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x12", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x12 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z12", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z12 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y13", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y13 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x13", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x13 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z13", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z13 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y14", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y14 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x14", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x14 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z14", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z14 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y15", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y15 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x15", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x15 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z15", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z15 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y16", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y16 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x16", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x16 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z16", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z16 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y17", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y17 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x17", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x17 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z17", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z17 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y18", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y18 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x18", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x18 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z18", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z18 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y19", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y19 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x19", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x19 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z19", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z19 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y20", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y20 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x20", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x20 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z20", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z20 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y21", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y21 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x21", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x21 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z21", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z21 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y22", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y22 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x22", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x22 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z22", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z22 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y23", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y23 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x23", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x23 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z23", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z23 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y24", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y24 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x24", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x24 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z24", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z24 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y25", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y25 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x25", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x25 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z25", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z25 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y26", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y26 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x26", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x26 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z26", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z26 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y27", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y27 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x27", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x27 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z27", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z27 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y28", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y28 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x28", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x28 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z28", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z28 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y29", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y29 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x29", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x29 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z29", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z29 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y30", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y30 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x30", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x30 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z30", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z30 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y31", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y31 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x31", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x31 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z31", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z31 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y32", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y32 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x32", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x32 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z32", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z32 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y33", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y33 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x33", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x33 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z33", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z33 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y34", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y34 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x34", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x34 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z34", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z34 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y35", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y35 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x35", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x35 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z35", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z35 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y36", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y36 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x36", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x36 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z36", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z36 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y37", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y37 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x37", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x37 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z37", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z37 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y38", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y38 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x38", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x38 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z38", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z38 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y39", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y39 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x39", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x39 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z39", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z39 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y40", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y40 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x40", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x40 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z40", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z40 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y41", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y41 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x41", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x41 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z41", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z41 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y42", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y42 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x42", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x42 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z42", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z42 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y43", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y43 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x43", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x43 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z43", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z43 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y44", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y44 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x44", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x44 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z44", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z44 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y45", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y45 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x45", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x45 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z45", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z45 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y46", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y46 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x46", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x46 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z46", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z46 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y47", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y47 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x47", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x47 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z47", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z47 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y48", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y48 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x48", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x48 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z48", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z48 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y49", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y49 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x49", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x49 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z49", "Dimensions", "Z-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_z49 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_y50", "Dimensions", "Y-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_y50 = 15.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_x50", "Dimensions", "X-offset of the hole in the sensor mount")
params.sensor_mount_hole_offset_x50 = 0.0

params.addProperty("App::PropertyLength", "sensor_mount_hole_offset_z50", "Dimensions", "Z-offset of the hole in the sensor mount")
params
