import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create new document
doc = App.newDocument("SlottedChannelGuideBracket")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create named parameters for dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "total_length", "Dimensions", "Total length of the bracket")
params.total_length = 155.0

params.addProperty("App::PropertyLength", "main_height", "Dimensions", "Main body height")
params.main_height = 35.0

params.addProperty("App::PropertyLength", "web_height", "Dimensions", "Web height")
params.web_height = 10.0

params.addProperty("App::PropertyLength", "flange_height", "Dimensions", "Flange height")
params.flange_height = 25.0

params.addProperty("App::PropertyLength", "slot_width", "Dimensions", "Slot width")
params.slot_width = 12.0

params.addProperty("App::PropertyLength", "slot_depth", "Dimensions", "Slot depth")
params.slot_depth = 15.0

params.addProperty("App::PropertyLength", "slot_spacing", "Dimensions", "Slot spacing")
params.slot_spacing = 37.5

params.addProperty("App::PropertyLength", "flange_width", "Dimensions", "Flange width")
params.flange_width = 95.0

params.addProperty("App::PropertyLength", "flange_depth", "Dimensions", "Flange depth")
params.flange_depth = 18.0

params.addProperty("App::PropertyLength", "flange_spacing", "Dimensions", "Flange spacing")
params.flange_spacing = 18.0

params.addProperty("App::PropertyLength", "flange_depth2", "Dimensions", "Second flange depth")
params.flange_depth2 = 11.0

params.addProperty("App::PropertyLength", "flange_spacing2", "Dimensions", "Second flange spacing")
params.flange_spacing2 = 30.0

params.addProperty("App::PropertyLength", "corner_radius", "Dimensions", "Corner radius")
params.corner_radius = 3.0

params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet radius")
params.fillet_radius = 2.5

params.addProperty("App::PropertyLength", "web_radius", "Dimensions", "Web radius")
params.web_radius = 1.0

params.addProperty("App::PropertyLength", "web_depth", "Dimensions", "Web depth")
params.web_depth = 13.5

params.addProperty("App::PropertyLength", "web_depth2", "Dimensions", "Second web depth")
params.web_depth2 = 13.5

params.addProperty("App::PropertyLength", "web_depth3", "Dimensions", "Third web depth")
params.web_depth3 = 13.5

params.addProperty("App::PropertyLength", "web_depth4", "Dimensions", "Fourth web depth")
params.web_depth4 = 13.5

params.addProperty("App::PropertyLength", "web_depth5", "Dimensions", "Fifth web depth")
params.web_depth5 = 13.5

params.addProperty("App::PropertyLength", "web_depth6", "Dimensions", "Sixth web depth")
params.web_depth6 = 13.5

params.addProperty("App::PropertyLength", "web_depth7", "Dimensions", "Seventh web depth")
params.web_depth7 = 13.5

params.addProperty("App::PropertyLength", "web_depth8", "Dimensions", "Eighth web depth")
params.web_depth8 = 13.5

params.addProperty("App::PropertyLength", "web_depth9", "Dimensions", "Ninth web depth")
params.web_depth9 = 13.5

params.addProperty("App::PropertyLength", "web_depth10", "Dimensions", "Tenth web depth")
params.web_depth10 = 13.5

params.addProperty("App::PropertyLength", "web_depth11", "Dimensions", "Eleventh web depth")
params.web_depth11 = 13.5

params.addProperty("App::PropertyLength", "web_depth12", "Dimensions", "Twelfth web depth")
params.web_depth12 = 13.5

params.addProperty("App::PropertyLength", "web_depth13", "Dimensions", "Thirteenth web depth")
params.web_depth13 = 13.5

params.addProperty("App::PropertyLength", "web_depth14", "Dimensions", "Fourteenth web depth")
params.web_depth14 = 13.5

params.addProperty("App::PropertyLength", "web_depth15", "Dimensions", "Fifteenth web depth")
params.web_depth15 = 13.5

