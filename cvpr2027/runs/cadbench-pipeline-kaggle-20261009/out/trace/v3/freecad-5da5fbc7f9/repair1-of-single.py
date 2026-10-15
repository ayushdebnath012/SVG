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
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_78", "Dimensions", "Fan mounting hole radius 78")
params.fan_mount_hole_radius_78 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_79", "Dimensions", "Fan mounting hole radius 79")
params.fan_mount_hole_radius_79 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_80", "Dimensions", "Fan mounting hole radius 80")
params.fan_mount_hole_radius_80 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_81", "Dimensions", "Fan mounting hole radius 81")
params.fan_mount_hole_radius_81 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_82", "Dimensions", "Fan mounting hole radius 82")
params.fan_mount_hole_radius_82 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_83", "Dimensions", "Fan mounting hole radius 83")
params.fan_mount_hole_radius_83 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_84", "Dimensions", "Fan mounting hole radius 84")
params.fan_mount_hole_radius_84 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_85", "Dimensions", "Fan mounting hole radius 85")
params.fan_mount_hole_radius_85 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_86", "Dimensions", "Fan mounting hole radius 86")
params.fan_mount_hole_radius_86 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_87", "Dimensions", "Fan mounting hole radius 87")
params.fan_mount_hole_radius_87 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_88", "Dimensions", "Fan mounting hole radius 88")
params.fan_mount_hole_radius_88 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_89", "Dimensions", "Fan mounting hole radius 89")
params.fan_mount_hole_radius_89 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_90", "Dimensions", "Fan mounting hole radius 90")
params.fan_mount_hole_radius_90 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_91", "Dimensions", "Fan mounting hole radius 91")
params.fan_mount_hole_radius_91 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_92", "Dimensions", "Fan mounting hole radius 92")
params.fan_mount_hole_radius_92 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_93", "Dimensions", "Fan mounting hole radius 93")
params.fan_mount_hole_radius_93 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_94", "Dimensions", "Fan mounting hole radius 94")
params.fan_mount_hole_radius_94 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_95", "Dimensions", "Fan mounting hole radius 95")
params.fan_mount_hole_radius_95 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_96", "Dimensions", "Fan mounting hole radius 96")
params.fan_mount_hole_radius_96 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_97", "Dimensions", "Fan mounting hole radius 97")
params.fan_mount_hole_radius_97 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_98", "Dimensions", "Fan mounting hole radius 98")
params.fan_mount_hole_radius_98 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_99", "Dimensions", "Fan mounting hole radius 99")
params.fan_mount_hole_radius_99 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_100", "Dimensions", "Fan mounting hole radius 100")
params.fan_mount_hole_radius_100 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_101", "Dimensions", "Fan mounting hole radius 101")
params.fan_mount_hole_radius_101 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_102", "Dimensions", "Fan mounting hole radius 102")
params.fan_mount_hole_radius_102 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_103", "Dimensions", "Fan mounting hole radius 103")
params.fan_mount_hole_radius_103 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_104", "Dimensions", "Fan mounting hole radius 104")
params.fan_mount_hole_radius_104 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_105", "Dimensions", "Fan mounting hole radius 105")
params.fan_mount_hole_radius_105 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_106", "Dimensions", "Fan mounting hole radius 106")
params.fan_mount_hole_radius_106 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_107", "Dimensions", "Fan mounting hole radius 107")
params.fan_mount_hole_radius_107 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_108", "Dimensions", "Fan mounting hole radius 108")
params.fan_mount_hole_radius_108 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_109", "Dimensions", "Fan mounting hole radius 109")
params.fan_mount_hole_radius_109 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_110", "Dimensions", "Fan mounting hole radius 110")
params.fan_mount_hole_radius_110 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_111", "Dimensions", "Fan mounting hole radius 111")
params.fan_mount_hole_radius_111 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_112", "Dimensions", "Fan mounting hole radius 112")
params.fan_mount_hole_radius_112 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_113", "Dimensions", "Fan mounting hole radius 113")
params.fan_mount_hole_radius_113 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_114", "Dimensions", "Fan mounting hole radius 114")
params.fan_mount_hole_radius_114 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_115", "Dimensions", "Fan mounting hole radius 115")
params.fan_mount_hole_radius_115 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_116", "Dimensions", "Fan mounting hole radius 116")
params.fan_mount_hole_radius_116 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_117", "Dimensions", "Fan mounting hole radius 117")
params.fan_mount_hole_radius_117 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_118", "Dimensions", "Fan mounting hole radius 118")
params.fan_mount_hole_radius_118 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_119", "Dimensions", "Fan mounting hole radius 119")
params.fan_mount_hole_radius_119 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_120", "Dimensions", "Fan mounting hole radius 120")
params.fan_mount_hole_radius_120 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_121", "Dimensions", "Fan mounting hole radius 121")
params.fan_mount_hole_radius_121 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_122", "Dimensions", "Fan mounting hole radius 122")
params.fan_mount_hole_radius_122 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_123", "Dimensions", "Fan mounting hole radius 123")
params.fan_mount_hole_radius_123 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_124", "Dimensions", "Fan mounting hole radius 124")
params.fan_mount_hole_radius_124 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_125", "Dimensions", "Fan mounting hole radius 125")
params.fan_mount_hole_radius_125 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_126", "Dimensions", "Fan mounting hole radius 126")
params.fan_mount_hole_radius_126 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_127", "Dimensions", "Fan mounting hole radius 127")
params.fan_mount_hole_radius_127 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_128", "Dimensions", "Fan mounting hole radius 128")
params.fan_mount_hole_radius_128 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_129", "Dimensions", "Fan mounting hole radius 129")
params.fan_mount_hole_radius_129 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_130", "Dimensions", "Fan mounting hole radius 130")
params.fan_mount_hole_radius_130 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_131", "Dimensions", "Fan mounting hole radius 131")
params.fan_mount_hole_radius_131 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_132", "Dimensions", "Fan mounting hole radius 132")
params.fan_mount_hole_radius_132 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_133", "Dimensions", "Fan mounting hole radius 133")
params.fan_mount_hole_radius_133 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_134", "Dimensions", "Fan mounting hole radius 134")
params.fan_mount_hole_radius_134 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_135", "Dimensions", "Fan mounting hole radius 135")
params.fan_mount_hole_radius_135 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_136", "Dimensions", "Fan mounting hole radius 136")
params.fan_mount_hole_radius_136 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_137", "Dimensions", "Fan mounting hole radius 137")
params.fan_mount_hole_radius_137 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_138", "Dimensions", "Fan mounting hole radius 138")
params.fan_mount_hole_radius_138 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_139", "Dimensions", "Fan mounting hole radius 139")
params.fan_mount_hole_radius_139 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_140", "Dimensions", "Fan mounting hole radius 140")
params.fan_mount_hole_radius_140 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_141", "Dimensions", "Fan mounting hole radius 141")
params.fan_mount_hole_radius_141 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_142", "Dimensions", "Fan mounting hole radius 142")
params.fan_mount_hole_radius_142 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_143", "Dimensions", "Fan mounting hole radius 143")
params.fan_mount_hole_radius_143 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_144", "Dimensions", "Fan mounting hole radius 144")
params.fan_mount_hole_radius_144 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_145", "Dimensions", "Fan mounting hole radius 145")
params.fan_mount_hole_radius_145 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_146", "Dimensions", "Fan mounting hole radius 146")
params.fan_mount_hole_radius_146 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_147", "Dimensions", "Fan mounting hole radius 147")
params.fan_mount_hole_radius_147 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_148", "Dimensions", "Fan mounting hole radius 148")
params.fan_mount_hole_radius_148 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_149", "Dimensions", "Fan mounting hole radius 149")
params.fan_mount_hole_radius_149 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_150", "Dimensions", "Fan mounting hole radius 150")
params.fan_mount_hole_radius_150 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_151", "Dimensions", "Fan mounting hole radius 151")
params.fan_mount_hole_radius_151 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_152", "Dimensions", "Fan mounting hole radius 152")
params.fan_mount_hole_radius_152 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_153", "Dimensions", "Fan mounting hole radius 153")
params.fan_mount_hole_radius_153 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_154", "Dimensions", "Fan mounting hole radius 154")
params.fan_mount_hole_radius_154 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_155", "Dimensions", "Fan mounting hole radius 155")
params.fan_mount_hole_radius_155 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_156", "Dimensions", "Fan mounting hole radius 156")
params.fan_mount_hole_radius_156 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_157", "Dimensions", "Fan mounting hole radius 157")
params.fan_mount_hole_radius_157 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_158", "Dimensions", "Fan mounting hole radius 158")
params.fan_mount_hole_radius_158 = 6.8
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_159", "Dimensions", "Fan mounting hole radius 159")
params.fan_mount_hole_radius_159 = 3.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_160", "Dimensions", "Fan mounting hole radius 160")
params.fan_mount_hole_radius_160 = 4.5
params.addProperty("App::PropertyLength", "fan_mount_hole_radius_
