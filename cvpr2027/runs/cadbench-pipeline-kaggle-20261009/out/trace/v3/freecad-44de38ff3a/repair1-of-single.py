import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create new document
doc = App.newDocument("Cylindrical_Actuator_Mount")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create named parameters for key dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "main_length", "Dimensions", "Main body length")
params.main_length = 151.0

params.addProperty("App::PropertyLength", "flange_width", "Dimensions", "Flange width")
params.flange_width = 71.8

params.addProperty("App::PropertyLength", "flange_height", "Dimensions", "Flange height")
params.flange_height = 36.96

params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft diameter")
params.shaft_diameter = 20.0

params.addProperty("App::PropertyLength", "shaft_length", "Dimensions", "Shaft length")
params.shaft_length = 59.0

params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "Mounting hole diameter")
params.mounting_hole_diameter = 5.0

params.addProperty("App::PropertyLength", "mounting_hole_spacing", "Dimensions", "Mounting hole spacing")
params.mounting_hole_spacing = 45.98

params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange thickness")
params.flange_thickness = 17.1

params.addProperty("App::PropertyLength", "flange_radius", "Dimensions", "Flange outer radius")
params.flange_radius = 35.98

params.addProperty("App::PropertyLength", "flange_inner_radius", "Dimensions", "Flange inner radius")
params.flange_inner_radius = 25.0

params.addProperty("App::PropertyLength", "flange_mounting_radius", "Dimensions", "Flange mounting radius")
params.flange_mounting_radius = 30.98

params.addProperty("App::PropertyLength", "flange_mounting_hole_diameter", "Dimensions", "Flange mounting hole diameter")
params.flange_mounting_hole_diameter = 6.5

params.addProperty("App::PropertyLength", "flange_mounting_hole_spacing", "Dimensions", "Flange mounting hole spacing")
params.flange_mounting_hole_spacing = 18.53

params.addProperty("App::PropertyLength", "flange_mounting_hole_angle", "Dimensions", "Flange mounting hole angle")
params.flange_mounting_hole_angle = 45.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_count", "Dimensions", "Flange mounting hole count")
params.flange_mounting_hole_count = 4

