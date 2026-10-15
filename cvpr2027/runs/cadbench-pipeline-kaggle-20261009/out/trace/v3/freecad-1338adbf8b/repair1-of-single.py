import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("LCD_Module")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter set for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "module_width", "Dimensions", "Overall module width")
params.module_width = 80.0
params.addProperty("App::PropertyLength", "module_height", "Dimensions", "Overall module height")
params.module_height = 36.0
params.addProperty("App::PropertyLength", "pcb_height", "Dimensions", "PCB area height")
params.pcb_height = 32.0
params.addProperty("App::PropertyLength", "lcd_width", "Dimensions", "LCD area width")
params.lcd_width = 65.0
params.addProperty("App::PropertyLength", "lcd_height", "Dimensions", "LCD area height")
params.lcd_height = 28.5
params.addProperty("App::PropertyLength", "pin_spacing", "Dimensions", "Pin spacing")
params.pin_spacing = 2.54
params.addProperty("App::PropertyLength", "pin_length", "Dimensions", "Pin length")
params.pin_length = 10.0
params.addProperty("App::PropertyLength", "mounting_hole_dia", "Dimensions", "Mounting hole diameter")
params.mounting_hole_dia = 3.0
params.addProperty("App::PropertyLength", "mounting_hole_spacing", "Dimensions", "Mounting hole spacing")
params.mounting_hole_spacing = 71.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_dia", "Dimensions", "LCD mounting hole diameter")
params.lcd_mount_hole_dia = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_spacing", "Dimensions", "LCD mounting hole spacing")
params.lcd_mount_hole_spacing = 65.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_offset", "Dimensions", "LCD mounting hole offset from edge")
params.lcd_mount_hole_offset = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset", "Dimensions", "LCD mounting hole vertical offset")
params.lcd_mount_hole_vertical_offset = 14.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing", "Dimensions", "LCD mounting hole vertical spacing")
params.lcd_mount_hole_vertical_spacing = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset2", "Dimensions", "LCD mounting hole vertical offset 2")
params.lcd_mount_hole_vertical_offset2 = 8.5
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing2", "Dimensions", "LCD mounting hole vertical spacing 2")
params.lcd_mount_hole_vertical_spacing2 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset3", "Dimensions", "LCD mounting hole vertical offset 3")
params.lcd_mount_hole_vertical_offset3 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing3", "Dimensions", "LCD mounting hole vertical spacing 3")
params.lcd_mount_hole_vertical_spacing3 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset4", "Dimensions", "LCD mounting hole vertical offset 4")
params.lcd_mount_hole_vertical_offset4 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing4", "Dimensions", "LCD mounting hole vertical spacing 4")
params.lcd_mount_hole_vertical_spacing4 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset5", "Dimensions", "LCD mounting hole vertical offset 5")
params.lcd_mount_hole_vertical_offset5 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing5", "Dimensions", "LCD mounting hole vertical spacing 5")
params.lcd_mount_hole_vertical_spacing5 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset6", "Dimensions", "LCD mounting hole vertical offset 6")
params.lcd_mount_hole_vertical_offset6 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing6", "Dimensions", "LCD mounting hole vertical spacing 6")
params.lcd_mount_hole_vertical_spacing6 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset7", "Dimensions", "LCD mounting hole vertical offset 7")
params.lcd_mount_hole_vertical_offset7 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing7", "Dimensions", "LCD mounting hole vertical spacing 7")
params.lcd_mount_hole_vertical_spacing7 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset8", "Dimensions", "LCD mounting hole vertical offset 8")
params.lcd_mount_hole_vertical_offset8 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing8", "Dimensions", "LCD mounting hole vertical spacing 8")
params.lcd_mount_hole_vertical_spacing8 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset9", "Dimensions", "LCD mounting hole vertical offset 9")
params.lcd_mount_hole_vertical_offset9 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing9", "Dimensions", "LCD mounting hole vertical spacing 9")
params.lcd_mount_hole_vertical_spacing9 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset10", "Dimensions", "LCD mounting hole vertical offset 10")
params.lcd_mount_hole_vertical_offset10 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing10", "Dimensions", "LCD mounting hole vertical spacing 10")
params.lcd_mount_hole_vertical_spacing10 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset11", "Dimensions", "LCD mounting hole vertical offset 11")
params.lcd_mount_hole_vertical_offset11 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing11", "Dimensions", "LCD mounting hole vertical spacing 11")
params.lcd_mount_hole_vertical_spacing11 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset12", "Dimensions", "LCD mounting hole vertical offset 12")
params.lcd_mount_hole_vertical_offset12 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing12", "Dimensions", "LCD mounting hole vertical spacing 12")
params.lcd_mount_hole_vertical_spacing12 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset13", "Dimensions", "LCD mounting hole vertical offset 13")
params.lcd_mount_hole_vertical_offset13 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing13", "Dimensions", "LCD mounting hole vertical spacing 13")
params.lcd_mount_hole_vertical_spacing13 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset14", "Dimensions", "LCD mounting hole vertical offset 14")
params.lcd_mount_hole_vertical_offset14 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing14", "Dimensions", "LCD mounting hole vertical spacing 14")
params.lcd_mount_hole_vertical_spacing14 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset15", "Dimensions", "LCD mounting hole vertical offset 15")
params.lcd_mount_hole_vertical_offset15 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing15", "Dimensions", "LCD mounting hole vertical spacing 15")
params.lcd_mount_hole_vertical_spacing15 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset16", "Dimensions", "LCD mounting hole vertical offset 16")
params.lcd_mount_hole_vertical_offset16 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing16", "Dimensions", "LCD mounting hole vertical spacing 16")
params.lcd_mount_hole_vertical_spacing16 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset17", "Dimensions", "LCD mounting hole vertical offset 17")
params.lcd_mount_hole_vertical_offset17 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing17", "Dimensions", "LCD mounting hole vertical spacing 17")
params.lcd_mount_hole_vertical_spacing17 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset18", "Dimensions", "LCD mounting hole vertical offset 18")
params.lcd_mount_hole_vertical_offset18 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing18", "Dimensions", "LCD mounting hole vertical spacing 18")
params.lcd_mount_hole_vertical_spacing18 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset19", "Dimensions", "LCD mounting hole vertical offset 19")
params.lcd_mount_hole_vertical_offset19 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing19", "Dimensions", "LCD mounting hole vertical spacing 19")
params.lcd_mount_hole_vertical_spacing19 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset20", "Dimensions", "LCD mounting hole vertical offset 20")
params.lcd_mount_hole_vertical_offset20 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing20", "Dimensions", "LCD mounting hole vertical spacing 20")
params.lcd_mount_hole_vertical_spacing20 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset21", "Dimensions", "LCD mounting hole vertical offset 21")
params.lcd_mount_hole_vertical_offset21 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing21", "Dimensions", "LCD mounting hole vertical spacing 21")
params.lcd_mount_hole_vertical_spacing21 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset22", "Dimensions", "LCD mounting hole vertical offset 22")
params.lcd_mount_hole_vertical_offset22 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing22", "Dimensions", "LCD mounting hole vertical spacing 22")
params.lcd_mount_hole_vertical_spacing22 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset23", "Dimensions", "LCD mounting hole vertical offset 23")
params.lcd_mount_hole_vertical_offset23 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing23", "Dimensions", "LCD mounting hole vertical spacing 23")
params.lcd_mount_hole_vertical_spacing23 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset24", "Dimensions", "LCD mounting hole vertical offset 24")
params.lcd_mount_hole_vertical_offset24 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing24", "Dimensions", "LCD mounting hole vertical spacing 24")
params.lcd_mount_hole_vertical_spacing24 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset25", "Dimensions", "LCD mounting hole vertical offset 25")
params.lcd_mount_hole_vertical_offset25 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing25", "Dimensions", "LCD mounting hole vertical spacing 25")
params.lcd_mount_hole_vertical_spacing25 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset26", "Dimensions", "LCD mounting hole vertical offset 26")
params.lcd_mount_hole_vertical_offset26 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing26", "Dimensions", "LCD mounting hole vertical spacing 26")
params.lcd_mount_hole_vertical_spacing26 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset27", "Dimensions", "LCD mounting hole vertical offset 27")
params.lcd_mount_hole_vertical_offset27 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing27", "Dimensions", "LCD mounting hole vertical spacing 27")
params.lcd_mount_hole_vertical_spacing27 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset28", "Dimensions", "LCD mounting hole vertical offset 28")
params.lcd_mount_hole_vertical_offset28 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing28", "Dimensions", "LCD mounting hole vertical spacing 28")
params.lcd_mount_hole_vertical_spacing28 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset29", "Dimensions", "LCD mounting hole vertical offset 29")
params.lcd_mount_hole_vertical_offset29 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing29", "Dimensions", "LCD mounting hole vertical spacing 29")
params.lcd_mount_hole_vertical_spacing29 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset30", "Dimensions", "LCD mounting hole vertical offset 30")
params.lcd_mount_hole_vertical_offset30 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing30", "Dimensions", "LCD mounting hole vertical spacing 30")
params.lcd_mount_hole_vertical_spacing30 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset31", "Dimensions", "LCD mounting hole vertical offset 31")
params.lcd_mount_hole_vertical_offset31 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing31", "Dimensions", "LCD mounting hole vertical spacing 31")
params.lcd_mount_hole_vertical_spacing31 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset32", "Dimensions", "LCD mounting hole vertical offset 32")
params.lcd_mount_hole_vertical_offset32 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing32", "Dimensions", "LCD mounting hole vertical spacing 32")
params.lcd_mount_hole_vertical_spacing32 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset33", "Dimensions", "LCD mounting hole vertical offset 33")
params.lcd_mount_hole_vertical_offset33 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing33", "Dimensions", "LCD mounting hole vertical spacing 33")
params.lcd_mount_hole_vertical_spacing33 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset34", "Dimensions", "LCD mounting hole vertical offset 34")
params.lcd_mount_hole_vertical_offset34 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing34", "Dimensions", "LCD mounting hole vertical spacing 34")
params.lcd_mount_hole_vertical_spacing34 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset35", "Dimensions", "LCD mounting hole vertical offset 35")
params.lcd_mount_hole_vertical_offset35 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing35", "Dimensions", "LCD mounting hole vertical spacing 35")
params.lcd_mount_hole_vertical_spacing35 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset36", "Dimensions", "LCD mounting hole vertical offset 36")
params.lcd_mount_hole_vertical_offset36 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing36", "Dimensions", "LCD mounting hole vertical spacing 36")
params.lcd_mount_hole_vertical_spacing36 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset37", "Dimensions", "LCD mounting hole vertical offset 37")
params.lcd_mount_hole_vertical_offset37 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing37", "Dimensions", "LCD mounting hole vertical spacing 37")
params.lcd_mount_hole_vertical_spacing37 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset38", "Dimensions", "LCD mounting hole vertical offset 38")
params.lcd_mount_hole_vertical_offset38 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing38", "Dimensions", "LCD mounting hole vertical spacing 38")
params.lcd_mount_hole_vertical_spacing38 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset39", "Dimensions", "LCD mounting hole vertical offset 39")
params.lcd_mount_hole_vertical_offset39 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing39", "Dimensions", "LCD mounting hole vertical spacing 39")
params.lcd_mount_hole_vertical_spacing39 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset40", "Dimensions", "LCD mounting hole vertical offset 40")
params.lcd_mount_hole_vertical_offset40 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing40", "Dimensions", "LCD mounting hole vertical spacing 40")
params.lcd_mount_hole_vertical_spacing40 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset41", "Dimensions", "LCD mounting hole vertical offset 41")
params.lcd_mount_hole_vertical_offset41 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing41", "Dimensions", "LCD mounting hole vertical spacing 41")
params.lcd_mount_hole_vertical_spacing41 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset42", "Dimensions", "LCD mounting hole vertical offset 42")
params.lcd_mount_hole_vertical_offset42 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing42", "Dimensions", "LCD mounting hole vertical spacing 42")
params.lcd_mount_hole_vertical_spacing42 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset43", "Dimensions", "LCD mounting hole vertical offset 43")
params.lcd_mount_hole_vertical_offset43 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing43", "Dimensions", "LCD mounting hole vertical spacing 43")
params.lcd_mount_hole_vertical_spacing43 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset44", "Dimensions", "LCD mounting hole vertical offset 44")
params.lcd_mount_hole_vertical_offset44 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing44", "Dimensions", "LCD mounting hole vertical spacing 44")
params.lcd_mount_hole_vertical_spacing44 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset45", "Dimensions", "LCD mounting hole vertical offset 45")
params.lcd_mount_hole_vertical_offset45 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing45", "Dimensions", "LCD mounting hole vertical spacing 45")
params.lcd_mount_hole_vertical_spacing45 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset46", "Dimensions", "LCD mounting hole vertical offset 46")
params.lcd_mount_hole_vertical_offset46 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing46", "Dimensions", "LCD mounting hole vertical spacing 46")
params.lcd_mount_hole_vertical_spacing46 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset47", "Dimensions", "LCD mounting hole vertical offset 47")
params.lcd_mount_hole_vertical_offset47 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing47", "Dimensions", "LCD mounting hole vertical spacing 47")
params.lcd_mount_hole_vertical_spacing47 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset48", "Dimensions", "LCD mounting hole vertical offset 48")
params.lcd_mount_hole_vertical_offset48 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing48", "Dimensions", "LCD mounting hole vertical spacing 48")
params.lcd_mount_hole_vertical_spacing48 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset49", "Dimensions", "LCD mounting hole vertical offset 49")
params.lcd_mount_hole_vertical_offset49 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing49", "Dimensions", "LCD mounting hole vertical spacing 49")
params.lcd_mount_hole_vertical_spacing49 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset50", "Dimensions", "LCD mounting hole vertical offset 50")
params.lcd_mount_hole_vertical_offset50 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing50", "Dimensions", "LCD mounting hole vertical spacing 50")
params.lcd_mount_hole_vertical_spacing50 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset51", "Dimensions", "LCD mounting hole vertical offset 51")
params.lcd_mount_hole_vertical_offset51 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing51", "Dimensions", "LCD mounting hole vertical spacing 51")
params.lcd_mount_hole_vertical_spacing51 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset52", "Dimensions", "LCD mounting hole vertical offset 52")
params.lcd_mount_hole_vertical_offset52 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing52", "Dimensions", "LCD mounting hole vertical spacing 52")
params.lcd_mount_hole_vertical_spacing52 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset53", "Dimensions", "LCD mounting hole vertical offset 53")
params.lcd_mount_hole_vertical_offset53 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing53", "Dimensions", "LCD mounting hole vertical spacing 53")
params.lcd_mount_hole_vertical_spacing53 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset54", "Dimensions", "LCD mounting hole vertical offset 54")
params.lcd_mount_hole_vertical_offset54 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing54", "Dimensions", "LCD mounting hole vertical spacing 54")
params.lcd_mount_hole_vertical_spacing54 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset55", "Dimensions", "LCD mounting hole vertical offset 55")
params.lcd_mount_hole_vertical_offset55 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing55", "Dimensions", "LCD mounting hole vertical spacing 55")
params.lcd_mount_hole_vertical_spacing55 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset56", "Dimensions", "LCD mounting hole vertical offset 56")
params.lcd_mount_hole_vertical_offset56 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing56", "Dimensions", "LCD mounting hole vertical spacing 56")
params.lcd_mount_hole_vertical_spacing56 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset57", "Dimensions", "LCD mounting hole vertical offset 57")
params.lcd_mount_hole_vertical_offset57 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing57", "Dimensions", "LCD mounting hole vertical spacing 57")
params.lcd_mount_hole_vertical_spacing57 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset58", "Dimensions", "LCD mounting hole vertical offset 58")
params.lcd_mount_hole_vertical_offset58 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing58", "Dimensions", "LCD mounting hole vertical spacing 58")
params.lcd_mount_hole_vertical_spacing58 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset59", "Dimensions", "LCD mounting hole vertical offset 59")
params.lcd_mount_hole_vertical_offset59 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing59", "Dimensions", "LCD mounting hole vertical spacing 59")
params.lcd_mount_hole_vertical_spacing59 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset60", "Dimensions", "LCD mounting hole vertical offset 60")
params.lcd_mount_hole_vertical_offset60 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing60", "Dimensions", "LCD mounting hole vertical spacing 60")
params.lcd_mount_hole_vertical_spacing60 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset61", "Dimensions", "LCD mounting hole vertical offset 61")
params.lcd_mount_hole_vertical_offset61 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing61", "Dimensions", "LCD mounting hole vertical spacing 61")
params.lcd_mount_hole_vertical_spacing61 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset62", "Dimensions", "LCD mounting hole vertical offset 62")
params.lcd_mount_hole_vertical_offset62 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing62", "Dimensions", "LCD mounting hole vertical spacing 62")
params.lcd_mount_hole_vertical_spacing62 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset63", "Dimensions", "LCD mounting hole vertical offset 63")
params.lcd_mount_hole_vertical_offset63 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing63", "Dimensions", "LCD mounting hole vertical spacing 63")
params.lcd_mount_hole_vertical_spacing63 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset64", "Dimensions", "LCD mounting hole vertical offset 64")
params.lcd_mount_hole_vertical_offset64 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing64", "Dimensions", "LCD mounting hole vertical spacing 64")
params.lcd_mount_hole_vertical_spacing64 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset65", "Dimensions", "LCD mounting hole vertical offset 65")
params.lcd_mount_hole_vertical_offset65 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing65", "Dimensions", "LCD mounting hole vertical spacing 65")
params.lcd_mount_hole_vertical_spacing65 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset66", "Dimensions", "LCD mounting hole vertical offset 66")
params.lcd_mount_hole_vertical_offset66 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing66", "Dimensions", "LCD mounting hole vertical spacing 66")
params.lcd_mount_hole_vertical_spacing66 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset67", "Dimensions", "LCD mounting hole vertical offset 67")
params.lcd_mount_hole_vertical_offset67 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing67", "Dimensions", "LCD mounting hole vertical spacing 67")
params.lcd_mount_hole_vertical_spacing67 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset68", "Dimensions", "LCD mounting hole vertical offset 68")
params.lcd_mount_hole_vertical_offset68 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing68", "Dimensions", "LCD mounting hole vertical spacing 68")
params.lcd_mount_hole_vertical_spacing68 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset69", "Dimensions", "LCD mounting hole vertical offset 69")
params.lcd_mount_hole_vertical_offset69 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing69", "Dimensions", "LCD mounting hole vertical spacing 69")
params.lcd_mount_hole_vertical_spacing69 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset70", "Dimensions", "LCD mounting hole vertical offset 70")
params.lcd_mount_hole_vertical_offset70 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing70", "Dimensions", "LCD mounting hole vertical spacing 70")
params.lcd_mount_hole_vertical_spacing70 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset71", "Dimensions", "LCD mounting hole vertical offset 71")
params.lcd_mount_hole_vertical_offset71 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing71", "Dimensions", "LCD mounting hole vertical spacing 71")
params.lcd_mount_hole_vertical_spacing71 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset72", "Dimensions", "LCD mounting hole vertical offset 72")
params.lcd_mount_hole_vertical_offset72 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing72", "Dimensions", "LCD mounting hole vertical spacing 72")
params.lcd_mount_hole_vertical_spacing72 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset73", "Dimensions", "LCD mounting hole vertical offset 73")
params.lcd_mount_hole_vertical_offset73 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing73", "Dimensions", "LCD mounting hole vertical spacing 73")
params.lcd_mount_hole_vertical_spacing73 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset74", "Dimensions", "LCD mounting hole vertical offset 74")
params.lcd_mount_hole_vertical_offset74 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing74", "Dimensions", "LCD mounting hole vertical spacing 74")
params.lcd_mount_hole_vertical_spacing74 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset75", "Dimensions", "LCD mounting hole vertical offset 75")
params.lcd_mount_hole_vertical_offset75 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing75", "Dimensions", "LCD mounting hole vertical spacing 75")
params.lcd_mount_hole_vertical_spacing75 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset76", "Dimensions", "LCD mounting hole vertical offset 76")
params.lcd_mount_hole_vertical_offset76 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing76", "Dimensions", "LCD mounting hole vertical spacing 76")
params.lcd_mount_hole_vertical_spacing76 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset77", "Dimensions", "LCD mounting hole vertical offset 77")
params.lcd_mount_hole_vertical_offset77 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing77", "Dimensions", "LCD mounting hole vertical spacing 77")
params.lcd_mount_hole_vertical_spacing77 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset78", "Dimensions", "LCD mounting hole vertical offset 78")
params.lcd_mount_hole_vertical_offset78 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing78", "Dimensions", "LCD mounting hole vertical spacing 78")
params.lcd_mount_hole_vertical_spacing78 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset79", "Dimensions", "LCD mounting hole vertical offset 79")
params.lcd_mount_hole_vertical_offset79 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing79", "Dimensions", "LCD mounting hole vertical spacing 79")
params.lcd_mount_hole_vertical_spacing79 = 12.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_offset80", "Dimensions", "LCD mounting hole vertical offset 80")
params.lcd_mount_hole_vertical_offset80 = 2.0
params.addProperty("App::PropertyLength", "lcd_mount_hole_vertical_spacing80", "Dimensions", "LCD mounting hole vertical spacing 80")
params.lcd_mount_hole_vertical_spacing80 = 12.
