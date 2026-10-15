import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("BoomCylinderPistonRing")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "D1", "Dimensions", "Outer Diameter")
params.D1 = 276.5
params.addProperty("App::PropertyLength", "D2", "Dimensions", "Outer Flange Diameter")
params.D2 = 272.0
params.addProperty("App::PropertyLength", "D3", "Dimensions", "Main Body Diameter")
params.D3 = 252.0
params.addProperty("App::PropertyLength", "D4", "Dimensions", "Inner Bore Diameter")
params.D4 = 197.0
params.addProperty("App::PropertyLength", "D5", "Dimensions", "Inner Shoulder Diameter")
params.D5 = 171.0
params.addProperty("App::PropertyLength", "D6", "Dimensions", "Inner Shoulder Diameter 2")
params.D6 = 166.0
params.addProperty("App::PropertyLength", "D7", "Dimensions", "Inner Bore Diameter 2")
params.D7 = 166.0
params.addProperty("App::PropertyLength", "H1", "Dimensions", "Total Height")
params.H1 = 169.0
params.addProperty("App::PropertyLength", "H2", "Dimensions", "Flange Height")
params.H2 = 64.0
params.addProperty("App::PropertyLength", "H3", "Dimensions", "Main Body Height")
params.H3 = 105.0
params.addProperty("App::PropertyLength", "H4", "Dimensions", "Inner Shoulder Height")
params.H4 = 31.0
params.addProperty("App::PropertyLength", "H5", "Dimensions", "Inner Shoulder Height 2")
params.H5 = 14.0
params.addProperty("App::PropertyLength", "H6", "Dimensions", "Inner Bore Height")
params.H6 = 10.0
params.addProperty("App::PropertyLength", "R1", "Dimensions", "Outer Fillet Radius")
params.R1 = 4.0
params.addProperty("App::PropertyLength", "R2", "Dimensions", "Inner Shoulder Fillet Radius")
params.R2 = 0.4
params.addProperty("App::PropertyLength", "R3", "Dimensions", "Inner Bore Fillet Radius")
params.R3 = 0.4
params.addProperty("App::PropertyLength", "R4", "Dimensions", "Inner Bore Fillet Radius 2")
params.R4 = 0.4
params.addProperty("App::PropertyLength", "R5", "Dimensions", "Inner Bore Fillet Radius 3")
params.R5 = 0.4
params.addProperty("App::PropertyLength", "R6", "Dimensions", "Inner Bore Fillet Radius 4")
params.R6 = 0.4
params.addProperty("App::PropertyLength", "R7", "Dimensions", "Inner Bore Fillet Radius 5")
params.R7 = 0.4
params.addProperty("App::PropertyLength", "R8", "Dimensions", "Inner Bore Fillet Radius 6")
params.R8 = 0.4
params.addProperty("App::PropertyLength", "R9", "Dimensions", "Inner Bore Fillet Radius 7")
params.R9 = 0.4
params.addProperty("App::PropertyLength", "R10", "Dimensions", "Inner Bore Fillet Radius 8")
params.R10 = 0.4
params.addProperty("App::PropertyLength", "R11", "Dimensions", "Inner Bore Fillet Radius 9")
params.R11 = 0.4
params.addProperty("App::PropertyLength", "R12", "Dimensions", "Inner Bore Fillet Radius 10")
params.R12 = 0.4
params.addProperty("App::PropertyLength", "R13", "Dimensions", "Inner Bore Fillet Radius 11")
params.R13 = 0.4
params.addProperty("App::PropertyLength", "R14", "Dimensions", "Inner Bore Fillet Radius 12")
params.R14 = 0.4
params.addProperty("App::PropertyLength", "R15", "Dimensions", "Inner Bore Fillet Radius 13")
params.R15 = 0.4
params.addProperty("App::PropertyLength", "R16", "Dimensions", "Inner Bore Fillet Radius 14")
params.R16 = 0.4
params.addProperty("App::PropertyLength", "R17", "Dimensions", "Inner Bore Fillet Radius 15")
params.R17 = 0.4
params.addProperty("App::PropertyLength", "R18", "Dimensions", "Inner Bore Fillet Radius 16")
params.R18 = 0.4
params.addProperty("App::PropertyLength", "R19", "Dimensions", "Inner Bore Fillet Radius 17")
params.R19 = 0.4
params.addProperty("App::PropertyLength", "R20", "Dimensions", "Inner Bore Fillet Radius 18")
params.R20 = 0.4
params.addProperty("App::PropertyLength", "R21", "Dimensions", "Inner Bore Fillet Radius 19")
params.R21 = 0.4
params.addProperty("App::PropertyLength", "R22", "Dimensions", "Inner Bore Fillet Radius 20")
params.R22 = 0.4
params.addProperty("App::PropertyLength", "R23", "Dimensions", "Inner Bore Fillet Radius 21")
params.R23 = 0.4
params.addProperty("App::PropertyLength", "R24", "Dimensions", "Inner Bore Fillet Radius 22")
params.R24 = 0.4
params.addProperty("App::PropertyLength", "R25", "Dimensions", "Inner Bore Fillet Radius 23")
params.R25 = 0.4
params.addProperty("App::PropertyLength", "R26", "Dimensions", "Inner Bore Fillet Radius 24")
params.R26 = 0.4
params.addProperty("App::PropertyLength", "R27", "Dimensions", "Inner Bore Fillet Radius 25")
params.R27 = 0.4
params.addProperty("App::PropertyLength", "R28", "Dimensions", "Inner Bore Fillet Radius 26")
params.R28 = 0.4
params.addProperty("App::PropertyLength", "R29", "Dimensions", "Inner Bore Fillet Radius 27")
params.R29 = 0.4
params.addProperty("App::PropertyLength", "R30", "Dimensions", "Inner Bore Fillet Radius 28")
params.R30 = 0.4
params.addProperty("App::PropertyLength", "R31", "Dimensions", "Inner Bore Fillet Radius 29")
params.R31 = 0.4
params.addProperty("App::PropertyLength", "R32", "Dimensions", "Inner Bore Fillet Radius 30")
params.R32 = 0.4
params.addProperty("App::PropertyLength", "R33", "Dimensions", "Inner Bore Fillet Radius 31")
params.R33 = 0.4
params.addProperty("App::PropertyLength", "R34", "Dimensions", "Inner Bore Fillet Radius 32")
params.R34 = 0.4
params.addProperty("App::PropertyLength", "R35", "Dimensions", "Inner Bore Fillet Radius 33")
params.R35 = 0.4
params.addProperty("App::PropertyLength", "R36", "Dimensions", "Inner Bore Fillet Radius 34")
params.R36 = 0.4
params.addProperty("App::PropertyLength", "R37", "Dimensions", "Inner Bore Fillet Radius 35")
params.R37 = 0.4
params.addProperty("App::PropertyLength", "R38", "Dimensions", "Inner Bore Fillet Radius 36")
params.R38 = 0.4
params.addProperty("App::PropertyLength", "R39", "Dimensions", "Inner Bore Fillet Radius 37")
params.R39 = 0.4
params.addProperty("App::PropertyLength", "R40", "Dimensions", "Inner Bore Fillet Radius 38")
params.R40 = 0.4
params.addProperty("App::PropertyLength", "R41", "Dimensions", "Inner Bore Fillet Radius 39")
params.R41 = 0.4
params.addProperty("App::PropertyLength", "R42", "Dimensions", "Inner Bore Fillet Radius 40")
params.R42 = 0.4
params.addProperty("App::PropertyLength", "R43", "Dimensions", "Inner Bore Fillet Radius 41")
params.R43 = 0.4
params.addProperty("App::PropertyLength", "R44", "Dimensions", "Inner Bore Fillet Radius 42")
params.R44 = 0.4
params.addProperty("App::PropertyLength", "R45", "Dimensions", "Inner Bore Fillet Radius 43")
params.R45 = 0.4
params.addProperty("App::PropertyLength", "R46", "Dimensions", "Inner Bore Fillet Radius 44")
params.R46 = 0.4
params.addProperty("App::PropertyLength", "R47", "Dimensions", "Inner Bore Fillet Radius 45")
params.R47 = 0.4
params.addProperty("App::PropertyLength", "R48", "Dimensions", "Inner Bore Fillet Radius 46")
params.R48 = 0.4
params.addProperty("App::PropertyLength", "R49", "Dimensions", "Inner Bore Fillet Radius 47")
params.R49 = 0.4
params.addProperty("App::PropertyLength", "R50", "Dimensions", "Inner Bore Fillet Radius 48")
params.R50 = 0.4
params.addProperty("App::PropertyLength", "R51", "Dimensions", "Inner Bore Fillet Radius 49")
params.R51 = 0.4
params.addProperty("App::PropertyLength", "R52", "Dimensions", "Inner Bore Fillet Radius 50")
params.R52 = 0.4
params.addProperty("App::PropertyLength", "R53", "Dimensions", "Inner Bore Fillet Radius 51")
params.R53 = 0.4
params.addProperty("App::PropertyLength", "R54", "Dimensions", "Inner Bore Fillet Radius 52")
params.R54 = 0.4
params.addProperty("App::PropertyLength", "R55", "Dimensions", "Inner Bore Fillet Radius 53")
params.R55 = 0.4
params.addProperty("App::PropertyLength", "R56", "Dimensions", "Inner Bore Fillet Radius 54")
params.R56 = 0.4
params.addProperty("App::PropertyLength", "R57", "Dimensions", "Inner Bore Fillet Radius 55")
params.R57 = 0.4
params.addProperty("App::PropertyLength", "R58", "Dimensions", "Inner Bore Fillet Radius 56")
params.R58 = 0.4
params.addProperty("App::PropertyLength", "R59", "Dimensions", "Inner Bore Fillet Radius 57")
params.R59 = 0.4
params.addProperty("App::PropertyLength", "R60", "Dimensions", "Inner Bore Fillet Radius 58")
params.R60 = 0.4
params.addProperty("App::PropertyLength", "R61", "Dimensions", "Inner Bore Fillet Radius 59")
params.R61 = 0.4
params.addProperty("App::PropertyLength", "R62", "Dimensions", "Inner Bore Fillet Radius 60")
params.R62 = 0.4
params.addProperty("App::PropertyLength", "R63", "Dimensions", "Inner Bore Fillet Radius 61")
params.R63 = 0.4
params.addProperty("App::PropertyLength", "R64", "Dimensions", "Inner Bore Fillet Radius 62")
params.R64 = 0.4
params.addProperty("App::PropertyLength", "R65", "Dimensions", "Inner Bore Fillet Radius 63")
params.R65 = 0.4
params.addProperty("App::PropertyLength", "R66", "Dimensions", "Inner Bore Fillet Radius 64")
params.R66 = 0.4
params.addProperty("App::PropertyLength", "R67", "Dimensions", "Inner Bore Fillet Radius 65")
params.R67 = 0.4
params.addProperty("App::PropertyLength", "R68", "Dimensions", "Inner Bore Fillet Radius 66")
params.R68 = 0.4
params.addProperty("App::PropertyLength", "R69", "Dimensions", "Inner Bore Fillet Radius 67")
params.R69 = 0.4
params.addProperty("App::PropertyLength", "R70", "Dimensions", "Inner Bore Fillet Radius 68")
params.R70 = 0.4
params.addProperty("App::PropertyLength", "R71", "Dimensions", "Inner Bore Fillet Radius 69")
params.R71 = 0.4
params.addProperty("App::PropertyLength", "R72", "Dimensions", "Inner Bore Fillet Radius 70")
params.R72 = 0.4
params.addProperty("App::PropertyLength", "R73", "Dimensions", "Inner Bore Fillet Radius 71")
params.R73 = 0.4
params.addProperty("App::PropertyLength", "R74", "Dimensions", "Inner Bore Fillet Radius 72")
params.R74 = 0.4
params.addProperty("App::PropertyLength", "R75", "Dimensions", "Inner Bore Fillet Radius 73")
params.R75 = 0.4
params.addProperty("App::PropertyLength", "R76", "Dimensions", "Inner Bore Fillet Radius 74")
params.R76 = 0.4
params.addProperty("App::PropertyLength", "R77", "Dimensions", "Inner Bore Fillet Radius 75")
params.R77 = 0.4
params.addProperty("App::PropertyLength", "R78", "Dimensions", "Inner Bore Fillet Radius 76")
params.R78 = 0.4
params.addProperty("App::PropertyLength", "R79", "Dimensions", "Inner Bore Fillet Radius 77")
params.R79 = 0.4
params.addProperty("App::PropertyLength", "R80", "Dimensions", "Inner Bore Fillet Radius 78")
params.R80 = 0.4
params.addProperty("App::PropertyLength", "R81", "Dimensions", "Inner Bore Fillet Radius 79")
params.R81 = 0.4
params.addProperty("App::PropertyLength", "R82", "Dimensions", "Inner Bore Fillet Radius 80")
params.R82 = 0.4
params.addProperty("App::PropertyLength", "R83", "Dimensions", "Inner Bore Fillet Radius 81")
params.R83 = 0.4
params.addProperty("App::PropertyLength", "R84", "Dimensions", "Inner Bore Fillet Radius 82")
params.R84 = 0.4
params.addProperty("App::PropertyLength", "R85", "Dimensions", "Inner Bore Fillet Radius 83")
params.R85 = 0.4
params.addProperty("App::PropertyLength", "R86", "Dimensions", "Inner Bore Fillet Radius 84")
params.R86 = 0.4
params.addProperty("App::PropertyLength", "R87", "Dimensions", "Inner Bore Fillet Radius 85")
params.R87 = 0.4
params.addProperty("App::PropertyLength", "R88", "Dimensions", "Inner Bore Fillet Radius 86")
params.R88 = 0.4
params.addProperty("App::PropertyLength", "R89", "Dimensions", "Inner Bore Fillet Radius 87")
params.R89 = 0.4
params.addProperty("App::PropertyLength", "R90", "Dimensions", "Inner Bore Fillet Radius 88")
params.R90 = 0.4
params.addProperty("App::PropertyLength", "R91", "Dimensions", "Inner Bore Fillet Radius 89")
params.R91 = 0.4
params.addProperty("App::PropertyLength", "R92", "Dimensions", "Inner Bore Fillet Radius 90")
params.R92 = 0.4
params.addProperty("App::PropertyLength", "R93", "Dimensions", "Inner Bore Fillet Radius 91")
params.R93 = 0.4
params.addProperty("App::PropertyLength", "R94", "Dimensions", "Inner Bore Fillet Radius 92")
params.R94 = 0.4
params.addProperty("App::PropertyLength", "R95", "Dimensions", "Inner Bore Fillet Radius 93")
params.R95 = 0.4
params.addProperty("App::PropertyLength", "R96", "Dimensions", "Inner Bore
