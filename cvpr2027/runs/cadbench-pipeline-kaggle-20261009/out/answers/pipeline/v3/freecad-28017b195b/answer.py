import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("FPV_Mount")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "base_width", "Dimensions", "Base width")
params.base_width = 42.34
params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Base height")
params.base_height = 16.0
params.addProperty("App::PropertyLength", "arm_length", "Dimensions", "Arm length")
params.arm_length = 19.85
params.addProperty("App::PropertyLength", "arm_width", "Dimensions", "Arm width")
params.arm_width = 13.0
params.addProperty("App::PropertyLength", "mount_height", "Dimensions", "Mount height")
params.mount_height = 14.55
params.addProperty("App::PropertyLength", "mount_width", "Dimensions", "Mount width")
params.mount_width = 20.0
params.addProperty("App::PropertyLength", "hole_diameter", "Dimensions", "Mount hole diameter")
params.hole_diameter = 3.0
params.addProperty("App::PropertyLength", "hole_spacing", "Dimensions", "Mount hole spacing")
params.hole_spacing = 16.9
params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet radius")
params.fillet_radius = 1.0
params.addProperty("App::PropertyLength", "chamfer_size", "Dimensions", "Chamfer size")
params.chamfer_size = 1.0
params.addProperty("App::PropertyLength", "arm_hole_diameter", "Dimensions", "Arm hole diameter")
params.arm_hole_diameter = 2.0
params.addProperty("App::PropertyLength", "arm_hole_spacing", "Dimensions", "Arm hole spacing")
params.arm_hole_spacing = 9.0
params.addProperty("App::PropertyLength", "arm_hole_offset", "Dimensions", "Arm hole offset")
params.arm_hole_offset = 1.49
params.addProperty("App::PropertyLength", "mount_hole_diameter", "Dimensions", "Mount hole diameter")
params.mount_hole_diameter = 3.5
params.addProperty("App::PropertyLength", "mount_hole_offset", "Dimensions", "Mount hole offset")
params.mount_hole_offset = 2.81
params.addProperty("App::PropertyLength", "mount_hole_spacing", "Dimensions", "Mount hole spacing")
params.mount_hole_spacing = 12.68
params.addProperty("App::PropertyLength", "mount_hole_radius", "Dimensions", "Mount hole radius")
params.mount_hole_radius = 0.68
params.addProperty("App::PropertyLength", "arm_hole_radius", "Dimensions", "Arm hole radius")
params.arm_hole_radius = 1.3
params.addProperty("App::PropertyLength", "arm_hole_offset2", "Dimensions", "Arm hole offset 2")
params.arm_hole_offset2 = 1.19
params.addProperty("App::PropertyLength", "arm_hole_offset3", "Dimensions", "Arm hole offset 3")
params.arm_hole_offset3 = 1.14
params.addProperty("App::PropertyLength", "arm_hole_offset4", "Dimensions", "Arm hole offset 4")
params.arm_hole_offset4 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset5", "Dimensions", "Arm hole offset 5")
params.arm_hole_offset5 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset6", "Dimensions", "Arm hole offset 6")
params.arm_hole_offset6 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset7", "Dimensions", "Arm hole offset 7")
params.arm_hole_offset7 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset8", "Dimensions", "Arm hole offset 8")
params.arm_hole_offset8 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset9", "Dimensions", "Arm hole offset 9")
params.arm_hole_offset9 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset10", "Dimensions", "Arm hole offset 10")
params.arm_hole_offset10 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset11", "Dimensions", "Arm hole offset 11")
params.arm_hole_offset11 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset12", "Dimensions", "Arm hole offset 12")
params.arm_hole_offset12 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset13", "Dimensions", "Arm hole offset 13")
params.arm_hole_offset13 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset14", "Dimensions", "Arm hole offset 14")
params.arm_hole_offset14 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset15", "Dimensions", "Arm hole offset 15")
params.arm_hole_offset15 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset16", "Dimensions", "Arm hole offset 16")
params.arm_hole_offset16 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset17", "Dimensions", "Arm hole offset 17")
params.arm_hole_offset17 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset18", "Dimensions", "Arm hole offset 18")
params.arm_hole_offset18 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset19", "Dimensions", "Arm hole offset 19")
params.arm_hole_offset19 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset20", "Dimensions", "Arm hole offset 20")
params.arm_hole_offset20 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset21", "Dimensions", "Arm hole offset 21")
params.arm_hole_offset21 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset22", "Dimensions", "Arm hole offset 22")
params.arm_hole_offset22 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset23", "Dimensions", "Arm hole offset 23")
params.arm_hole_offset23 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset24", "Dimensions", "Arm hole offset 24")
params.arm_hole_offset24 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset25", "Dimensions", "Arm hole offset 25")
params.arm_hole_offset25 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset26", "Dimensions", "Arm hole offset 26")
params.arm_hole_offset26 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset27", "Dimensions", "Arm hole offset 27")
params.arm_hole_offset27 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset28", "Dimensions", "Arm hole offset 28")
params.arm_hole_offset28 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset29", "Dimensions", "Arm hole offset 29")
params.arm_hole_offset29 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset30", "Dimensions", "Arm hole offset 30")
params.arm_hole_offset30 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset31", "Dimensions", "Arm hole offset 31")
params.arm_hole_offset31 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset32", "Dimensions", "Arm hole offset 32")
params.arm_hole_offset32 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset33", "Dimensions", "Arm hole offset 33")
params.arm_hole_offset33 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset34", "Dimensions", "Arm hole offset 34")
params.arm_hole_offset34 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset35", "Dimensions", "Arm hole offset 35")
params.arm_hole_offset35 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset36", "Dimensions", "Arm hole offset 36")
params.arm_hole_offset36 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset37", "Dimensions", "Arm hole offset 37")
params.arm_hole_offset37 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset38", "Dimensions", "Arm hole offset 38")
params.arm_hole_offset38 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset39", "Dimensions", "Arm hole offset 39")
params.arm_hole_offset39 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset40", "Dimensions", "Arm hole offset 40")
params.arm_hole_offset40 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset41", "Dimensions", "Arm hole offset 41")
params.arm_hole_offset41 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset42", "Dimensions", "Arm hole offset 42")
params.arm_hole_offset42 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset43", "Dimensions", "Arm hole offset 43")
params.arm_hole_offset43 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset44", "Dimensions", "Arm hole offset 44")
params.arm_hole_offset44 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset45", "Dimensions", "Arm hole offset 45")
params.arm_hole_offset45 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset46", "Dimensions", "Arm hole offset 46")
params.arm_hole_offset46 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset47", "Dimensions", "Arm hole offset 47")
params.arm_hole_offset47 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset48", "Dimensions", "Arm hole offset 48")
params.arm_hole_offset48 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset49", "Dimensions", "Arm hole offset 49")
params.arm_hole_offset49 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset50", "Dimensions", "Arm hole offset 50")
params.arm_hole_offset50 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset51", "Dimensions", "Arm hole offset 51")
params.arm_hole_offset51 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset52", "Dimensions", "Arm hole offset 52")
params.arm_hole_offset52 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset53", "Dimensions", "Arm hole offset 53")
params.arm_hole_offset53 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset54", "Dimensions", "Arm hole offset 54")
params.arm_hole_offset54 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset55", "Dimensions", "Arm hole offset 55")
params.arm_hole_offset55 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset56", "Dimensions", "Arm hole offset 56")
params.arm_hole_offset56 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset57", "Dimensions", "Arm hole offset 57")
params.arm_hole_offset57 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset58", "Dimensions", "Arm hole offset 58")
params.arm_hole_offset58 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset59", "Dimensions", "Arm hole offset 59")
params.arm_hole_offset59 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset60", "Dimensions", "Arm hole offset 60")
params.arm_hole_offset60 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset61", "Dimensions", "Arm hole offset 61")
params.arm_hole_offset61 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset62", "Dimensions", "Arm hole offset 62")
params.arm_hole_offset62 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset63", "Dimensions", "Arm hole offset 63")
params.arm_hole_offset63 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset64", "Dimensions", "Arm hole offset 64")
params.arm_hole_offset64 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset65", "Dimensions", "Arm hole offset 65")
params.arm_hole_offset65 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset66", "Dimensions", "Arm hole offset 66")
params.arm_hole_offset66 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset67", "Dimensions", "Arm hole offset 67")
params.arm_hole_offset67 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset68", "Dimensions", "Arm hole offset 68")
params.arm_hole_offset68 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset69", "Dimensions", "Arm hole offset 69")
params.arm_hole_offset69 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset70", "Dimensions", "Arm hole offset 70")
params.arm_hole_offset70 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset71", "Dimensions", "Arm hole offset 71")
params.arm_hole_offset71 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset72", "Dimensions", "Arm hole offset 72")
params.arm_hole_offset72 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset73", "Dimensions", "Arm hole offset 73")
params.arm_hole_offset73 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset74", "Dimensions", "Arm hole offset 74")
params.arm_hole_offset74 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset75", "Dimensions", "Arm hole offset 75")
params.arm_hole_offset75 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset76", "Dimensions", "Arm hole offset 76")
params.arm_hole_offset76 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset77", "Dimensions", "Arm hole offset 77")
params.arm_hole_offset77 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset78", "Dimensions", "Arm hole offset 78")
params.arm_hole_offset78 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset79", "Dimensions", "Arm hole offset 79")
params.arm_hole_offset79 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset80", "Dimensions", "Arm hole offset 80")
params.arm_hole_offset80 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset81", "Dimensions", "Arm hole offset 81")
params.arm_hole_offset81 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset82", "Dimensions", "Arm hole offset 82")
params.arm_hole_offset82 = 1.49
params.addProperty("App::PropertyLength", "arm_hole_offset83", "Dimensions", "Arm hole offset 83")
params.arm_hole_offset83 = 1.4
