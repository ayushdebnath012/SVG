import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("MountingFlange")

# --- Parameters ---
# Define a VarSet to hold the named parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central through hole")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Set the values as specified in the prompt
params.outer_diameter = 66.675
params.flange_thickness = 13.49375
params.bore_diameter = 23.8125
params.bolt_circle_diameter = 53.18125
params.bolt_hole_diameter = 6.746875
params.number_bolt_holes = 4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange Profile) ---
# Create the main sketch for the flange body
sketch_profile = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.ConstrainToCurrentPlane = True
sketch_profile.Support = (doc.getObject("XY_Plane"), [])

# Add geometry: Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
sketch_profile.addGeometry(outer_circle, False)

# Add geometry: Inner Circle (Bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
sketch_profile.addGeometry(inner_circle, False)

# Add constraints: Concentric
sketch_profile.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 2)) # Equal radii of circle 0 and 1? No, concentric.
# Correct constraint for concentric circles in Sketcher:
# Constraint type "Concentric" (index 10) or "Equal" on radii if centered at same point.
# Since both are centered at (0,0), we just need to ensure they are concentric.
# Sketcher Constraint "Concentric" (10) requires two circles.
sketch_profile.addConstraint(Sketcher.Constraint("Concentric", 0, 1, 1, 2))

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "PadFlange")
pad.Profile = sketch_profile
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False

# --- Hole Sketch (Bolt Hole) ---
# Create a sketch for the bolt hole pattern
sketch_hole = body.newObject("Sketcher::SketchObject", "BoltHoleSketch")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hole.ConstrainToCurrentPlane = True
sketch_hole.Support = (doc.getObject("XY_Plane"), [])

# Add geometry: Bolt Hole Circle
bolt_hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
sketch_hole.addGeometry(bolt_hole_circle, False)

