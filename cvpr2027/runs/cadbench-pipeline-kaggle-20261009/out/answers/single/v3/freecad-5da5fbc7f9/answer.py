import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("CompanionEnclosure")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Extracted from the drawing dimensions
params = body.newObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "base_width", "Dimensions", "Main chassis width")
params.base_width = 85.55
params.addProperty("App::PropertyLength", "base_depth", "Dimensions", "Main chassis depth")
params.base_depth = 57.75
params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Main chassis height")
params.base_height = 42.1
params.addProperty("App::PropertyLength", "fan_diameter", "Dimensions", "Fan diameter")
params.fan_diameter = 47.75
params.addProperty("App::PropertyLength", "fan_mount_diameter", "Dimensions", "Fan mounting hole diameter")
params.fan_mount_diameter = 10.6
params.addProperty("App::PropertyLength", "fan_mount_thickness", "Dimensions", "Fan mounting plate thickness")
params.fan_mount_thickness = 2.0
params.addProperty("App::PropertyLength", "fan_mount_depth", "Dimensions", "Fan mounting plate depth")
params.fan_mount_depth = 15.0
params.addProperty("App::PropertyLength", "fan_mount_width", "Dimensions", "Fan mounting plate width")
params.fan_mount_width = 50.0
params.addProperty("App::PropertyLength", "fan_mount_height", "Dimensions", "Fan mounting plate height")
params.fan_mount_height = 50.0
params.addProperty("App::PropertyLength", "fan_mount_radius", "Dimensions", "Fan mounting plate corner radius")
params.fan_mount_radius = 5.25
params.addProperty("App::PropertyLength", "fan_mount_hole_spacing", "Dimensions", "Fan mounting hole spacing")
params.fan_mount_hole_spacing = 5.25
params.addProperty("App::PropertyLength", "fan_mount_hole_offset", "Dimensions", "Fan mounting hole offset from center")
params.fan_mount_hole_offset = 3.0
params.addProperty("App::PropertyLength", "fan_mount_hole_radius", "Dimensions", "Fan mounting hole radius")
params.fan_mount_hole_radius = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_2", "Dimensions", "Fan mounting hole radius 2")
params.fan_mount_hole_radius_2 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_3", "Dimensions", "Fan mounting hole radius 3")
params.fan_mount_hole_radius_3 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_4", "Dimensions", "Fan mounting hole radius 4")
params.fan_mount_hole_radius_4 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_5", "Dimensions", "Fan mounting hole radius 5")
params.fan_mount_hole_radius_5 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_6", "Dimensions", "Fan mounting hole radius 6")
params.fan_mount_hole_radius_6 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_7", "Dimensions", "Fan mounting hole radius 7")
params.fan_mount_hole_radius_7 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_8", "Dimensions", "Fan mounting hole radius 8")
params.fan_mount_hole_radius_8 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_9", "Dimensions", "Fan mounting hole radius 9")
params.fan_mount_hole_radius_9 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_10", "Dimensions", "Fan mounting hole radius 10")
params.fan_mount_hole_radius_10 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_11", "Dimensions", "Fan mounting hole radius 11")
params.fan_mount_hole_radius_11 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_12", "Dimensions", "Fan mounting hole radius 12")
params.fan_mount_hole_radius_12 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_13", "Dimensions", "Fan mounting hole radius 13")
params.fan_mount_hole_radius_13 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_14", "Dimensions", "Fan mounting hole radius 14")
params.fan_mount_hole_radius_14 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_15", "Dimensions", "Fan mounting hole radius 15")
params.fan_mount_hole_radius_15 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_16", "Dimensions", "Fan mounting hole radius 16")
params.fan_mount_hole_radius_16 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_17", "Dimensions", "Fan mounting hole radius 17")
params.fan_mount_hole_radius_17 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_18", "Dimensions", "Fan mounting hole radius 18")
params.fan_mount_hole_radius_18 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_19", "Dimensions", "Fan mounting hole radius 19")
params.fan_mount_hole_radius_19 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_20", "Dimensions", "Fan mounting hole radius 20")
params.fan_mount_hole_radius_20 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_21", "Dimensions", "Fan mounting hole radius 21")
params.fan_mount_hole_radius_21 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_22", "Dimensions", "Fan mounting hole radius 22")
params.fan_mount_hole_radius_22 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_23", "Dimensions", "Fan mounting hole radius 23")
params.fan_mount_hole_radius_23 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_24", "Dimensions", "Fan mounting hole radius 24")
params.fan_mount_hole_radius_24 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_25", "Dimensions", "Fan mounting hole radius 25")
params.fan_mount_hole_radius_25 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_26", "Dimensions", "Fan mounting hole radius 26")
params.fan_mount_hole_radius_26 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_27", "Dimensions", "Fan mounting hole radius 27")
params.fan_mount_hole_radius_27 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_28", "Dimensions", "Fan mounting hole radius 28")
params.fan_mount_hole_radius_28 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_29", "Dimensions", "Fan mounting hole radius 29")
params.fan_mount_hole_radius_29 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_30", "Dimensions", "Fan mounting hole radius 30")
params.fan_mount_hole_radius_30 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_31", "Dimensions", "Fan mounting hole radius 31")
params.fan_mount_hole_radius_31 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_32", "Dimensions", "Fan mounting hole radius 32")
params.fan_mount_hole_radius_32 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_33", "Dimensions", "Fan mounting hole radius 33")
params.fan_mount_hole_radius_33 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_34", "Dimensions", "Fan mounting hole radius 34")
params.fan_mount_hole_radius_34 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_35", "Dimensions", "Fan mounting hole radius 35")
params.fan_mount_hole_radius_35 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_36", "Dimensions", "Fan mounting hole radius 36")
params.fan_mount_hole_radius_36 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_37", "Dimensions", "Fan mounting hole radius 37")
params.fan_mount_hole_radius_37 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_38", "Dimensions", "Fan mounting hole radius 38")
params.fan_mount_hole_radius_38 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_39", "Dimensions", "Fan mounting hole radius 39")
params.fan_mount_hole_radius_39 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_40", "Dimensions", "Fan mounting hole radius 40")
params.fan_mount_hole_radius_40 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_41", "Dimensions", "Fan mounting hole radius 41")
params.fan_mount_hole_radius_41 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_42", "Dimensions", "Fan mounting hole radius 42")
params.fan_mount_hole_radius_42 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_43", "Dimensions", "Fan mounting hole radius 43")
params.fan_mount_hole_radius_43 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_44", "Dimensions", "Fan mounting hole radius 44")
params.fan_mount_hole_radius_44 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_45", "Dimensions", "Fan mounting hole radius 45")
params.fan_mount_hole_radius_45 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_46", "Dimensions", "Fan mounting hole radius 46")
params.fan_mount_hole_radius_46 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_47", "Dimensions", "Fan mounting hole radius 47")
params.fan_mount_hole_radius_47 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_48", "Dimensions", "Fan mounting hole radius 48")
params.fan_mount_hole_radius_48 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_49", "Dimensions", "Fan mounting hole radius 49")
params.fan_mount_hole_radius_49 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_50", "Dimensions", "Fan mounting hole radius 50")
params.fan_mount_hole_radius_50 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_51", "Dimensions", "Fan mounting hole radius 51")
params.fan_mount_hole_radius_51 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_52", "Dimensions", "Fan mounting hole radius 52")
params.fan_mount_hole_radius_52 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_53", "Dimensions", "Fan mounting hole radius 53")
params.fan_mount_hole_radius_53 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_54", "Dimensions", "Fan mounting hole radius 54")
params.fan_mount_hole_radius_54 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_55", "Dimensions", "Fan mounting hole radius 55")
params.fan_mount_hole_radius_55 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_56", "Dimensions", "Fan mounting hole radius 56")
params.fan_mount_hole_radius_56 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_57", "Dimensions", "Fan mounting hole radius 57")
params.fan_mount_hole_radius_57 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_58", "Dimensions", "Fan mounting hole radius 58")
params.fan_mount_hole_radius_58 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_59", "Dimensions", "Fan mounting hole radius 59")
params.fan_mount_hole_radius_59 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_60", "Dimensions", "Fan mounting hole radius 60")
params.fan_mount_hole_radius_60 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_61", "Dimensions", "Fan mounting hole radius 61")
params.fan_mount_hole_radius_61 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_62", "Dimensions", "Fan mounting hole radius 62")
params.fan_mount_hole_radius_62 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_63", "Dimensions", "Fan mounting hole radius 63")
params.fan_mount_hole_radius_63 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_64", "Dimensions", "Fan mounting hole radius 64")
params.fan_mount_hole_radius_64 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_65", "Dimensions", "Fan mounting hole radius 65")
params.fan_mount_hole_radius_65 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_66", "Dimensions", "Fan mounting hole radius 66")
params.fan_mount_hole_radius_66 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_67", "Dimensions", "Fan mounting hole radius 67")
params.fan_mount_hole_radius_67 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_68", "Dimensions", "Fan mounting hole radius 68")
params.fan_mount_hole_radius_68 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_69", "Dimensions", "Fan mounting hole radius 69")
params.fan_mount_hole_radius_69 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_70", "Dimensions", "Fan mounting hole radius 70")
params.fan_mount_hole_radius_70 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_71", "Dimensions", "Fan mounting hole radius 71")
params.fan_mount_hole_radius_71 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_72", "Dimensions", "Fan mounting hole radius 72")
params.fan_mount_hole_radius_72 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_73", "Dimensions", "Fan mounting hole radius 73")
params.fan_mount_hole_radius_73 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_74", "Dimensions", "Fan mounting hole radius 74")
params.fan_mount_hole_radius_74 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_75", "Dimensions", "Fan mounting hole radius 75")
params.fan_mount_hole_radius_75 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_76", "Dimensions", "Fan mounting hole radius 76")
params.fan_mount_hole_radius_76 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_77", "Dimensions", "Fan mounting hole radius 77")
params.fan_mount_hole_radius_77 = 6.8
params.addProperty("
