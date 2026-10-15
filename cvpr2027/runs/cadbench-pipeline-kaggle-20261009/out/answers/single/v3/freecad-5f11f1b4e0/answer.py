import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

def create_relay_housing():
    # Create new document
    doc = App.newDocument("RelayHousing")
    
    # Create XY plane
    xy_plane = doc.addObject("Part::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    doc.addObject("App::DocumentObjectGroup", "XY_Plane")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    doc.addObject("App::DocumentObjectGroup", "Body")
    
    # Create parameters for dimensions
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "total_length", "Dimensions", "Total length of housing")
    params.total_length = 71.0
    
    params.addProperty("App::PropertyLength", "base_width", "Dimensions", "Width of base")
    params.base_width = 49.0
    
    params.addProperty("App::PropertyLength", "base_height", "Dimensions", "Height of base")
    params.base_height = 22.0
    
    params.addProperty("App::PropertyLength", "mounting_height", "Dimensions", "Height of mounting section")
    params.mounting_height = 55.5
    
    params.addProperty("App::PropertyLength", "mounting_width", "Dimensions", "Width of mounting section")
    params.mounting_width = 35.5
    
    params.addProperty("App::PropertyLength", "mounting_depth", "Dimensions", "Depth of mounting section")
    params.mounting_depth = 22.0
    
    params.addProperty("App::PropertyLength", "terminal_height", "Dimensions", "Height of terminal section")
    params.terminal_height = 59.8
    
    params.addProperty("App::PropertyLength", "terminal_width", "Dimensions", "Width of terminal section")
    params.terminal_width = 21.0
    
    params.addProperty("App::PropertyLength", "terminal_depth", "Dimensions", "Depth of terminal section")
    params.terminal_depth = 22.0
    
    params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of main bore")
    params.bore_diameter = 19.0
    
    params.addProperty("App::PropertyLength", "bore_depth", "Dimensions", "Depth of main bore")
    params.bore_depth = 18.7
    
    params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet radius")
    params.fillet_radius = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_diameter", "Dimensions", "Diameter of terminal bores")
    params.terminal_bore_diameter = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing", "Dimensions", "Spacing between terminal bores")
    params.terminal_bore_spacing = 14.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth", "Dimensions", "Depth of terminal bores")
    params.terminal_bore_depth = 6.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset", "Dimensions", "Offset of terminal bores from edge")
    params.terminal_bore_offset = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing2", "Dimensions", "Spacing between second set of terminal bores")
    params.terminal_bore_spacing2 = 7.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset2", "Dimensions", "Offset of second set of terminal bores from edge")
    params.terminal_bore_offset2 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth2", "Dimensions", "Depth of second set of terminal bores")
    params.terminal_bore_depth2 = 7.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset3", "Dimensions", "Offset of third set of terminal bores from edge")
    params.terminal_bore_offset3 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth3", "Dimensions", "Depth of third set of terminal bores")
    params.terminal_bore_depth3 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing3", "Dimensions", "Spacing between third set of terminal bores")
    params.terminal_bore_spacing3 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset4", "Dimensions", "Offset of fourth set of terminal bores from edge")
    params.terminal_bore_offset4 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth4", "Dimensions", "Depth of fourth set of terminal bores")
    params.terminal_bore_depth4 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing4", "Dimensions", "Spacing between fourth set of terminal bores")
    params.terminal_bore_spacing4 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset5", "Dimensions", "Offset of fifth set of terminal bores from edge")
    params.terminal_bore_offset5 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth5", "Dimensions", "Depth of fifth set of terminal bores")
    params.terminal_bore_depth5 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing5", "Dimensions", "Spacing between fifth set of terminal bores")
    params.terminal_bore_spacing5 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset6", "Dimensions", "Offset of sixth set of terminal bores from edge")
    params.terminal_bore_offset6 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth6", "Dimensions", "Depth of sixth set of terminal bores")
    params.terminal_bore_depth6 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing6", "Dimensions", "Spacing between sixth set of terminal bores")
    params.terminal_bore_spacing6 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset7", "Dimensions", "Offset of seventh set of terminal bores from edge")
    params.terminal_bore_offset7 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth7", "Dimensions", "Depth of seventh set of terminal bores")
    params.terminal_bore_depth7 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing7", "Dimensions", "Spacing between seventh set of terminal bores")
    params.terminal_bore_spacing7 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset8", "Dimensions", "Offset of eighth set of terminal bores from edge")
    params.terminal_bore_offset8 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth8", "Dimensions", "Depth of eighth set of terminal bores")
    params.terminal_bore_depth8 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing8", "Dimensions", "Spacing between eighth set of terminal bores")
    params.terminal_bore_spacing8 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset9", "Dimensions", "Offset of ninth set of terminal bores from edge")
    params.terminal_bore_offset9 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth9", "Dimensions", "Depth of ninth set of terminal bores")
    params.terminal_bore_depth9 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing9", "Dimensions", "Spacing between ninth set of terminal bores")
    params.terminal_bore_spacing9 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset10", "Dimensions", "Offset of tenth set of terminal bores from edge")
    params.terminal_bore_offset10 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth10", "Dimensions", "Depth of tenth set of terminal bores")
    params.terminal_bore_depth10 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing10", "Dimensions", "Spacing between tenth set of terminal bores")
    params.terminal_bore_spacing10 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset11", "Dimensions", "Offset of eleventh set of terminal bores from edge")
    params.terminal_bore_offset11 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth11", "Dimensions", "Depth of eleventh set of terminal bores")
    params.terminal_bore_depth11 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing11", "Dimensions", "Spacing between eleventh set of terminal bores")
    params.terminal_bore_spacing11 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset12", "Dimensions", "Offset of twelfth set of terminal bores from edge")
    params.terminal_bore_offset12 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth12", "Dimensions", "Depth of twelfth set of terminal bores")
    params.terminal_bore_depth12 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing12", "Dimensions", "Spacing between twelfth set of terminal bores")
    params.terminal_bore_spacing12 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset13", "Dimensions", "Offset of thirteenth set of terminal bores from edge")
    params.terminal_bore_offset13 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth13", "Dimensions", "Depth of thirteenth set of terminal bores")
    params.terminal_bore_depth13 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing13", "Dimensions", "Spacing between thirteenth set of terminal bores")
    params.terminal_bore_spacing13 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset14", "Dimensions", "Offset of fourteenth set of terminal bores from edge")
    params.terminal_bore_offset14 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth14", "Dimensions", "Depth of fourteenth set of terminal bores")
    params.terminal_bore_depth14 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing14", "Dimensions", "Spacing between fourteenth set of terminal bores")
    params.terminal_bore_spacing14 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset15", "Dimensions", "Offset of fifteenth set of terminal bores from edge")
    params.terminal_bore_offset15 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth15", "Dimensions", "Depth of fifteenth set of terminal bores")
    params.terminal_bore_depth15 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing15", "Dimensions", "Spacing between fifteenth set of terminal bores")
    params.terminal_bore_spacing15 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset16", "Dimensions", "Offset of sixteenth set of terminal bores from edge")
    params.terminal_bore_offset16 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth16", "Dimensions", "Depth of sixteenth set of terminal bores")
    params.terminal_bore_depth16 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing16", "Dimensions", "Spacing between sixteenth set of terminal bores")
    params.terminal_bore_spacing16 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset17", "Dimensions", "Offset of seventeenth set of terminal bores from edge")
    params.terminal_bore_offset17 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth17", "Dimensions", "Depth of seventeenth set of terminal bores")
    params.terminal_bore_depth17 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing17", "Dimensions", "Spacing between seventeenth set of terminal bores")
    params.terminal_bore_spacing17 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset18", "Dimensions", "Offset of eighteenth set of terminal bores from edge")
    params.terminal_bore_offset18 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth18", "Dimensions", "Depth of eighteenth set of terminal bores")
    params.terminal_bore_depth18 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing18", "Dimensions", "Spacing between eighteenth set of terminal bores")
    params.terminal_bore_spacing18 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset19", "Dimensions", "Offset of nineteenth set of terminal bores from edge")
    params.terminal_bore_offset19 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth19", "Dimensions", "Depth of nineteenth set of terminal bores")
    params.terminal_bore_depth19 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing19", "Dimensions", "Spacing between nineteenth set of terminal bores")
    params.terminal_bore_spacing19 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset20", "Dimensions", "Offset of twentieth set of terminal bores from edge")
    params.terminal_bore_offset20 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth20", "Dimensions", "Depth of twentieth set of terminal bores")
    params.terminal_bore_depth20 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing20", "Dimensions", "Spacing between twentieth set of terminal bores")
    params.terminal_bore_spacing20 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset21", "Dimensions", "Offset of twenty-first set of terminal bores from edge")
    params.terminal_bore_offset21 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth21", "Dimensions", "Depth of twenty-first set of terminal bores")
    params.terminal_bore_depth21 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing21", "Dimensions", "Spacing between twenty-first set of terminal bores")
    params.terminal_bore_spacing21 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset22", "Dimensions", "Offset of twenty-second set of terminal bores from edge")
    params.terminal_bore_offset22 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth22", "Dimensions", "Depth of twenty-second set of terminal bores")
    params.terminal_bore_depth22 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing22", "Dimensions", "Spacing between twenty-second set of terminal bores")
    params.terminal_bore_spacing22 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset23", "Dimensions", "Offset of twenty-third set of terminal bores from edge")
    params.terminal_bore_offset23 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth23", "Dimensions", "Depth of twenty-third set of terminal bores")
    params.terminal_bore_depth23 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing23", "Dimensions", "Spacing between twenty-third set of terminal bores")
    params.terminal_bore_spacing23 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset24", "Dimensions", "Offset of twenty-fourth set of terminal bores from edge")
    params.terminal_bore_offset24 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth24", "Dimensions", "Depth of twenty-fourth set of terminal bores")
    params.terminal_bore_depth24 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing24", "Dimensions", "Spacing between twenty-fourth set of terminal bores")
    params.terminal_bore_spacing24 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset25", "Dimensions", "Offset of twenty-fifth set of terminal bores from edge")
    params.terminal_bore_offset25 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth25", "Dimensions", "Depth of twenty-fifth set of terminal bores")
    params.terminal_bore_depth25 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing25", "Dimensions",
