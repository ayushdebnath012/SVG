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
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing25", "Dimensions", "Spacing between twenty-fifth set of terminal bores")
    params.terminal_bore_spacing25 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset26", "Dimensions", "Offset of twenty-sixth set of terminal bores from edge")
    params.terminal_bore_offset26 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth26", "Dimensions", "Depth of twenty-sixth set of terminal bores")
    params.terminal_bore_depth26 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing26", "Dimensions", "Spacing between twenty-sixth set of terminal bores")
    params.terminal_bore_spacing26 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset27", "Dimensions", "Offset of twenty-seventh set of terminal bores from edge")
    params.terminal_bore_offset27 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth27", "Dimensions", "Depth of twenty-seventh set of terminal bores")
    params.terminal_bore_depth27 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing27", "Dimensions", "Spacing between twenty-seventh set of terminal bores")
    params.terminal_bore_spacing27 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset28", "Dimensions", "Offset of twenty-eighth set of terminal bores from edge")
    params.terminal_bore_offset28 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth28", "Dimensions", "Depth of twenty-eighth set of terminal bores")
    params.terminal_bore_depth28 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing28", "Dimensions", "Spacing between twenty-eighth set of terminal bores")
    params.terminal_bore_spacing28 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset29", "Dimensions", "Offset of twenty-ninth set of terminal bores from edge")
    params.terminal_bore_offset29 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth29", "Dimensions", "Depth of twenty-ninth set of terminal bores")
    params.terminal_bore_depth29 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing29", "Dimensions", "Spacing between twenty-ninth set of terminal bores")
    params.terminal_bore_spacing29 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset30", "Dimensions", "Offset of thirtieth set of terminal bores from edge")
    params.terminal_bore_offset30 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth30", "Dimensions", "Depth of thirtieth set of terminal bores")
    params.terminal_bore_depth30 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing30", "Dimensions", "Spacing between thirtieth set of terminal bores")
    params.terminal_bore_spacing30 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset31", "Dimensions", "Offset of thirty-first set of terminal bores from edge")
    params.terminal_bore_offset31 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth31", "Dimensions", "Depth of thirty-first set of terminal bores")
    params.terminal_bore_depth31 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing31", "Dimensions", "Spacing between thirty-first set of terminal bores")
    params.terminal_bore_spacing31 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset32", "Dimensions", "Offset of thirty-second set of terminal bores from edge")
    params.terminal_bore_offset32 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth32", "Dimensions", "Depth of thirty-second set of terminal bores")
    params.terminal_bore_depth32 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing32", "Dimensions", "Spacing between thirty-second set of terminal bores")
    params.terminal_bore_spacing32 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset33", "Dimensions", "Offset of thirty-third set of terminal bores from edge")
    params.terminal_bore_offset33 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth33", "Dimensions", "Depth of thirty-third set of terminal bores")
    params.terminal_bore_depth33 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing33", "Dimensions", "Spacing between thirty-third set of terminal bores")
    params.terminal_bore_spacing33 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset34", "Dimensions", "Offset of thirty-fourth set of terminal bores from edge")
    params.terminal_bore_offset34 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth34", "Dimensions", "Depth of thirty-fourth set of terminal bores")
    params.terminal_bore_depth34 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing34", "Dimensions", "Spacing between thirty-fourth set of terminal bores")
    params.terminal_bore_spacing34 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset35", "Dimensions", "Offset of thirty-fifth set of terminal bores from edge")
    params.terminal_bore_offset35 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth35", "Dimensions", "Depth of thirty-fifth set of terminal bores")
    params.terminal_bore_depth35 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing35", "Dimensions", "Spacing between thirty-fifth set of terminal bores")
    params.terminal_bore_spacing35 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset36", "Dimensions", "Offset of thirty-sixth set of terminal bores from edge")
    params.terminal_bore_offset36 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth36", "Dimensions", "Depth of thirty-sixth set of terminal bores")
    params.terminal_bore_depth36 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing36", "Dimensions", "Spacing between thirty-sixth set of terminal bores")
    params.terminal_bore_spacing36 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset37", "Dimensions", "Offset of thirty-seventh set of terminal bores from edge")
    params.terminal_bore_offset37 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth37", "Dimensions", "Depth of thirty-seventh set of terminal bores")
    params.terminal_bore_depth37 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing37", "Dimensions", "Spacing between thirty-seventh set of terminal bores")
    params.terminal_bore_spacing37 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset38", "Dimensions", "Offset of thirty-eighth set of terminal bores from edge")
    params.terminal_bore_offset38 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth38", "Dimensions", "Depth of thirty-eighth set of terminal bores")
    params.terminal_bore_depth38 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing38", "Dimensions", "Spacing between thirty-eighth set of terminal bores")
    params.terminal_bore_spacing38 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset39", "Dimensions", "Offset of thirty-ninth set of terminal bores from edge")
    params.terminal_bore_offset39 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth39", "Dimensions", "Depth of thirty-ninth set of terminal bores")
    params.terminal_bore_depth39 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing39", "Dimensions", "Spacing between thirty-ninth set of terminal bores")
    params.terminal_bore_spacing39 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset40", "Dimensions", "Offset of fortieth set of terminal bores from edge")
    params.terminal_bore_offset40 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth40", "Dimensions", "Depth of fortieth set of terminal bores")
    params.terminal_bore_depth40 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing40", "Dimensions", "Spacing between fortieth set of terminal bores")
    params.terminal_bore_spacing40 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset41", "Dimensions", "Offset of forty-first set of terminal bores from edge")
    params.terminal_bore_offset41 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth41", "Dimensions", "Depth of forty-first set of terminal bores")
    params.terminal_bore_depth41 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing41", "Dimensions", "Spacing between forty-first set of terminal bores")
    params.terminal_bore_spacing41 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset42", "Dimensions", "Offset of forty-second set of terminal bores from edge")
    params.terminal_bore_offset42 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth42", "Dimensions", "Depth of forty-second set of terminal bores")
    params.terminal_bore_depth42 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing42", "Dimensions", "Spacing between forty-second set of terminal bores")
    params.terminal_bore_spacing42 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset43", "Dimensions", "Offset of forty-third set of terminal bores from edge")
    params.terminal_bore_offset43 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth43", "Dimensions", "Depth of forty-third set of terminal bores")
    params.terminal_bore_depth43 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing43", "Dimensions", "Spacing between forty-third set of terminal bores")
    params.terminal_bore_spacing43 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset44", "Dimensions", "Offset of forty-fourth set of terminal bores from edge")
    params.terminal_bore_offset44 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth44", "Dimensions", "Depth of forty-fourth set of terminal bores")
    params.terminal_bore_depth44 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing44", "Dimensions", "Spacing between forty-fourth set of terminal bores")
    params.terminal_bore_spacing44 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset45", "Dimensions", "Offset of forty-fifth set of terminal bores from edge")
    params.terminal_bore_offset45 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth45", "Dimensions", "Depth of forty-fifth set of terminal bores")
    params.terminal_bore_depth45 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing45", "Dimensions", "Spacing between forty-fifth set of terminal bores")
    params.terminal_bore_spacing45 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset46", "Dimensions", "Offset of forty-sixth set of terminal bores from edge")
    params.terminal_bore_offset46 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth46", "Dimensions", "Depth of forty-sixth set of terminal bores")
    params.terminal_bore_depth46 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing46", "Dimensions", "Spacing between forty-sixth set of terminal bores")
    params.terminal_bore_spacing46 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset47", "Dimensions", "Offset of forty-seventh set of terminal bores from edge")
    params.terminal_bore_offset47 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth47", "Dimensions", "Depth of forty-seventh set of terminal bores")
    params.terminal_bore_depth47 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing47", "Dimensions", "Spacing between forty-seventh set of terminal bores")
    params.terminal_bore_spacing47 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset48", "Dimensions", "Offset of forty-eighth set of terminal bores from edge")
    params.terminal_bore_offset48 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth48", "Dimensions", "Depth of forty-eighth set of terminal bores")
    params.terminal_bore_depth48 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing48", "Dimensions", "Spacing between forty-eighth set of terminal bores")
    params.terminal_bore_spacing48 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset49", "Dimensions", "Offset of forty-ninth set of terminal bores from edge")
    params.terminal_bore_offset49 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth49", "Dimensions", "Depth of forty-ninth set of terminal bores")
    params.terminal_bore_depth49 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing49", "Dimensions", "Spacing between forty-ninth set of terminal bores")
    params.terminal_bore_spacing49 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset50", "Dimensions", "Offset of fiftieth set of terminal bores from edge")
    params.terminal_bore_offset50 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth50", "Dimensions", "Depth of fiftieth set of terminal bores")
    params.terminal_bore_depth50 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing50", "Dimensions", "Spacing between fiftieth set of terminal bores")
    params.terminal_bore_spacing50 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset51", "Dimensions", "Offset of fifty-first set of terminal bores from edge")
    params.terminal_bore_offset51 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth51", "Dimensions", "Depth of fifty-first set of terminal bores")
    params.terminal_bore_depth51 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing51", "Dimensions", "Spacing between fifty-first set of terminal bores")
    params.terminal_bore_spacing51 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset52", "Dimensions", "Offset of fifty-second set of terminal bores from edge")
    params.terminal_bore_offset52 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth52", "Dimensions", "Depth of fifty-second set of terminal bores")
    params.terminal_bore_depth52 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing52", "Dimensions", "Spacing between fifty-second set of terminal bores")
    params.terminal_bore_spacing52 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_offset53", "Dimensions", "Offset of fifty-third set of terminal bores from edge")
    params.terminal_bore_offset53 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_depth53", "Dimensions", "Depth of fifty-third set of terminal bores")
    params.terminal_bore_depth53 = 2.0
    
    params.addProperty("App::PropertyLength", "terminal_bore_spacing53", "Dimensions", "Spacing between fifty-third set of terminal bores")
    params.terminal_bore_spacing53 = 2.0
    
    params.addProperty("App::Property