params.addProperty("App::PropertyLength", "web_depth16", "Dimensions", "Sixteenth web depth")
params.web_depth16 = 13.5

params.addProperty("App::PropertyLength", "web_depth17", "Dimensions", "Seventeenth web depth")
params.web_depth17 = 13.5

params.addProperty("App::PropertyLength", "web_depth18", "Dimensions", "Eighteenth web depth")
params.web_depth18 = 13.5

params.addProperty("App::PropertyLength", "web_depth19", "Dimensions", "Nineteenth web depth")
params.web_depth19 = 13.5

params.addProperty("App::PropertyLength", "web_depth20", "Dimensions", "Twentieth web depth")
params.web_depth20 = 13.5

params.addProperty("App::PropertyLength", "web_depth21", "Dimensions", "Twenty-first web depth")
params.web_depth21 = 13.5

params.addProperty("App::PropertyLength", "web_depth22", "Dimensions", "Twenty-second web depth")
params.web_depth22 = 13.5

params.addProperty("App::PropertyLength", "web_depth23", "Dimensions", "Twenty-third web depth")
params.web_depth23 = 13.5

params.addProperty("App::PropertyLength", "web_depth24", "Dimensions", "Twenty-fourth web depth")
params.web_depth24 = 13.5

params.addProperty("App::PropertyLength", "web_depth25", "Dimensions", "Twenty-fifth web depth")
params.web_depth25 = 13.5

params.addProperty("App::PropertyLength", "web_depth26", "Dimensions", "Twenty-sixth web depth")
params.web_depth26 = 13.5

params.addProperty("App::PropertyLength", "web_depth27", "Dimensions", "Twenty-seventh web depth")
params.web_depth27 = 13.5

params.addProperty("App::PropertyLength", "web_depth28", "Dimensions", "Twenty-eighth web depth")
params.web_depth28 = 13.5

params.addProperty("App::PropertyLength", "web_depth29", "Dimensions", "Twenty-ninth web depth")
params.web_depth29 = 13.5

params.addProperty("App::PropertyLength", "web_depth30", "Dimensions", "Thirtieth web depth")
params.web_depth30 = 13.5

params.addProperty("App::PropertyLength", "web_depth31", "Dimensions", "Thirty-first web depth")
params.web_depth31 = 13.5

params.addProperty("App::PropertyLength", "web_depth32", "Dimensions", "Thirty-second web depth")
params.web_depth32 = 13.5

params.addProperty("App::PropertyLength", "web_depth33", "Dimensions", "Thirty-third web depth")
params.web_depth33 = 13.5

params.addProperty("App::PropertyLength", "web_depth34", "Dimensions", "Thirty-fourth web depth")
params.web_depth34 = 13.5

params.addProperty("App::PropertyLength", "web_depth35", "Dimensions", "Thirty-fifth web depth")
params.web_depth35 = 13.5

params.addProperty("App::PropertyLength", "web_depth36", "Dimensions", "Thirty-sixth web depth")
params.web_depth36 = 13.5

params.addProperty("App::PropertyLength", "web_depth37", "Dimensions", "Thirty-seventh web depth")
params.web_depth37 = 13.5

params.addProperty("App::PropertyLength", "web_depth38", "Dimensions", "Thirty-eighth web depth")
params.web_depth38 = 13.5

params.addProperty("App::PropertyLength", "web_depth39", "Dimensions", "Thirty-ninth web depth")
params.web_depth39 = 13.5

params.addProperty("App::PropertyLength", "web_depth40", "Dimensions", "Fortieth web depth")
params.web_depth40 = 13.5

params.addProperty("App::PropertyLength", "web_depth41", "Dimensions", "Forty-first web depth")
params.web_depth41 = 13.5

params.addProperty("App::PropertyLength", "web_depth42", "Dimensions", "Forty-second web depth")
params.web_depth42 = 13.5

