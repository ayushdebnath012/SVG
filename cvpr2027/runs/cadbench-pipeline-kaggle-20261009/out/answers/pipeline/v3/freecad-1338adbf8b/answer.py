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
params.addProperty("App::PropertyLength", "lcd_width", "Dimensions", "LCD area width")
params.lcd_width = 65.0
params.addProperty("App::PropertyLength", "lcd_height", "Dimensions", "LCD area height")
params.lcd_height = 28.5
params.addProperty("App::PropertyLength", "pcb_height", "Dimensions", "PCB area height")
params.pcb_height = 32.0
params.addProperty("App::PropertyLength", "pin_spacing", "Dimensions", "Pin spacing")
params.pin_spacing = 2.54
params.addProperty("App::PropertyLength", "pin_count", "Dimensions", "Number of pins")
params.pin_count = 16
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
params.lcd_mount_hole_vertical_offset38 =
