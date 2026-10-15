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
params.flange_mounting_hole_radius70 = 2