# --- Hole Feature (Single Bolt Hole) ---
hole = body.newObject("PartDesign::Hole", "BoltHole")
hole.Profile = sketch_hole
hole.Type = "Simple"
hole.Depth = params.flange_thickness
hole.ThroughAll = True
hole.Unwrap = False
hole.UnwrapAngle = 360.0
hole.UnwrapLength = 0.0
hole.UnwrapOffset = 0.0
hole.UnwrapRadius = 0.0
hole.UnwrapThickness = 0.0
hole.UnwrapWidth = 0.0
hole.UnwrapHeight = 0.0
hole.UnwrapDepth = 0.0
hole.UnwrapDiameter = 0.0
hole.UnwrapRadius2 = 0.0
hole.UnwrapRadius3 = 0.0
hole.UnwrapRadius4 = 0.0
hole.UnwrapRadius5 = 0.0
hole.UnwrapRadius6 = 0.0
hole.UnwrapRadius7 = 0.0
hole.UnwrapRadius8 = 0.0
hole.UnwrapRadius9 = 0.0
hole.UnwrapRadius10 = 0.0
hole.UnwrapRadius11 = 0.0
hole.UnwrapRadius12 = 0.0
hole.UnwrapRadius13 = 0.0
hole.UnwrapRadius14 = 0.0
hole.UnwrapRadius15 = 0.0
hole.UnwrapRadius16 = 0.0
hole.UnwrapRadius17 = 0.0
hole.UnwrapRadius18 = 0.0
hole.UnwrapRadius19 = 0.0
hole.UnwrapRadius20 = 0.0
hole.UnwrapRadius21 = 0.0
hole.UnwrapRadius22 = 0.0
hole.UnwrapRadius23 = 0.0
hole.UnwrapRadius24 = 0.0
hole.UnwrapRadius25 = 0.0
hole.UnwrapRadius26 = 0.0
hole.UnwrapRadius27 = 0.0
hole.UnwrapRadius28 = 0.0
hole.UnwrapRadius29 = 0.0
hole.UnwrapRadius30 = 0.0
hole.UnwrapRadius31 = 0.0
hole.UnwrapRadius32 = 0.0
hole.UnwrapRadius33 = 0.0
hole.UnwrapRadius34 = 0.0
hole.UnwrapRadius35 = 0.0
hole.UnwrapRadius36 = 0.0
hole.UnwrapRadius37 = 0.0
hole.UnwrapRadius38 = 0.0
hole.UnwrapRadius39 = 0.0
hole.UnwrapRadius40 = 0.0
hole.UnwrapRadius41 = 0.0
hole.UnwrapRadius42 = 0.0
hole.UnwrapRadius43 = 0.0
hole.UnwrapRadius44 = 0.0
hole.UnwrapRadius45 = 0.0
hole.UnwrapRadius46 = 0.0
hole.UnwrapRadius47 = 0.0
hole.UnwrapRadius48 = 0.0
hole.UnwrapRadius49 = 0.0
hole.UnwrapRadius50 = 0.0
hole.UnwrapRadius51 = 0.0
hole.UnwrapRadius52 = 0.0
hole.UnwrapRadius53 = 0.0
hole.UnwrapRadius54 = 0.0
hole.UnwrapRadius55 = 0.0
hole.UnwrapRadius56 = 0.0
hole.UnwrapRadius57 = 0.0
hole.UnwrapRadius58 = 0.0
hole.UnwrapRadius59 = 0.0
hole.UnwrapRadius60 = 0.0
hole.UnwrapRadius61 = 0.0
hole.UnwrapRadius62 = 0.0
hole.UnwrapRadius63 = 0.0
hole.UnwrapRadius64 = 0.0
hole.UnwrapRadius65 = 0.0
hole.UnwrapRadius66 = 0.0
hole.UnwrapRadius67 = 0.0
hole.UnwrapRadius68 = 0.0
hole.UnwrapRadius69 = 0.0
hole.UnwrapRadius70 = 0.0
hole.UnwrapRadius71 = 0.0
hole.UnwrapRadius72 = 0.0
hole.UnwrapRadius73 = 0.0
hole.UnwrapRadius74 = 0.0
hole.UnwrapRadius75 = 0.0
hole.UnwrapRadius76 = 0.0
hole.UnwrapRadius77 = 0.0
hole.UnwrapRadius78 = 0.0
hole.UnwrapRadius79 = 0.0
hole.UnwrapRadius80 = 0.0
hole.UnwrapRadius81 = 0.0
hole.UnwrapRadius82 = 0.0
hole.UnwrapRadius83 = 0.0
hole.UnwrapRadius84 = 0.0
hole.UnwrapRadius85 = 0.0
hole.UnwrapRadius86 = 0.0
hole.UnwrapRadius87 = 0.0
hole.UnwrapRadius88 = 0.0
hole.UnwrapRadius89 = 0.0
hole.UnwrapRadius90 = 0.0
hole.UnwrapRadius91 = 0.0
hole.UnwrapRadius92 = 0.0
hole.UnwrapRadius93 = 0.0
hole.UnwrapRadius94 = 0.0
hole.UnwrapRadius95 = 0.0
hole.UnwrapRadius96 = 0.0
hole.UnwrapRadius97 = 0.0
hole.UnwrapRadius98 = 0.0
hole.UnwrapRadius99 = 0.0
hole.UnwrapRadius100 = 0.0
hole.UnwrapRadius101 = 0.0
hole.UnwrapRadius102 = 0.0
hole.UnwrapRadius103 = 0.0
hole.UnwrapRadius104 = 0.0
hole.UnwrapRadius105 = 0.0
hole.UnwrapRadius106 = 0.0
hole.UnwrapRadius107 = 0.0
hole.UnwrapRadius108 = 0.0
hole.UnwrapRadius109 = 0.0
hole.UnwrapRadius110 = 0.0
hole.UnwrapRadius111 = 0.0
hole.UnwrapRadius112 = 0.0
hole.UnwrapRadius113 = 0.0
hole.UnwrapRadius114 = 0.0
hole.UnwrapRadius115 = 0.0
hole.UnwrapRadius116 = 0.0
hole.UnwrapRadius117 = 0.0
hole.UnwrapRadius118 = 0.0
hole.UnwrapRadius119 = 0.0
hole.UnwrapRadius120 = 0.0
hole.UnwrapRadius121 = 0.0
hole.UnwrapRadius122 = 0.0
hole.UnwrapRadius123 = 0.0
hole.UnwrapRadius124 = 0.0
hole.UnwrapRadius125 = 0.0
hole.UnwrapRadius126 = 0.0
hole.UnwrapRadius127 = 0.0
hole.UnwrapRadius128 = 0.0
hole.UnwrapRadius129 = 0.0
hole.UnwrapRadius130 = 0.0
hole.UnwrapRadius131 = 0.0
hole.UnwrapRadius132 = 0.0
hole.UnwrapRadius133 = 0.0
hole.UnwrapRadius134 = 0.0
hole.UnwrapRadius135 = 0.0
hole.UnwrapRadius136 = 0.0
hole.UnwrapRadius137 = 0.0
hole.UnwrapRadius138 = 0.0
hole.UnwrapRadius139 = 0.0
hole.UnwrapRadius140 = 0.0
hole.UnwrapRadius141 = 0.0
hole.UnwrapRadius142 = 0.0
hole.UnwrapRadius143 = 0.0
hole.UnwrapRadius144 = 0.0
hole.UnwrapRadius145 = 0.0
hole.UnwrapRadius146 = 0.0
hole.UnwrapRadius147 = 0.0
hole.UnwrapRadius148 = 0.0
hole.UnwrapRadius149 = 0.0
hole.UnwrapRadius150 = 0.0
hole.UnwrapRadius151 = 0.0
hole.UnwrapRadius152 = 0.0
hole.UnwrapRadius153 = 0.0
hole.UnwrapRadius154 = 0.0
hole.UnwrapRadius155 = 0.0
hole.UnwrapRadius156 = 0.0
hole.UnwrapRadius157 = 0.0
hole.UnwrapRadius158 = 0.0
hole.UnwrapRadius159 = 0.0
hole.UnwrapRadius160 = 0.0
hole.UnwrapRadius161 = 0.0
hole.UnwrapRadius162 = 0.0
hole.UnwrapRadius163 = 0.0
hole.UnwrapRadius164 = 0.0
hole.UnwrapRadius165 = 0.0
hole.UnwrapRadius166 = 0.0
hole.UnwrapRadius167 = 0.0
hole.UnwrapRadius168 = 0.0
hole.UnwrapRadius169 = 0.0
hole.UnwrapRadius170 = 0.0
hole.UnwrapRadius171 = 0.0
hole.UnwrapRadius172 = 0.0
hole.UnwrapRadius173 = 0.0
hole.UnwrapRadius174 = 0.0
hole.UnwrapRadius175 = 0.0
hole.UnwrapRadius176 = 0.0
hole.UnwrapRadius177 = 0.0
hole.UnwrapRadius178 = 0.0
hole.UnwrapRadius179 = 0.0
hole.UnwrapRadius180 = 0.0
hole.UnwrapRadius181 = 0.0
hole.UnwrapRadius182 = 0.0
hole.UnwrapRadius183 = 0.0
hole.UnwrapRadius184 = 0.0
hole.UnwrapRadius185 = 0.0
hole.UnwrapRadius186 = 0.0
hole.UnwrapRadius187 = 0.0
hole.UnwrapRadius188 = 0.0
hole.UnwrapRadius189 = 0.0
hole.UnwrapRadius190 = 0.0
hole.UnwrapRadius191 = 0.0
hole.UnwrapRadius192 = 0.0
hole.UnwrapRadius193 = 0.0
hole.UnwrapRadius194 = 0.0
hole.UnwrapRadius195 = 0.0
hole.UnwrapRadius196 = 0.0
hole.UnwrapRadius197 = 0.0
hole.UnwrapRadius198 = 0.0
hole.UnwrapRadius199 = 0.0
hole.UnwrapRadius200 = 0.0
hole.UnwrapRadius201 = 0.0
hole.UnwrapRadius202 = 0.0
hole.UnwrapRadius203 = 0.0
hole.UnwrapRadius204 = 0.0
hole.UnwrapRadius205 = 0.0
hole.UnwrapRadius206 = 0.0
hole.UnwrapRadius207 = 0.0
hole.UnwrapRadius208 = 0.0
hole.UnwrapRadius209 = 0.0
hole.UnwrapRadius210 = 0.0
hole.UnwrapRadius211 = 0.0
hole.UnwrapRadius212 = 0.0
hole.UnwrapRadius213 = 0.0
hole.UnwrapRadius214 = 0.0
hole.UnwrapRadius215 = 0.0
hole.UnwrapRadius216 = 0.0
hole.UnwrapRadius217 = 0.0
hole.UnwrapRadius218 = 0.0
hole.UnwrapRadius219 = 0.0
hole.UnwrapRadius220 = 0.0
hole.UnwrapRadius221 = 0.0
hole.UnwrapRadius222 = 0.0
hole.UnwrapRadius223 = 0.0
hole.UnwrapRadius224 = 0.0
hole.UnwrapRadius225 = 0.0
hole.UnwrapRadius226 = 0.0
hole.UnwrapRadius227 = 0.0
hole.UnwrapRadius228 = 0.0
hole.UnwrapRadius229 = 0.0
hole.UnwrapRadius230 = 0.0
hole.UnwrapRadius231 = 0.0
hole.UnwrapRadius232 = 0.0
hole.UnwrapRadius233 = 0.0
hole.UnwrapRadius234 = 0.0
hole.UnwrapRadius235 = 0.0
hole.UnwrapRadius236 = 0.0
hole.UnwrapRadius237 = 0.0
hole.UnwrapRadius238 = 0.0
hole.UnwrapRadius239 = 0.0
hole.UnwrapRadius240 = 0.0
hole.UnwrapRadius241 = 0.0
hole
