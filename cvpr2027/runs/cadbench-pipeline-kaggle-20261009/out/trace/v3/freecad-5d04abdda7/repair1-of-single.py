import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("LatheTailstockBody")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "MainLength", "Dimensions", "Overall length")
params.MainLength = 310.0

params.addProperty("App::PropertyLength", "MainWidth", "Dimensions", "Overall width")
params.MainWidth = 190.0

params.addProperty("App::PropertyLength", "BaseWidth", "Dimensions", "Base width")
params.BaseWidth = 210.0

params.addProperty("App::PropertyLength", "BaseHeight", "Dimensions", "Base height")
params.BaseHeight = 35.0

params.addProperty("App::PropertyLength", "ShaftDiameter", "Dimensions", "Shaft diameter")
params.ShaftDiameter = 28.4

params.addProperty("App::PropertyLength", "ShaftLength", "Dimensions", "Shaft length")
params.ShaftLength = 120.0

params.addProperty("App::PropertyLength", "MountingPlateWidth", "Dimensions", "Mounting plate width")
params.MountingPlateWidth = 100.0

params.addProperty("App::PropertyLength", "MountingPlateHeight", "Dimensions", "Mounting plate height")
params.MountingPlateHeight = 35.0

params.addProperty("App::PropertyLength", "MountingPlateThickness", "Dimensions", "Mounting plate thickness")
params.MountingPlateThickness = 14.0

params.addProperty("App::PropertyLength", "MountingPlateOffset", "Dimensions", "Mounting plate offset from end")
params.MountingPlateOffset = 100.0

params.addProperty("App::PropertyLength", "MountingPlateDepth", "Dimensions", "Mounting plate depth")
params.MountingPlateDepth = 35.0

params.addProperty("App::PropertyLength", "MountingPlateThickness2", "Dimensions", "Mounting plate thickness 2")
params.MountingPlateThickness2 = 9.0