params.addProperty("App::PropertyLength", "flange_mounting_hole_offset", "Dimensions", "Flange mounting hole offset")
params.flange_mounting_hole_offset = 8.64

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius", "Dimensions", "Flange mounting hole radius")
params.flange_mounting_hole_radius = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius2", "Dimensions", "Flange mounting hole radius2")
params.flange_mounting_hole_radius2 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius3", "Dimensions", "Flange mounting hole radius3")
params.flange_mounting_hole_radius3 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius4", "Dimensions", "Flange mounting hole radius4")
params.flange_mounting_hole_radius4 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius5", "Dimensions", "Flange mounting hole radius5")
params.flange_mounting_hole_radius5 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius6", "Dimensions", "Flange mounting hole radius6")
params.flange_mounting_hole_radius6 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius7", "Dimensions", "Flange mounting hole radius7")
params.flange_mounting_hole_radius7 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius8", "Dimensions", "Flange mounting hole radius8")
params.flange_mounting_hole_radius8 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius9", "Dimensions", "Flange mounting hole radius9")
params.flange_mounting_hole_radius9 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius10", "Dimensions", "Flange mounting hole radius10")
params.flange_mounting_hole_radius10 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius11", "Dimensions", "Flange mounting hole radius11")
params.flange_mounting_hole_radius11 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius12", "Dimensions", "Flange mounting hole radius12")
params.flange_mounting_hole_radius12 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius13", "Dimensions", "Flange mounting hole radius13")
params.flange_mounting_hole_radius13 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius14", "Dimensions", "Flange mounting hole radius14")
params.flange_mounting_hole_radius14 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius15", "Dimensions", "Flange mounting hole radius15")
params.flange_mounting_hole_radius15 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius16", "Dimensions", "Flange mounting hole radius16")
params.flange_mounting_hole_radius16 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius17", "Dimensions", "Flange mounting hole radius17")
params.flange_mounting_hole_radius17 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius18", "Dimensions", "Flange mounting hole radius18")
params.flange_mounting_hole_radius18 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius19", "Dimensions", "Flange mounting hole radius19")
params.flange_mounting_hole_radius19 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius20", "Dimensions", "Flange mounting hole radius20")
params.flange_mounting_hole_radius20 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius21", "Dimensions", "Flange mounting hole radius21")
params.flange_mounting_hole_radius21 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius22", "Dimensions", "Flange mounting hole radius22")
params.flange_mounting_hole_radius22 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius23", "Dimensions", "Flange mounting hole radius23")
params.flange_mounting_hole_radius23 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius24", "Dimensions", "Flange mounting hole radius24")
params.flange_mounting_hole_radius24 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius25", "Dimensions", "Flange mounting hole radius25")
params.flange_mounting_hole_radius25 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius26", "Dimensions", "Flange mounting hole radius26")
params.flange_mounting_hole_radius26 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius27", "Dimensions", "Flange mounting hole radius27")
params.flange_mounting_hole_radius27 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius28", "Dimensions", "Flange mounting hole radius28")
params.flange_mounting_hole_radius28 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius29", "Dimensions", "Flange mounting hole radius29")
params.flange_mounting_hole_radius29 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius30", "Dimensions", "Flange mounting hole radius30")
params.flange_mounting_hole_radius30 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius31", "Dimensions", "Flange mounting hole radius31")
params.flange_mounting_hole_radius31 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius32", "Dimensions", "Flange mounting hole radius32")
params.flange_mounting_hole_radius32 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius33", "Dimensions", "Flange mounting hole radius33")
params.flange_mounting_hole_radius33 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius34", "Dimensions", "Flange mounting hole radius34")
params.flange_mounting_hole_radius34 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius35", "Dimensions", "Flange mounting hole radius35")
params.flange_mounting_hole_radius35 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius36", "Dimensions", "Flange mounting hole radius36")
params.flange_mounting_hole_radius36 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius37", "Dimensions", "Flange mounting hole radius37")
params.flange_mounting_hole_radius37 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius38", "Dimensions", "Flange mounting hole radius38")
params.flange_mounting_hole_radius38 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius39", "Dimensions", "Flange mounting hole radius39")
params.flange_mounting_hole_radius39 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius40", "Dimensions", "Flange mounting hole radius40")
params.flange_mounting_hole_radius40 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius41", "Dimensions", "Flange mounting hole radius41")
params.flange_mounting_hole_radius41 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius42", "Dimensions", "Flange mounting hole radius42")
params.flange_mounting_hole_radius42 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius43", "Dimensions", "Flange mounting hole radius43")
params.flange_mounting_hole_radius43 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius44", "Dimensions", "Flange mounting hole radius44")
params.flange_mounting_hole_radius44 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius45", "Dimensions", "Flange mounting hole radius45")
params.flange_mounting_hole_radius45 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius46", "Dimensions", "Flange mounting hole radius46")
params.flange_mounting_hole_radius46 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius47", "Dimensions", "Flange mounting hole radius47")
params.flange_mounting_hole_radius47 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius48", "Dimensions", "Flange mounting hole radius48")
params.flange_mounting_hole_radius48 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius49", "Dimensions", "Flange mounting hole radius49")
params.flange_mounting_hole_radius49 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius50", "Dimensions", "Flange mounting hole radius50")
params.flange_mounting_hole_radius50 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius51", "Dimensions", "Flange mounting hole radius51")
params.flange_mounting_hole_radius51 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius52", "Dimensions", "Flange mounting hole radius52")
params.flange_mounting_hole_radius52 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius53", "Dimensions", "Flange mounting hole radius53")
params.flange_mounting_hole_radius53 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius54", "Dimensions", "Flange mounting hole radius54")
params.flange_mounting_hole_radius54 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius55", "Dimensions", "Flange mounting hole radius55")
params.flange_mounting_hole_radius55 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius56", "Dimensions", "Flange mounting hole radius56")
params.flange_mounting_hole_radius56 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius57", "Dimensions", "Flange mounting hole radius57")
params.flange_mounting_hole_radius57 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius58", "Dimensions", "Flange mounting hole radius58")
params.flange_mounting_hole_radius58 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius59", "Dimensions", "Flange mounting hole radius59")
params.flange_mounting_hole_radius59 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius60", "Dimensions", "Flange mounting hole radius60")
params.flange_mounting_hole_radius60 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius61", "Dimensions", "Flange mounting hole radius61")
params.flange_mounting_hole_radius61 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius62", "Dimensions", "Flange mounting hole radius62")
params.flange_mounting_hole_radius62 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius63", "Dimensions", "Flange mounting hole radius63")
params.flange_mounting_hole_radius63 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius64", "Dimensions", "Flange mounting hole radius64")
params.flange_mounting_hole_radius64 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius65", "Dimensions", "Flange mounting hole radius65")
params.flange_mounting_hole_radius65 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius66", "Dimensions", "Flange mounting hole radius66")
params.flange_mounting_hole_radius66 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius67", "Dimensions", "Flange mounting hole radius67")
params.flange_mounting_hole_radius67 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius68", "Dimensions", "Flange mounting hole radius68")
params.flange_mounting_hole_radius68 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius69", "Dimensions", "Flange mounting hole radius69")
params.flange_mounting_hole_radius69 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius70", "Dimensions", "Flange mounting hole radius70")
params.flange_mounting_hole_radius70 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius71", "Dimensions", "Flange mounting hole radius71")
params.flange_mounting_hole_radius71 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius72", "Dimensions", "Flange mounting hole radius72")
params.flange_mounting_hole_radius72 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius73", "Dimensions", "Flange mounting hole radius73")
params.flange_mounting_hole_radius73 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius74", "Dimensions", "Flange mounting hole radius74")
params.flange_mounting_hole_radius74 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius75", "Dimensions", "Flange mounting hole radius75")
params.flange_mounting_hole_radius75 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius76", "Dimensions", "Flange mounting hole radius76")
params.flange_mounting_hole_radius76 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius77", "Dimensions", "Flange mounting hole radius77")
params.flange_mounting_hole_radius77 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius78", "Dimensions", "Flange mounting hole radius78")
params.flange_mounting_hole_radius78 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius79", "Dimensions", "Flange mounting hole radius79")
params.flange_mounting_hole_radius79 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius80", "Dimensions", "Flange mounting hole radius80")
params.flange_mounting_hole_radius80 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius81", "Dimensions", "Flange mounting hole radius81")
params.flange_mounting_hole_radius81 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius82", "Dimensions", "Flange mounting hole radius82")
params.flange_mounting_hole_radius82 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius83", "Dimensions", "Flange mounting hole radius83")
params.flange_mounting_hole_radius83 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius84", "Dimensions", "Flange mounting hole radius84")
params.flange_mounting_hole_radius84 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius85", "Dimensions", "Flange mounting hole radius85")
params.flange_mounting_hole_radius85 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius86", "Dimensions", "Flange mounting hole radius86")
params.flange_mounting_hole_radius86 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius87", "Dimensions", "Flange mounting hole radius87")
params.flange_mounting_hole_radius87 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius88", "Dimensions", "Flange mounting hole radius88")
params.flange_mounting_hole_radius88 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius89", "Dimensions", "Flange mounting hole radius89")
params.flange_mounting_hole_radius89 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius90", "Dimensions", "Flange mounting hole radius90")
params.flange_mounting_hole_radius90 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius91", "Dimensions", "Flange mounting hole radius91")
params.flange_mounting_hole_radius91 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius92", "Dimensions", "Flange mounting hole radius92")
params.flange_mounting_hole_radius92 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius93", "Dimensions", "Flange mounting hole radius93")
params.flange_mounting_hole_radius93 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius94", "Dimensions", "Flange mounting hole radius94")
params.flange_mounting_hole_radius94 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius95", "Dimensions", "Flange mounting hole radius95")
params.flange_mounting_hole_radius95 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius96", "Dimensions", "Flange mounting hole radius96")
params.flange_mounting_hole_radius96 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius97", "Dimensions", "Flange mounting hole radius97")
params.flange_mounting_hole_radius97 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius98", "Dimensions", "Flange mounting hole radius98")
params.flange_mounting_hole_radius98 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius99", "Dimensions", "Flange mounting hole radius99")
params.flange_mounting_hole_radius99 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius100", "Dimensions", "Flange mounting hole radius100")
params.flange_mounting_hole_radius100 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius101", "Dimensions", "Flange mounting hole radius101")
params.flange_mounting_hole_radius101 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius102", "Dimensions", "Flange mounting hole radius102")
params.flange_mounting_hole_radius102 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius103", "Dimensions", "Flange mounting hole radius103")
params.flange_mounting_hole_radius103 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius104", "Dimensions", "Flange mounting hole radius104")
params.flange_mounting_hole_radius104 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius105", "Dimensions", "Flange mounting hole radius105")
params.flange_mounting_hole_radius105 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius106", "Dimensions", "Flange mounting hole radius106")
params.flange_mounting_hole_radius106 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius107", "Dimensions", "Flange mounting hole radius107")
params.flange_mounting_hole_radius107 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius108", "Dimensions", "Flange mounting hole radius108")
params.flange_mounting_hole_radius108 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius109", "Dimensions", "Flange mounting hole radius109")
params.flange_mounting_hole_radius109 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius110", "Dimensions", "Flange mounting hole radius110")
params.flange_mounting_hole_radius110 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius111", "Dimensions", "Flange mounting hole radius111")
params.flange_mounting_hole_radius111 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius112", "Dimensions", "Flange mounting hole radius112")
params.flange_mounting_hole_radius112 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius113", "Dimensions", "Flange mounting hole radius113")
params.flange_mounting_hole_radius113 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius114", "Dimensions", "Flange mounting hole radius114")
params.flange_mounting_hole_radius114 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius115", "Dimensions", "Flange mounting hole radius115")
params.flange_mounting_hole_radius115 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius116", "Dimensions", "Flange mounting hole radius116")
params.flange_mounting_hole_radius116 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius117", "Dimensions", "Flange mounting hole radius117")
params.flange_mounting_hole_radius117 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius118", "Dimensions", "Flange mounting hole radius118")
params.flange_mounting_hole_radius118 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius119", "Dimensions", "Flange mounting hole radius119")
params.flange_mounting_hole_radius119 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius120", "Dimensions", "Flange mounting hole radius120")
params.flange_mounting_hole_radius120 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius121", "Dimensions", "Flange mounting hole radius121")
params.flange_mounting_hole_radius121 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius122", "Dimensions", "Flange mounting hole radius122")
params.flange_mounting_hole_radius122 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius123", "Dimensions", "Flange mounting hole radius123")
params.flange_mounting_hole_radius123 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius124", "Dimensions", "Flange mounting hole radius124")
params.flange_mounting_hole_radius124 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius125", "Dimensions", "Flange mounting hole radius125")
params.flange_mounting_hole_radius125 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius126", "Dimensions", "Flange mounting hole radius126")
params.flange_mounting_hole_radius126 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius127", "Dimensions", "Flange mounting hole radius127")
params.flange_mounting_hole_radius127 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius128", "Dimensions", "Flange mounting hole radius128")
params.flange_mounting_hole_radius128 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius129", "Dimensions", "Flange mounting hole radius129")
params.flange_mounting_hole_radius129 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius130", "Dimensions", "Flange mounting hole radius130")
params.flange_mounting_hole_radius130 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius131", "Dimensions", "Flange mounting hole radius131")
params.flange_mounting_hole_radius131 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius132", "Dimensions", "Flange mounting hole radius132")
params.flange_mounting_hole_radius132 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius133", "Dimensions", "Flange mounting hole radius133")
params.flange_mounting_hole_radius133 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius134", "Dimensions", "Flange mounting hole radius134")
params.flange_mounting_hole_radius134 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius135", "Dimensions", "Flange mounting hole radius135")
params.flange_mounting_hole_radius135 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius136", "Dimensions", "Flange mounting hole radius136")
params.flange_mounting_hole_radius136 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius137", "Dimensions", "Flange mounting hole radius137")
params.flange_mounting_hole_radius137 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius138", "Dimensions", "Flange mounting hole radius138")
params.flange_mounting_hole_radius138 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius139", "Dimensions", "Flange mounting hole radius139")
params.flange_mounting_hole_radius139 = 29.2

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius140", "Dimensions", "Flange mounting hole radius140")
params.flange_mounting_hole_radius140 = 42.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius141", "Dimensions", "Flange mounting hole radius141")
params.flange_mounting_hole_radius141 = 40.04

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius142", "Dimensions", "Flange mounting hole radius142")
params.flange_mounting_hole_radius142 = 30.91

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius143", "Dimensions", "Flange mounting hole radius143")
params.flange_mounting_hole_radius143 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius144", "Dimensions", "Flange mounting hole radius144")
params.flange_mounting_hole_radius144 = 2.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius145", "Dimensions", "Flange mounting hole radius145")
params.flange_mounting_hole_radius145 = 8.68

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius146", "Dimensions", "Flange mounting hole radius146")
params.flange_mounting_hole_radius146 = 19.4

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius147", "Dimensions", "Flange mounting hole radius147")
params.flange_mounting_hole_radius147 = 21.0

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius148", "Dimensions", "Flange mounting hole radius148")
params.flange_mounting_hole_radius148 = 38.9

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius149", "Dimensions", "Flange mounting hole radius149")
params.flange_mounting_hole_radius149 = 19.62

params.addProperty("App::PropertyLength", "flange_mounting_hole_radius150", "Dimensions", "Flange mounting hole radius150")
params.flange_mounting_hole_radius150 = 29