params.addProperty("App::PropertyLength", "web_depth43", "Dimensions", "Forty-third web depth")
params.web_depth43 = 13.5

params.addProperty("App::PropertyLength", "web_depth44", "Dimensions", "Forty-fourth web depth")
params.web_depth44 = 13.5

params.addProperty("App::PropertyLength", "web_depth45", "Dimensions", "Forty-fifth web depth")
params.web_depth45 = 13.5

params.addProperty("App::PropertyLength", "web_depth46", "Dimensions", "Forty-sixth web depth")
params.web_depth46 = 13.5

params.addProperty("App::PropertyLength", "web_depth47", "Dimensions", "Forty-seventh web depth")
params.web_depth47 = 13.5

params.addProperty("App::PropertyLength", "web_depth48", "Dimensions", "Forty-eighth web depth")
params.web_depth48 = 13.5

params.addProperty("App::PropertyLength", "web_depth49", "Dimensions", "Forty-ninth web depth")
params.web_depth49 = 13.5

params.addProperty("App::PropertyLength", "web_depth50", "Dimensions", "Fiftieth web depth")
params.web_depth50 = 13.5

params.addProperty("App::PropertyLength", "web_depth51", "Dimensions", "Fifty-first web depth")
params.web_depth51 = 13.5

params.addProperty("App::PropertyLength", "web_depth52", "Dimensions", "Fifty-second web depth")
params.web_depth52 = 13.5

params.addProperty("App::PropertyLength", "web_depth53", "Dimensions", "Fifty-third web depth")
params.web_depth53 = 13.5

params.addProperty("App::PropertyLength", "web_depth54", "Dimensions", "Fifty-fourth web depth")
params.web_depth54 = 13.5

params.addProperty("App::PropertyLength", "web_depth55", "Dimensions", "Fifty-fifth web depth")
params.web_depth55 = 13.5

params.addProperty("App::PropertyLength", "web_depth56", "Dimensions", "Fifty-sixth web depth")
params.web_depth56 = 13.5

params.addProperty("App::PropertyLength", "web_depth57", "Dimensions", "Fifty-seventh web depth")
params.web_depth57 = 13.5

params.addProperty("App::PropertyLength", "web_depth58", "Dimensions", "Fifty-eighth web depth")
params.web_depth58 = 13.5

params.addProperty("App::PropertyLength", "web_depth59", "Dimensions", "Fifty-ninth web depth")
params.web_depth59 = 13.5

params.addProperty("App::PropertyLength", "web_depth60", "Dimensions", "Sixtieth web depth")
params.web_depth60 = 13.5

params.addProperty("App::PropertyLength", "web_depth61", "Dimensions", "Sixty-first web depth")
params.web_depth61 = 13.5

params.addProperty("App::PropertyLength", "web_depth62", "Dimensions", "Sixty-second web depth")
params.web_depth62 = 13.5

params.addProperty("App::PropertyLength", "web_depth63", "Dimensions", "Sixty-third web depth")
params.web_depth63 = 13.5

params.addProperty("App::PropertyLength", "web_depth64", "Dimensions", "Sixty-fourth web depth")
params.web_depth64 = 13.5

params.addProperty("App::PropertyLength", "web_depth65", "Dimensions", "Sixty-fifth web depth")
params.web_depth65 = 13.5

params.addProperty("App::PropertyLength", "web_depth66", "Dimensions", "Sixty-sixth web depth")
params.web_depth66 = 13.5

params.addProperty("App::PropertyLength", "web_depth67", "Dimensions", "Sixty-seventh web depth")
params.web_depth67 = 13.5

params.addProperty("App::PropertyLength", "web_depth68", "Dimensions", "Sixty-eighth web depth")
params.web_depth68 = 13.5

params.addProperty("App::PropertyLength", "web_depth69", "Dimensions", "Sixty-ninth web depth")
params.web_depth69 = 13.5