params.addProperty("App::PropertyLength", "MountingPlateThickness3", "Dimensions", "Mounting plate thickness 3")
params.MountingPlateThickness3 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness4", "Dimensions", "Mounting plate thickness 4")
params.MountingPlateThickness4 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness5", "Dimensions", "Mounting plate thickness 5")
params.MountingPlateThickness5 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness6", "Dimensions", "Mounting plate thickness 6")
params.MountingPlateThickness6 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness7", "Dimensions", "Mounting plate thickness 7")
params.MountingPlateThickness7 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness8", "Dimensions", "Mounting plate thickness 8")
params.MountingPlateThickness8 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness9", "Dimensions", "Mounting plate thickness 9")
params.MountingPlateThickness9 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness10", "Dimensions", "Mounting plate thickness 10")
params.MountingPlateThickness10 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness11", "Dimensions", "Mounting plate thickness 11")
params.MountingPlateThickness11 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness12", "Dimensions", "Mounting plate thickness 12")
params.MountingPlateThickness12 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness13", "Dimensions", "Mounting plate thickness 13")
params.MountingPlateThickness13 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness14", "Dimensions", "Mounting plate thickness 14")
params.MountingPlateThickness14 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness15", "Dimensions", "Mounting plate thickness 15")
params.MountingPlateThickness15 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness16", "Dimensions", "Mounting plate thickness 16")
params.MountingPlateThickness16 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness17", "Dimensions", "Mounting plate thickness 17")
params.MountingPlateThickness17 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness18", "Dimensions", "Mounting plate thickness 18")
params.MountingPlateThickness18 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness19", "Dimensions", "Mounting plate thickness 19")
params.MountingPlateThickness19 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness20", "Dimensions", "Mounting plate thickness 20")
params.MountingPlateThickness20 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness21", "Dimensions", "Mounting plate thickness 21")
params.MountingPlateThickness21 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness22", "Dimensions", "Mounting plate thickness 22")
params.MountingPlateThickness22 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness23", "Dimensions", "Mounting plate thickness 23")
params.MountingPlateThickness23 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness24", "Dimensions", "Mounting plate thickness 24")
params.MountingPlateThickness24 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness25", "Dimensions", "Mounting plate thickness 25")
params.MountingPlateThickness25 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness26", "Dimensions", "Mounting plate thickness 26")
params.MountingPlateThickness26 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness27", "Dimensions", "Mounting plate thickness 27")
params.MountingPlateThickness27 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness28", "Dimensions", "Mounting plate thickness 28")
params.MountingPlateThickness28 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness29", "Dimensions", "Mounting plate thickness 29")
params.MountingPlateThickness29 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness30", "Dimensions", "Mounting plate thickness 30")
params.MountingPlateThickness30 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness31", "Dimensions", "Mounting plate thickness 31")
params.MountingPlateThickness31 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness32", "Dimensions", "Mounting plate thickness 32")
params.MountingPlateThickness32 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness33", "Dimensions", "Mounting plate thickness 33")
params.MountingPlateThickness33 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness34", "Dimensions", "Mounting plate thickness 34")
params.MountingPlateThickness34 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness35", "Dimensions", "Mounting plate thickness 35")
params.MountingPlateThickness35 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness36", "Dimensions", "Mounting plate thickness 36")
params.MountingPlateThickness36 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness37", "Dimensions", "Mounting plate thickness 37")
params.MountingPlateThickness37 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness38", "Dimensions", "Mounting plate thickness 38")
params.MountingPlateThickness38 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness39", "Dimensions", "Mounting plate thickness 39")
params.MountingPlateThickness39 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness40", "Dimensions", "Mounting plate thickness 40")
params.MountingPlateThickness40 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness41", "Dimensions", "Mounting plate thickness 41")
params.MountingPlateThickness41 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness42", "Dimensions", "Mounting plate thickness 42")
params.MountingPlateThickness42 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness43", "Dimensions", "Mounting plate thickness 43")
params.MountingPlateThickness43 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness44", "Dimensions", "Mounting plate thickness 44")
params.MountingPlateThickness44 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness45", "Dimensions", "Mounting plate thickness 45")
params.MountingPlateThickness45 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness46", "Dimensions", "Mounting plate thickness 46")
params.MountingPlateThickness46 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness47", "Dimensions", "Mounting plate thickness 47")
params.MountingPlateThickness47 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness48", "Dimensions", "Mounting plate thickness 48")
params.MountingPlateThickness48 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness49", "Dimensions", "Mounting plate thickness 49")
params.MountingPlateThickness49 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness50", "Dimensions", "Mounting plate thickness 50")
params.MountingPlateThickness50 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness51", "Dimensions", "Mounting plate thickness 51")
params.MountingPlateThickness51 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness52", "Dimensions", "Mounting plate thickness 52")
params.MountingPlateThickness52 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness53", "Dimensions", "Mounting plate thickness 53")
params.MountingPlateThickness53 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness54", "Dimensions", "Mounting plate thickness 54")
params.MountingPlateThickness54 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness55", "Dimensions", "Mounting plate thickness 55")
params.MountingPlateThickness55 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness56", "Dimensions", "Mounting plate thickness 56")
params.MountingPlateThickness56 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness57", "Dimensions", "Mounting plate thickness 57")
params.MountingPlateThickness57 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness58", "Dimensions", "Mounting plate thickness 58")
params.MountingPlateThickness58 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness59", "Dimensions", "Mounting plate thickness 59")
params.MountingPlateThickness59 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness60", "Dimensions", "Mounting plate thickness 60")
params.MountingPlateThickness60 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness61", "Dimensions", "Mounting plate thickness 61")
params.MountingPlateThickness61 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness62", "Dimensions", "Mounting plate thickness 62")
params.MountingPlateThickness62 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness63", "Dimensions", "Mounting plate thickness 63")
params.MountingPlateThickness63 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness64", "Dimensions", "Mounting plate thickness 64")
params.MountingPlateThickness64 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness65", "Dimensions", "Mounting plate thickness 65")
params.MountingPlateThickness65 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness66", "Dimensions", "Mounting plate thickness 66")
params.MountingPlateThickness66 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness67", "Dimensions", "Mounting plate thickness 67")
params.MountingPlateThickness67 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness68", "Dimensions", "Mounting plate thickness 68")
params.MountingPlateThickness68 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness69", "Dimensions", "Mounting plate thickness 69")
params.MountingPlateThickness69 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness70", "Dimensions", "Mounting plate thickness 70")
params.MountingPlateThickness70 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness71", "Dimensions", "Mounting plate thickness 71")
params.MountingPlateThickness71 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness72", "Dimensions", "Mounting plate thickness 72")
params.MountingPlateThickness72 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness73", "Dimensions", "Mounting plate thickness 73")
params.MountingPlateThickness73 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness74", "Dimensions", "Mounting plate thickness 74")
params.MountingPlateThickness74 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness75", "Dimensions", "Mounting plate thickness 75")
params.MountingPlateThickness75 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness76", "Dimensions", "Mounting plate thickness 76")
params.MountingPlateThickness76 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness77", "Dimensions", "Mounting plate thickness 77")
params.MountingPlateThickness77 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness78", "Dimensions", "Mounting plate thickness 78")
params.MountingPlateThickness78 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness79", "Dimensions", "Mounting plate thickness 79")
params.MountingPlateThickness79 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness80", "Dimensions", "Mounting plate thickness 80")
params.MountingPlateThickness80 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness81", "Dimensions", "Mounting plate thickness 81")
params.MountingPlateThickness81 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness82", "Dimensions", "Mounting plate thickness 82")
params.MountingPlateThickness82 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness83", "Dimensions", "Mounting plate thickness 83")
params.MountingPlateThickness83 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness84", "Dimensions", "Mounting plate thickness 84")
params.MountingPlateThickness84 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness85", "Dimensions", "Mounting plate thickness 85")
params.MountingPlateThickness85 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness86", "Dimensions", "Mounting plate thickness 86")
params.MountingPlateThickness86 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness87", "Dimensions", "Mounting plate thickness 87")
params.MountingPlateThickness87 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness88", "Dimensions", "Mounting plate thickness 88")
params.MountingPlateThickness88 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness89", "Dimensions", "Mounting plate thickness 89")
params.MountingPlateThickness89 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness90", "Dimensions", "Mounting plate thickness 90")
params.MountingPlateThickness90 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness91", "Dimensions", "Mounting plate thickness 91")
params.MountingPlateThickness91 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness92", "Dimensions", "Mounting plate thickness 92")
params.MountingPlateThickness92 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness93", "Dimensions", "Mounting plate thickness 93")
params.MountingPlateThickness93 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness94", "Dimensions", "Mounting plate thickness 94")
params.MountingPlateThickness94 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness95", "Dimensions", "Mounting plate thickness 95")
params.MountingPlateThickness95 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness96", "Dimensions", "Mounting plate thickness 96")
params.MountingPlateThickness96 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness97", "Dimensions", "Mounting plate thickness 97")
params.MountingPlateThickness97 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness98", "Dimensions", "Mounting plate thickness 98")
params.MountingPlateThickness98 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness99", "Dimensions", "Mounting plate thickness 99")
params.MountingPlateThickness99 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness100", "Dimensions", "Mounting plate thickness 100")
params.MountingPlateThickness100 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness101", "Dimensions", "Mounting plate thickness 101")
params.MountingPlateThickness101 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness102", "Dimensions", "Mounting plate thickness 102")
params.MountingPlateThickness102 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness103", "Dimensions", "Mounting plate thickness 103")
params.MountingPlateThickness103 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness104", "Dimensions", "Mounting plate thickness 104")
params.MountingPlateThickness104 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness105", "Dimensions", "Mounting plate thickness 105")
params.MountingPlateThickness105 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness106", "Dimensions", "Mounting plate thickness 106")
params.MountingPlateThickness106 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness107", "Dimensions", "Mounting plate thickness 107")
params.MountingPlateThickness107 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness108", "Dimensions", "Mounting plate thickness 108")
params.MountingPlateThickness108 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness109", "Dimensions", "Mounting plate thickness 109")
params.MountingPlateThickness109 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness110", "Dimensions", "Mounting plate thickness 110")
params.MountingPlateThickness110 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness111", "Dimensions", "Mounting plate thickness 111")
params.MountingPlateThickness111 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness112", "Dimensions", "Mounting plate thickness 112")
params.MountingPlateThickness112 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness113", "Dimensions", "Mounting plate thickness 113")
params.MountingPlateThickness113 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness114", "Dimensions", "Mounting plate thickness 114")
params.MountingPlateThickness114 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness115", "Dimensions", "Mounting plate thickness 115")
params.MountingPlateThickness115 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness116", "Dimensions", "Mounting plate thickness 116")
params.MountingPlateThickness116 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness117", "Dimensions", "Mounting plate thickness 117")
params.MountingPlateThickness117 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness118", "Dimensions", "Mounting plate thickness 118")
params.MountingPlateThickness118 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness119", "Dimensions", "Mounting plate thickness 119")
params.MountingPlateThickness119 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness120", "Dimensions", "Mounting plate thickness 120")
params.MountingPlateThickness120 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness121", "Dimensions", "Mounting plate thickness 121")
params.MountingPlateThickness121 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness122", "Dimensions", "Mounting plate thickness 122")
params.MountingPlateThickness122 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness123", "Dimensions", "Mounting plate thickness 123")
params.MountingPlateThickness123 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness124", "Dimensions", "Mounting plate thickness 124")
params.MountingPlateThickness124 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness125", "Dimensions", "Mounting plate thickness 125")
params.MountingPlateThickness125 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness126", "Dimensions", "Mounting plate thickness 126")
params.MountingPlateThickness126 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness127", "Dimensions", "Mounting plate thickness 127")
params.MountingPlateThickness127 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness128", "Dimensions", "Mounting plate thickness 128")
params.MountingPlateThickness128 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness129", "Dimensions", "Mounting plate thickness 129")
params.MountingPlateThickness129 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness130", "Dimensions", "Mounting plate thickness 130")
params.MountingPlateThickness130 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness131", "Dimensions", "Mounting plate thickness 131")
params.MountingPlateThickness131 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness132", "Dimensions", "Mounting plate thickness 132")
params.MountingPlateThickness132 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness133", "Dimensions", "Mounting plate thickness 133")
params.MountingPlateThickness133 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness134", "Dimensions", "Mounting plate thickness 134")
params.MountingPlateThickness134 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness135", "Dimensions", "Mounting plate thickness 135")
params.MountingPlateThickness135 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness136", "Dimensions", "Mounting plate thickness 136")
params.MountingPlateThickness136 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness137", "Dimensions", "Mounting plate thickness 137")
params.MountingPlateThickness137 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness138", "Dimensions", "Mounting plate thickness 138")
params.MountingPlateThickness138 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness139", "Dimensions", "Mounting plate thickness 139")
params.MountingPlateThickness139 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness140", "Dimensions", "Mounting plate thickness 140")
params.MountingPlateThickness140 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness141", "Dimensions", "Mounting plate thickness 141")
params.MountingPlateThickness141 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness142", "Dimensions", "Mounting plate thickness 142")
params.MountingPlateThickness142 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness143", "Dimensions", "Mounting plate thickness 143")
params.MountingPlateThickness143 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness144", "Dimensions", "Mounting plate thickness 144")
params.MountingPlateThickness144 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness145", "Dimensions", "Mounting plate thickness 145")
params.MountingPlateThickness145 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness146", "Dimensions", "Mounting plate thickness 146")
params.MountingPlateThickness146 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness147", "Dimensions", "Mounting plate thickness 147")
params.MountingPlateThickness147 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness148", "Dimensions", "Mounting plate thickness 148")
params.MountingPlateThickness148 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness149", "Dimensions", "Mounting plate thickness 149")
params.MountingPlateThickness149 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness150", "Dimensions", "Mounting plate thickness 150")
params.MountingPlateThickness150 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness151", "Dimensions", "Mounting plate thickness 151")
params.MountingPlateThickness151 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness152", "Dimensions", "Mounting plate thickness 152")
params.MountingPlateThickness152 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness153", "Dimensions", "Mounting plate thickness 153")
params.MountingPlateThickness153 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness154", "Dimensions", "Mounting plate thickness 154")
params.MountingPlateThickness154 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness155", "Dimensions", "Mounting plate thickness 155")
params.MountingPlateThickness155 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness156", "Dimensions", "Mounting plate thickness 156")
params.MountingPlateThickness156 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness157", "Dimensions", "Mounting plate thickness 157")
params.MountingPlateThickness157 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness158", "Dimensions", "Mounting plate thickness 158")
params.MountingPlateThickness158 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness159", "Dimensions", "Mounting plate thickness 159")
params.MountingPlateThickness159 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness160", "Dimensions", "Mounting plate thickness 160")
params.MountingPlateThickness160 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness161", "Dimensions", "Mounting plate thickness 161")
params.MountingPlateThickness161 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness162", "Dimensions", "Mounting plate thickness 162")
params.MountingPlateThickness162 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness163", "Dimensions", "Mounting plate thickness 163")
params.MountingPlateThickness163 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness164", "Dimensions", "Mounting plate thickness 164")
params.MountingPlateThickness164 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness165", "Dimensions", "Mounting plate thickness 165")
params.MountingPlateThickness165 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness166", "Dimensions", "Mounting plate thickness 166")
params.MountingPlateThickness166 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness167", "Dimensions", "Mounting plate thickness 167")
params.MountingPlateThickness167 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness168", "Dimensions", "Mounting plate thickness 168")
params.MountingPlateThickness168 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness169", "Dimensions", "Mounting plate thickness 169")
params.MountingPlateThickness169 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness170", "Dimensions", "Mounting plate thickness 170")
params.MountingPlateThickness170 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness171", "Dimensions", "Mounting plate thickness 171")
params.MountingPlateThickness171 = 10.0

params.addProperty("App::PropertyLength", "MountingPlateThickness172", "Dimensions", "Mounting plate thickness 172")
params.MountingPlateThickness172 = 10.0

params.addProperty("App::PropertyLength", "Mount
