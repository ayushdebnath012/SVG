import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("FoamFrame")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Extracted from the drawing dimensions
params = body.newObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "base_width", "Dimensions", "Main Frame Width")
params.base_width = 450.8
params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Main Frame Height")
params.base_height = 405.0
params.addProperty("App::PropertyLength", "base_depth", "Dimensions", "Main Frame Depth")
params.base_depth = 80.0
params.addProperty("App::PropertyLength", "wall_thickness", "Dimensions", "Wall Thickness")
params.wall_thickness = 12.7
params.addProperty("App::PropertyLength", "cutout_depth", "Dimensions", "Cutout Depth")
params.cutout_depth = 75.0
params.addProperty("App::PropertyLength", "cutout_width", "Dimensions", "Cutout Width")
params.cutout_width = 180.0
params.addProperty("App::PropertyLength", "cutout_height", "Dimensions", "Cutout Height")
params.cutout_height = 150.54
params.addProperty("App::PropertyLength", "cutout_radius", "Dimensions", "Cutout Radius")
params.cutout_radius = 107.7
params.addProperty("App::PropertyLength", "cutout_radius_small", "Dimensions", "Small Cutout Radius")
params.cutout_radius_small = 50.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny", "Dimensions", "Tiny Cutout Radius")
params.cutout_radius_tiny = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny2", "Dimensions", "Tiny Cutout Radius 2")
params.cutout_radius_tiny2 = 20.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny3", "Dimensions", "Tiny Cutout Radius 3")
params.cutout_radius_tiny3 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny4", "Dimensions", "Tiny Cutout Radius 4")
params.cutout_radius_tiny4 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny5", "Dimensions", "Tiny Cutout Radius 5")
params.cutout_radius_tiny5 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny6", "Dimensions", "Tiny Cutout Radius 6")
params.cutout_radius_tiny6 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny7", "Dimensions", "Tiny Cutout Radius 7")
params.cutout_radius_tiny7 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny8", "Dimensions", "Tiny Cutout Radius 8")
params.cutout_radius_tiny8 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny9", "Dimensions", "Tiny Cutout Radius 9")
params.cutout_radius_tiny9 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny10", "Dimensions", "Tiny Cutout Radius 10")
params.cutout_radius_tiny10 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny11", "Dimensions", "Tiny Cutout Radius 11")
params.cutout_radius_tiny11 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny12", "Dimensions", "Tiny Cutout Radius 12")
params.cutout_radius_tiny12 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny13", "Dimensions", "Tiny Cutout Radius 13")
params.cutout_radius_tiny13 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny14", "Dimensions", "Tiny Cutout Radius 14")
params.cutout_radius_tiny14 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny15", "Dimensions", "Tiny Cutout Radius 15")
params.cutout_radius_tiny15 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny16", "Dimensions", "Tiny Cutout Radius 16")
params.cutout_radius_tiny16 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny17", "Dimensions", "Tiny Cutout Radius 17")
params.cutout_radius_tiny17 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny18", "Dimensions", "Tiny Cutout Radius 18")
params.cutout_radius_tiny18 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny19", "Dimensions", "Tiny Cutout Radius 19")
params.cutout_radius_tiny19 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny20", "Dimensions", "Tiny Cutout Radius 20")
params.cutout_radius_tiny20 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny21", "Dimensions", "Tiny Cutout Radius 21")
params.cutout_radius_tiny21 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny22", "Dimensions", "Tiny Cutout Radius 22")
params.cutout_radius_tiny22 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny23", "Dimensions", "Tiny Cutout Radius 23")
params.cutout_radius_tiny23 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny24", "Dimensions", "Tiny Cutout Radius 24")
params.cutout_radius_tiny24 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny25", "Dimensions", "Tiny Cutout Radius 25")
params.cutout_radius_tiny25 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny26", "Dimensions", "Tiny Cutout Radius 26")
params.cutout_radius_tiny26 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny27", "Dimensions", "Tiny Cutout Radius 27")
params.cutout_radius_tiny27 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny28", "Dimensions", "Tiny Cutout Radius 28")
params.cutout_radius_tiny28 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny29", "Dimensions", "Tiny Cutout Radius 29")
params.cutout_radius_tiny29 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny30", "Dimensions", "Tiny Cutout Radius 30")
params.cutout_radius_tiny30 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny31", "Dimensions", "Tiny Cutout Radius 31")
params.cutout_radius_tiny31 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny32", "Dimensions", "Tiny Cutout Radius 32")
params.cutout_radius_tiny32 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny33", "Dimensions", "Tiny Cutout Radius 33")
params.cutout_radius_tiny33 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny34", "Dimensions", "Tiny Cutout Radius 34")
params.cutout_radius_tiny34 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny35", "Dimensions", "Tiny Cutout Radius 35")
params.cutout_radius_tiny35 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny36", "Dimensions", "Tiny Cutout Radius 36")
params.cutout_radius_tiny36 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny37", "Dimensions", "Tiny Cutout Radius 37")
params.cutout_radius_tiny37 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny38", "Dimensions", "Tiny Cutout Radius 38")
params.cutout_radius_tiny38 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny39", "Dimensions", "Tiny Cutout Radius 39")
params.cutout_radius_tiny39 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny40", "Dimensions", "Tiny Cutout Radius 40")
params.cutout_radius_tiny40 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny41", "Dimensions", "Tiny Cutout Radius 41")
params.cutout_radius_tiny41 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny42", "Dimensions", "Tiny Cutout Radius 42")
params.cutout_radius_tiny42 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny43", "Dimensions", "Tiny Cutout Radius 43")
params.cutout_radius_tiny43 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny44", "Dimensions", "Tiny Cutout Radius 44")
params.cutout_radius_tiny44 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny45", "Dimensions", "Tiny Cutout Radius 45")
params.cutout_radius_tiny45 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny46", "Dimensions", "Tiny Cutout Radius 46")
params.cutout_radius_tiny46 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny47", "Dimensions", "Tiny Cutout Radius 47")
params.cutout_radius_tiny47 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny48", "Dimensions", "Tiny Cutout Radius 48")
params.cutout_radius_tiny48 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny49", "Dimensions", "Tiny Cutout Radius 49")
params.cutout_radius_tiny49 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny50", "Dimensions", "Tiny Cutout Radius 50")
params.cutout_radius_tiny50 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny51", "Dimensions", "Tiny Cutout Radius 51")
params.cutout_radius_tiny51 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny52", "Dimensions", "Tiny Cutout Radius 52")
params.cutout_radius_tiny52 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny53", "Dimensions", "Tiny Cutout Radius 53")
params.cutout_radius_tiny53 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny54", "Dimensions", "Tiny Cutout Radius 54")
params.cutout_radius_tiny54 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny55", "Dimensions", "Tiny Cutout Radius 55")
params.cutout_radius_tiny55 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny56", "Dimensions", "Tiny Cutout Radius 56")
params.cutout_radius_tiny56 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny57", "Dimensions", "Tiny Cutout Radius 57")
params.cutout_radius_tiny57 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny58", "Dimensions", "Tiny Cutout Radius 58")
params.cutout_radius_tiny58 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny59", "Dimensions", "Tiny Cutout Radius 59")
params.cutout_radius_tiny59 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny60", "Dimensions", "Tiny Cutout Radius 60")
params.cutout_radius_tiny60 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny61", "Dimensions", "Tiny Cutout Radius 61")
params.cutout_radius_tiny61 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny62", "Dimensions", "Tiny Cutout Radius 62")
params.cutout_radius_tiny62 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny63", "Dimensions", "Tiny Cutout Radius 63")
params.cutout_radius_tiny63 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny64", "Dimensions", "Tiny Cutout Radius 64")
params.cutout_radius_tiny64 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny65", "Dimensions", "Tiny Cutout Radius 65")
params.cutout_radius_tiny65 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny66", "Dimensions", "Tiny Cutout Radius 66")
params.cutout_radius_tiny66 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny67", "Dimensions", "Tiny Cutout Radius 67")
params.cutout_radius_tiny67 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny68", "Dimensions", "Tiny Cutout Radius 68")
params.cutout_radius_tiny68 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny69", "Dimensions", "Tiny Cutout Radius 69")
params.cutout_radius_tiny69 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny70", "Dimensions", "Tiny Cutout Radius 70")
params.cutout_radius_tiny70 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny71", "Dimensions", "Tiny Cutout Radius 71")
params.cutout_radius_tiny71 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny72", "Dimensions", "Tiny Cutout Radius 72")
params.cutout_radius_tiny72 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny73", "Dimensions", "Tiny Cutout Radius 73")
params.cutout_radius_tiny73 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny74", "Dimensions", "Tiny Cutout Radius 74")
params.cutout_radius_tiny74 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny75", "Dimensions", "Tiny Cutout Radius 75")
params.cutout_radius_tiny75 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny76", "Dimensions", "Tiny Cutout Radius 76")
params.cutout_radius_tiny76 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny77", "Dimensions", "Tiny Cutout Radius 77")
params.cutout_radius_tiny77 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny78", "Dimensions", "Tiny Cutout Radius 78")
params.cutout_radius_tiny78 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny79", "Dimensions", "Tiny Cutout Radius 79")
params.cutout_radius_tiny79 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny80", "Dimensions", "Tiny Cutout Radius 80")
params.cutout_radius_tiny80 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny81", "Dimensions", "Tiny Cutout Radius 81")
params.cutout_radius_tiny81 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny82", "Dimensions", "Tiny Cutout Radius 82")
params.cutout_radius_tiny82 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny83", "Dimensions", "Tiny Cutout Radius 83")
params.cutout_radius_tiny83 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny84", "Dimensions", "Tiny Cutout Radius 84")
params.cutout_radius_tiny84 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny85", "Dimensions", "Tiny Cutout Radius 85")
params.cutout_radius_tiny85 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny86", "Dimensions", "Tiny Cutout Radius 86")
params.cutout_radius_tiny86 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny87", "Dimensions", "Tiny Cutout Radius 87")
params.cutout_radius_tiny87 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny88", "Dimensions", "Tiny Cutout Radius 88")
params.cutout_radius_tiny88 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny89", "Dimensions", "Tiny Cutout Radius 89")
params.cutout_radius_tiny89 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny90", "Dimensions", "Tiny Cutout Radius 90")
params.cutout_radius_tiny90 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny91", "Dimensions", "Tiny Cutout Radius 91")
params.cutout_radius_tiny91 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny92", "Dimensions", "Tiny Cutout Radius 92")
params.cutout_radius_tiny92 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny93", "Dimensions", "Tiny Cutout Radius 93")
params.cutout_radius_tiny93 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny94", "Dimensions", "Tiny Cutout Radius 94")
params.cutout_radius_tiny94 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny95", "Dimensions", "Tiny Cutout Radius 95")
params.cutout_radius_tiny95 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny96", "Dimensions", "Tiny Cutout Radius 96")
params.cutout_radius_tiny96 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny97", "Dimensions", "Tiny Cutout Radius 97")
params.cutout_radius_tiny97 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny98", "Dimensions", "Tiny Cutout Radius 98")
params.cutout_radius_tiny98 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny99", "Dimensions", "Tiny Cutout Radius 99")
params.cutout_radius_tiny99 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny100", "Dimensions", "Tiny Cutout Radius 100")
params.cutout_radius_tiny100 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny101", "Dimensions", "Tiny Cutout Radius 101")
params.cutout_radius_tiny101 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny102", "Dimensions", "Tiny Cutout Radius 102")
params.cutout_radius_tiny102 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny103", "Dimensions", "Tiny Cutout Radius 103")
params.cutout_radius_tiny103 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny104", "Dimensions", "Tiny Cutout Radius 104")
params.cutout_radius_tiny104 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny105", "Dimensions", "Tiny Cutout Radius 105")
params.cutout_radius_tiny105 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny106", "Dimensions", "Tiny Cutout Radius 106")
params.cutout_radius_tiny106 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny107", "Dimensions", "Tiny Cutout Radius 107")
params.cutout_radius_tiny107 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny108", "Dimensions", "Tiny Cutout Radius 108")
params.cutout_radius_tiny108 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny109", "Dimensions", "Tiny Cutout Radius 109")
params.cutout_radius_tiny109 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny110", "Dimensions", "Tiny Cutout Radius 110")
params.cutout_radius_tiny110 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny111", "Dimensions", "Tiny Cutout Radius 111")
params.cutout_radius_tiny111 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny112", "Dimensions", "Tiny Cutout Radius 112")
params.cutout_radius_tiny112 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny113", "Dimensions", "Tiny Cutout Radius 113")
params.cutout_radius_tiny113 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny114", "Dimensions", "Tiny Cutout Radius 114")
params.cutout_radius_tiny114 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny115", "Dimensions", "Tiny Cutout Radius 115")
params.cutout_radius_tiny115 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny116", "Dimensions", "Tiny Cutout Radius 116")
params.cutout_radius_tiny116 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny117", "Dimensions", "Tiny Cutout Radius 117")
params.cutout_radius_tiny117 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny118", "Dimensions", "Tiny Cutout Radius 118")
params.cutout_radius_tiny118 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny119", "Dimensions", "Tiny Cutout Radius 119")
params.cutout_radius_tiny119 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny120", "Dimensions", "Tiny Cutout Radius 120")
params.cutout_radius_tiny120 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny121", "Dimensions", "Tiny Cutout Radius 121")
params.cutout_radius_tiny121 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny122", "Dimensions", "Tiny Cutout Radius 122")
params.cutout_radius_tiny122 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny123", "Dimensions", "Tiny Cutout Radius 123")
params.cutout_radius_tiny123 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny124", "Dimensions", "Tiny Cutout Radius 124")
params.cutout_radius_tiny124 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny125", "Dimensions", "Tiny Cutout Radius 125")
params.cutout_radius_tiny125 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny126", "Dimensions", "Tiny Cutout Radius 126")
params.cutout_radius_tiny126 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny127", "Dimensions", "Tiny Cutout Radius 127")
params.cutout_radius_tiny127 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny128", "Dimensions", "Tiny Cutout Radius 128")
params.cutout_radius_tiny128 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny129", "Dimensions", "Tiny Cutout Radius 129")
params.cutout_radius_tiny129 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny130", "Dimensions", "Tiny Cutout Radius 130")
params.cutout_radius_tiny130 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny131", "Dimensions", "Tiny Cutout Radius 131")
params.cutout_radius_tiny131 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny132", "Dimensions", "Tiny Cutout Radius 132")
params.cutout_radius_tiny132 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny133", "Dimensions", "Tiny Cutout Radius 133")
params.cutout_radius_tiny133 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny134", "Dimensions", "Tiny Cutout Radius 134")
params.cutout_radius_tiny134 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny135", "Dimensions", "Tiny Cutout Radius 135")
params.cutout_radius_tiny135 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny136", "Dimensions", "Tiny Cutout Radius 136")
params.cutout_radius_tiny136 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny137", "Dimensions", "Tiny Cutout Radius 137")
params.cutout_radius_tiny137 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny138", "Dimensions", "Tiny Cutout Radius 138")
params.cutout_radius_tiny138 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny139", "Dimensions", "Tiny Cutout Radius 139")
params.cutout_radius_tiny139 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny140", "Dimensions", "Tiny Cutout Radius 140")
params.cutout_radius_tiny140 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny141", "Dimensions", "Tiny Cutout Radius 141")
params.cutout_radius_tiny141 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny142", "Dimensions", "Tiny Cutout Radius 142")
params.cutout_radius_tiny142 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny143", "Dimensions", "Tiny Cutout Radius 143")
params.cutout_radius_tiny143 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny144", "Dimensions", "Tiny Cutout Radius 144")
params.cutout_radius_tiny144 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny145", "Dimensions", "Tiny Cutout Radius 145")
params.cutout_radius_tiny145 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny146", "Dimensions", "Tiny Cutout Radius 146")
params.cutout_radius_tiny146 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny147", "Dimensions", "Tiny Cutout Radius 147")
params.cutout_radius_tiny147 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny148", "Dimensions", "Tiny Cutout Radius 148")
params.cutout_radius_tiny148 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny149", "Dimensions", "Tiny Cutout Radius 149")
params.cutout_radius_tiny149 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny150", "Dimensions", "Tiny Cutout Radius 150")
params.cutout_radius_tiny150 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny151", "Dimensions", "Tiny Cutout Radius 151")
params.cutout_radius_tiny151 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny152", "Dimensions", "Tiny Cutout Radius 152")
params.cutout_radius_tiny152 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny153", "Dimensions", "Tiny Cutout Radius 153")
params.cutout_radius_tiny153 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny154", "Dimensions", "Tiny Cutout Radius 154")
params.cutout_radius_tiny154 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny155", "Dimensions", "Tiny Cutout Radius 155")
params.cutout_radius_tiny155 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny156", "Dimensions", "Tiny Cutout Radius 156")
params.cutout_radius_tiny156 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny157", "Dimensions", "Tiny Cutout Radius 157")
params.cutout_radius_tiny157 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny158", "Dimensions", "Tiny Cutout Radius 158")
params.cutout_radius_tiny158 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny159", "Dimensions", "Tiny Cutout Radius 159")
params.cutout_radius_tiny159 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny160", "Dimensions", "Tiny Cutout Radius 160")
params.cutout_radius_tiny160 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny161", "Dimensions", "Tiny Cutout Radius 161")
params.cutout_radius_tiny161 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny162", "Dimensions", "Tiny Cutout Radius 162")
params.cutout_radius_tiny162 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny163", "Dimensions", "Tiny Cutout Radius 163")
params.cutout_radius_tiny163 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny164", "Dimensions", "Tiny Cutout Radius 164")
params.cutout_radius_tiny164 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny165", "Dimensions", "Tiny Cutout Radius 165")
params.cutout_radius_tiny165 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny166", "Dimensions", "Tiny Cutout Radius 166")
params.cutout_radius_tiny166 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny167", "Dimensions", "Tiny Cutout Radius 167")
params.cutout_radius_tiny167 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny168", "Dimensions", "Tiny Cutout Radius 168")
params.cutout_radius_tiny168 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny169", "Dimensions", "Tiny Cutout Radius 169")
params.cutout_radius_tiny169 = 25.0
params.addProperty("App::PropertyLength", "cutout_radius_tiny170", "Dimensions", "Tiny Cutout