params.addProperty("App::PropertyLength", "web_depth70", "Dimensions", "Seventieth web depth")
params.web_depth70 = 13.5

params.addProperty("App::PropertyLength", "web_depth71", "Dimensions", "Seventy-first web depth")
params.web_depth71 = 13.5

params.addProperty("App::PropertyLength", "web_depth72", "Dimensions", "Seventy-second web depth")
params.web_depth72 = 13.5

params.addProperty("App::PropertyLength", "web_depth73", "Dimensions", "Seventy-third web depth")
params.web_depth73 = 13.5

params.addProperty("App::PropertyLength", "web_depth74", "Dimensions", "Seventy-fourth web depth")
params.web_depth74 = 13.5

params.addProperty("App::PropertyLength", "web_depth75", "Dimensions", "Seventy-fifth web depth")
params.web_depth75 = 13.5

params.addProperty("App::PropertyLength", "web_depth76", "Dimensions", "Seventy-sixth web depth")
params.web_depth76 = 13.5

params.addProperty("App::PropertyLength", "web_depth77", "Dimensions", "Seventy-seventh web depth")
params.web_depth77 = 13.5

params.addProperty("App::PropertyLength", "web_depth78", "Dimensions", "Seventy-eighth web depth")
params.web_depth78 = 13.5

params.addProperty("App::PropertyLength", "web_depth79", "Dimensions", "Seventy-ninth web depth")
params.web_depth79 = 13.5

params.addProperty("App::PropertyLength", "web_depth80", "Dimensions", "Eightieth web depth")
params.web_depth80 = 13.5

params.addProperty("App::PropertyLength", "web_depth81", "Dimensions", "Eighty-first web depth")
params.web_depth81 = 13.5

params.addProperty("App::PropertyLength", "web_depth82", "Dimensions", "Eighty-second web depth")
params.web_depth82 = 13.5

params.addProperty("App::PropertyLength", "web_depth83", "Dimensions", "Eighty-third web depth")
params.web_depth83 = 13.5

params.addProperty("App::PropertyLength", "web_depth84", "Dimensions", "Eighty-fourth web depth")
params.web_depth84 = 13.5

params.addProperty("App::PropertyLength", "web_depth85", "Dimensions", "Eighty-fifth web depth")
params.web_depth85 = 13.5

params.addProperty("App::PropertyLength", "web_depth86", "Dimensions", "Eighty-sixth web depth")
params.web_depth86 = 13.5

params.addProperty("App::PropertyLength", "web_depth87", "Dimensions", "Eighty-seventh web depth")
params.web_depth87 = 13.5

params.addProperty("App::PropertyLength", "web_depth88", "Dimensions", "Eighty-eighth web depth")
params.web_depth88 = 13.5

params.addProperty("App::PropertyLength", "web_depth89", "Dimensions", "Eighty-ninth web depth")
params.web_depth89 = 13.5

params.addProperty("App::PropertyLength", "web_depth90", "Dimensions", "Ninetieth web depth")
params.web_depth90 = 13.5

params.addProperty("App::PropertyLength", "web_depth91", "Dimensions", "Ninety-first web depth")
params.web_depth91 = 13.5

params.addProperty("App::PropertyLength", "web_depth92", "Dimensions", "Ninety-second web depth")
params.web_depth92 = 13.5

params.addProperty("App::PropertyLength", "web_depth93", "Dimensions", "Ninety-third web depth")
params.web_depth93 = 13.5

params.addProperty("App::PropertyLength", "web_depth94", "Dimensions", "Ninety-fourth web depth")
params.web_depth94 = 13.5

params.addProperty("App::PropertyLength", "web_depth95", "Dimensions", "Ninety-fifth web depth")
params.web_depth95 = 13.5

params.addProperty("App::PropertyLength", "web_depth96", "Dimensions", "Nin
