import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("DualAxleMountingBracket")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "base_width", "Dimensions", "Base width")
params.base_width = 345.95
params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Base height")
params.base_height = 160.7
params.addProperty("App::PropertyLength", "mount_height", "Dimensions", "Mount height")
params.mount_height = 110
params.addProperty("App::PropertyLength", "mount_width", "Dimensions", "Mount width")
params.mount_width = 160
params.addProperty("App::PropertyLength", "mount_thickness", "Dimensions", "Mount thickness")
params.mount_thickness = 20
params.addProperty("App::PropertyLength", "mount_radius", "Dimensions", "Mount corner radius")
params.mount_radius = 10
params.addProperty("App::PropertyLength", "mount_bore_dia", "Dimensions", "Mount bore diameter")
params.mount_bore_dia = 45
params.addProperty("App::PropertyLength", "mount_bore_depth", "Dimensions", "Mount bore depth")
params.mount_bore_depth = 20
params.addProperty("App::PropertyLength", "mount_bore_offset", "Dimensions", "Mount bore offset")
params.mount_bore_offset = 16.74
params.addProperty("App::PropertyLength", "mount_bore_angle", "Dimensions", "Mount bore angle")
params.mount_bore_angle = 43.1
params.addProperty("App::PropertyLength", "mount_bore_count", "Dimensions", "Mount bore count")
params.mount_bore_count = 6
params.addProperty("App::PropertyLength", "mount_bore_spacing", "Dimensions", "Mount bore spacing")
params.mount_bore_spacing = 50
params.addProperty("App::PropertyLength", "mount_bore_radius", "Dimensions", "Mount bore radius")
params.mount_bore_radius = 21
params.addProperty("App::PropertyLength", "mount_bore_taper", "Dimensions", "Mount bore taper")
params.mount_bore_taper = 2
params.addProperty("App::PropertyLength", "mount_bore_taper_angle", "Dimensions", "Mount bore taper angle")
params.mount_bore_taper_angle = 30
params.addProperty("App::PropertyLength", "mount_bore_taper_radius", "Dimensions", "Mount bore taper radius")
params.mount_bore_taper_radius = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_depth", "Dimensions", "Mount bore taper depth")
params.mount_bore_taper_depth = 112
params.addProperty("App::PropertyLength", "mount_bore_taper_width", "Dimensions", "Mount bore taper width")
params.mount_bore_taper_width = 152
params.addProperty("App::PropertyLength", "mount_bore_taper_radius2", "Dimensions", "Mount bore taper radius 2")
params.mount_bore_taper_radius2 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius3", "Dimensions", "Mount bore taper radius 3")
params.mount_bore_taper_radius3 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius4", "Dimensions", "Mount bore taper radius 4")
params.mount_bore_taper_radius4 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius5", "Dimensions", "Mount bore taper radius 5")
params.mount_bore_taper_radius5 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius6", "Dimensions", "Mount bore taper radius 6")
params.mount_bore_taper_radius6 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius7", "Dimensions", "Mount bore taper radius 7")
params.mount_bore_taper_radius7 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius8", "Dimensions", "Mount bore taper radius 8")
params.mount_bore_taper_radius8 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius9", "Dimensions", "Mount bore taper radius 9")
params.mount_bore_taper_radius9 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius10", "Dimensions", "Mount bore taper radius 10")
params.mount_bore_taper_radius10 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius11", "Dimensions", "Mount bore taper radius 11")
params.mount_bore_taper_radius11 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius12", "Dimensions", "Mount bore taper radius 12")
params.mount_bore_taper_radius12 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius13", "Dimensions", "Mount bore taper radius 13")
params.mount_bore_taper_radius13 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius14", "Dimensions", "Mount bore taper radius 14")
params.mount_bore_taper_radius14 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius15", "Dimensions", "Mount bore taper radius 15")
params.mount_bore_taper_radius15 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius16", "Dimensions", "Mount bore taper radius 16")
params.mount_bore_taper_radius16 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius17", "Dimensions", "Mount bore taper radius 17")
params.mount_bore_taper_radius17 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius18", "Dimensions", "Mount bore taper radius 18")
params.mount_bore_taper_radius18 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius19", "Dimensions", "Mount bore taper radius 19")
params.mount_bore_taper_radius19 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius20", "Dimensions", "Mount bore taper radius 20")
params.mount_bore_taper_radius20 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius21", "Dimensions", "Mount bore taper radius 21")
params.mount_bore_taper_radius21 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius22", "Dimensions", "Mount bore taper radius 22")
params.mount_bore_taper_radius22 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius23", "Dimensions", "Mount bore taper radius 23")
params.mount_bore_taper_radius23 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius24", "Dimensions", "Mount bore taper radius 24")
params.mount_bore_taper_radius24 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius25", "Dimensions", "Mount bore taper radius 25")
params.mount_bore_taper_radius25 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius26", "Dimensions", "Mount bore taper radius 26")
params.mount_bore_taper_radius26 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius27", "Dimensions", "Mount bore taper radius 27")
params.mount_bore_taper_radius27 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius28", "Dimensions", "Mount bore taper radius 28")
params.mount_bore_taper_radius28 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius29", "Dimensions", "Mount bore taper radius 29")
params.mount_bore_taper_radius29 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius30", "Dimensions", "Mount bore taper radius 30")
params.mount_bore_taper_radius30 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius31", "Dimensions", "Mount bore taper radius 31")
params.mount_bore_taper_radius31 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius32", "Dimensions", "Mount bore taper radius 32")
params.mount_bore_taper_radius32 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius33", "Dimensions", "Mount bore taper radius 33")
params.mount_bore_taper_radius33 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius34", "Dimensions", "Mount bore taper radius 34")
params.mount_bore_taper_radius34 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius35", "Dimensions", "Mount bore taper radius 35")
params.mount_bore_taper_radius35 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius36", "Dimensions", "Mount bore taper radius 36")
params.mount_bore_taper_radius36 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius37", "Dimensions", "Mount bore taper radius 37")
params.mount_bore_taper_radius37 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius38", "Dimensions", "Mount bore taper radius 38")
params.mount_bore_taper_radius38 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius39", "Dimensions", "Mount bore taper radius 39")
params.mount_bore_taper_radius39 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius40", "Dimensions", "Mount bore taper radius 40")
params.mount_bore_taper_radius40 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius41", "Dimensions", "Mount bore taper radius 41")
params.mount_bore_taper_radius41 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius42", "Dimensions", "Mount bore taper radius 42")
params.mount_bore_taper_radius42 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius43", "Dimensions", "Mount bore taper radius 43")
params.mount_bore_taper_radius43 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius44", "Dimensions", "Mount bore taper radius 44")
params.mount_bore_taper_radius44 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius45", "Dimensions", "Mount bore taper radius 45")
params.mount_bore_taper_radius45 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius46", "Dimensions", "Mount bore taper radius 46")
params.mount_bore_taper_radius46 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius47", "Dimensions", "Mount bore taper radius 47")
params.mount_bore_taper_radius47 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius48", "Dimensions", "Mount bore taper radius 48")
params.mount_bore_taper_radius48 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius49", "Dimensions", "Mount bore taper radius 49")
params.mount_bore_taper_radius49 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius50", "Dimensions", "Mount bore taper radius 50")
params.mount_bore_taper_radius50 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius51", "Dimensions", "Mount bore taper radius 51")
params.mount_bore_taper_radius51 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius52", "Dimensions", "Mount bore taper radius 52")
params.mount_bore_taper_radius52 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius53", "Dimensions", "Mount bore taper radius 53")
params.mount_bore_taper_radius53 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius54", "Dimensions", "Mount bore taper radius 54")
params.mount_bore_taper_radius54 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius55", "Dimensions", "Mount bore taper radius 55")
params.mount_bore_taper_radius55 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius56", "Dimensions", "Mount bore taper radius 56")
params.mount_bore_taper_radius56 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius57", "Dimensions", "Mount bore taper radius 57")
params.mount_bore_taper_radius57 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius58", "Dimensions", "Mount bore taper radius 58")
params.mount_bore_taper_radius58 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius59", "Dimensions", "Mount bore taper radius 59")
params.mount_bore_taper_radius59 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius60", "Dimensions", "Mount bore taper radius 60")
params.mount_bore_taper_radius60 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius61", "Dimensions", "Mount bore taper radius 61")
params.mount_bore_taper_radius61 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius62", "Dimensions", "Mount bore taper radius 62")
params.mount_bore_taper_radius62 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius63", "Dimensions", "Mount bore taper radius 63")
params.mount_bore_taper_radius63 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius64", "Dimensions", "Mount bore taper radius 64")
params.mount_bore_taper_radius64 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius65", "Dimensions", "Mount bore taper radius 65")
params.mount_bore_taper_radius65 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius66", "Dimensions", "Mount bore taper radius 66")
params.mount_bore_taper_radius66 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius67", "Dimensions", "Mount bore taper radius 67")
params.mount_bore_taper_radius67 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius68", "Dimensions", "Mount bore taper radius 68")
params.mount_bore_taper_radius68 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius69", "Dimensions", "Mount bore taper radius 69")
params.mount_bore_taper_radius69 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius70", "Dimensions", "Mount bore taper radius 70")
params.mount_bore_taper_radius70 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius71", "Dimensions", "Mount bore taper radius 71")
params.mount_bore_taper_radius71 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius72", "Dimensions", "Mount bore taper radius 72")
params.mount_bore_taper_radius72 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius73", "Dimensions", "Mount bore taper radius 73")
params.mount_bore_taper_radius73 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius74", "Dimensions", "Mount bore taper radius 74")
params.mount_bore_taper_radius74 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius75", "Dimensions", "Mount bore taper radius 75")
params.mount_bore_taper_radius75 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius76", "Dimensions", "Mount bore taper radius 76")
params.mount_bore_taper_radius76 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius77", "Dimensions", "Mount bore taper radius 77")
params.mount_bore_taper_radius77 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius78", "Dimensions", "Mount bore taper radius 78")
params.mount_bore_taper_radius78 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius79", "Dimensions", "Mount bore taper radius 79")
params.mount_bore_taper_radius79 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius80", "Dimensions", "Mount bore taper radius 80")
params.mount_bore_taper_radius80 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius81", "Dimensions", "Mount bore taper radius 81")
params.mount_bore_taper_radius81 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius82", "Dimensions", "Mount bore taper radius 82")
params.mount_bore_taper_radius82 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius83", "Dimensions", "Mount bore taper radius 83")
params.mount_bore_taper_radius83 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius84", "Dimensions", "Mount bore taper radius 84")
params.mount_bore_taper_radius84 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius85", "Dimensions", "Mount bore taper radius 85")
params.mount_bore_taper_radius85 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius86", "Dimensions", "Mount bore taper radius 86")
params.mount_bore_taper_radius86 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius87", "Dimensions", "Mount bore taper radius 87")
params.mount_bore_taper_radius87 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius88", "Dimensions", "Mount bore taper radius 88")
params.mount_bore_taper_radius88 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius89", "Dimensions", "Mount bore taper radius 89")
params.mount_bore_taper_radius89 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius90", "Dimensions", "Mount bore taper radius 90")
params.mount_bore_taper_radius90 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius91", "Dimensions", "Mount bore taper radius 91")
params.mount_bore_taper_radius91 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius92", "Dimensions", "Mount bore taper radius 92")
params.mount_bore_taper_radius92 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius93", "Dimensions", "Mount bore taper radius 93")
params.mount_bore_taper_radius93 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius94", "Dimensions", "Mount bore taper radius 94")
params.mount_bore_taper_radius94 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius95", "Dimensions", "Mount bore taper radius 95")
params.mount_bore_taper_radius95 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius96", "Dimensions", "Mount bore taper radius 96")
params.mount_bore_taper_radius96 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius97", "Dimensions", "Mount bore taper radius 97")
params.mount_bore_taper_radius97 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius98", "Dimensions", "Mount bore taper radius 98")
params.mount_bore_taper_radius98 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius99", "Dimensions", "Mount bore taper radius 99")
params.mount_bore_taper_radius99 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius100", "Dimensions", "Mount bore taper radius 100")
params.mount_bore_taper_radius100 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius101", "Dimensions", "Mount bore taper radius 101")
params.mount_bore_taper_radius101 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius102", "Dimensions", "Mount bore taper radius 102")
params.mount_bore_taper_radius102 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius103", "Dimensions", "Mount bore taper radius 103")
params.mount_bore_taper_radius103 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius104", "Dimensions", "Mount bore taper radius 104")
params.mount_bore_taper_radius104 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius105", "Dimensions", "Mount bore taper radius 105")
params.mount_bore_taper_radius105 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius106", "Dimensions", "Mount bore taper radius 106")
params.mount_bore_taper_radius106 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius107", "Dimensions", "Mount bore taper radius 107")
params.mount_bore_taper_radius107 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius108", "Dimensions", "Mount bore taper radius 108")
params.mount_bore_taper_radius108 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius109", "Dimensions", "Mount bore taper radius 109")
params.mount_bore_taper_radius109 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius110", "Dimensions", "Mount bore taper radius 110")
params.mount_bore_taper_radius110 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius111", "Dimensions", "Mount bore taper radius 111")
params.mount_bore_taper_radius111 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius112", "Dimensions", "Mount bore taper radius 112")
params.mount_bore_taper_radius112 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius113", "Dimensions", "Mount bore taper radius 113")
params.mount_bore_taper_radius113 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius114", "Dimensions", "Mount bore taper radius 114")
params.mount_bore_taper_radius114 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius115", "Dimensions", "Mount bore taper radius 115")
params.mount_bore_taper_radius115 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius116", "Dimensions", "Mount bore taper radius 116")
params.mount_bore_taper_radius116 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius117", "Dimensions", "Mount bore taper radius 117")
params.mount_bore_taper_radius117 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius118", "Dimensions", "Mount bore taper radius 118")
params.mount_bore_taper_radius118 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius119", "Dimensions", "Mount bore taper radius 119")
params.mount_bore_taper_radius119 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius120", "Dimensions", "Mount bore taper radius 120")
params.mount_bore_taper_radius120 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius121", "Dimensions", "Mount bore taper radius 121")
params.mount_bore_taper_radius121 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius122", "Dimensions", "Mount bore taper radius 122")
params.mount_bore_taper_radius122 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius123", "Dimensions", "Mount bore taper radius 123")
params.mount_bore_taper_radius123 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius124", "Dimensions", "Mount bore taper radius 124")
params.mount_bore_taper_radius124 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius125", "Dimensions", "Mount bore taper radius 125")
params.mount_bore_taper_radius125 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius126", "Dimensions", "Mount bore taper radius 126")
params.mount_bore_taper_radius126 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius127", "Dimensions", "Mount bore taper radius 127")
params.mount_bore_taper_radius127 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius128", "Dimensions", "Mount bore taper radius 128")
params.mount_bore_taper_radius128 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius129", "Dimensions", "Mount bore taper radius 129")
params.mount_bore_taper_radius129 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius130", "Dimensions", "Mount bore taper radius 130")
params.mount_bore_taper_radius130 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius131", "Dimensions", "Mount bore taper radius 131")
params.mount_bore_taper_radius131 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius132", "Dimensions", "Mount bore taper radius 132")
params.mount_bore_taper_radius132 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius133", "Dimensions", "Mount bore taper radius 133")
params.mount_bore_taper_radius133 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius134", "Dimensions", "Mount bore taper radius 134")
params.mount_bore_taper_radius134 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius135", "Dimensions", "Mount bore taper radius 135")
params.mount_bore_taper_radius135 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius136", "Dimensions", "Mount bore taper radius 136")
params.mount_bore_taper_radius136 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius137", "Dimensions", "Mount bore taper radius 137")
params.mount_bore_taper_radius137 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius138", "Dimensions", "Mount bore taper radius 138")
params.mount_bore_taper_radius138 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius139", "Dimensions", "Mount bore taper radius 139")
params.mount_bore_taper_radius139 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius140", "Dimensions", "Mount bore taper radius 140")
params.mount_bore_taper_radius140 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius141", "Dimensions", "Mount bore taper radius 141")
params.mount_bore_taper_radius141 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius142", "Dimensions", "Mount bore taper radius 142")
params.mount_bore_taper_radius142 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius143", "Dimensions", "Mount bore taper radius 143")
params.mount_bore_taper_radius143 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius144", "Dimensions", "Mount bore taper radius 144")
params.mount_bore_taper_radius144 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius145", "Dimensions", "Mount bore taper radius 145")
params.mount_bore_taper_radius145 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius146", "Dimensions", "Mount bore taper radius 146")
params.mount_bore_taper_radius146 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius147", "Dimensions", "Mount bore taper radius 147")
params.mount_bore_taper_radius147 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius148", "Dimensions", "Mount bore taper radius 148")
params.mount_bore_taper_radius148 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius149", "Dimensions", "Mount bore taper radius 149")
params.mount_bore_taper_radius149 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius150", "Dimensions", "Mount bore taper radius 150")
params.mount_bore_taper_radius150 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius151", "Dimensions", "Mount bore taper radius 151")
params.mount_bore_taper_radius151 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius152", "Dimensions", "Mount bore taper radius 152")
params.mount_bore_taper_radius152 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius153", "Dimensions", "Mount bore taper radius 153")
params.mount_bore_taper_radius153 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius154", "Dimensions", "Mount bore taper radius 154")
params.mount_bore_taper_radius154 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius155", "Dimensions", "Mount bore taper radius 155")
params.mount_bore_taper_radius155 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius156", "Dimensions", "Mount bore taper radius 156")
params.mount_bore_taper_radius156 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius157", "Dimensions", "Mount bore taper radius 157")
params.mount_bore_taper_radius157 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius158", "Dimensions", "Mount bore taper radius 158")
params.mount_bore_taper_radius158 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius159", "Dimensions", "Mount bore taper radius 159")
params.mount_bore_taper_radius159 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius160", "Dimensions", "Mount bore taper radius 160")
params.mount_bore_taper_radius160 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius161", "Dimensions", "Mount bore taper radius 161")
params.mount_bore_taper_radius161 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius162", "Dimensions", "Mount bore taper radius 162")
params.mount_bore_taper_radius162 = 20
params.addProperty("App::PropertyLength", "mount_bore_taper_radius163", "Dimensions", "Mount bore taper radius 163")
params.mount_bore_taper_radius163 = 10
params.addProperty("App::PropertyLength", "mount_bore_taper_radius164", "Dimensions", "Mount bore taper radius 164")
params.mount_bore_taper_radius164 = 20
