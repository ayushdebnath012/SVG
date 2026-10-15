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
params.addProperty("App::PropertyLength", "mount_bore_t
