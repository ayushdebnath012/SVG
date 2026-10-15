from pathlib import Path
import FreeCAD as App, Part, Sketcher, PartDesign

# Create document
doc = App.newDocument("TriangulatedClevisMountBracket")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create named parameters for key dimensions
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "MainHeight", "Dimensions", "Main vertical height")
params.MainHeight = 85.74
params.addProperty("App::PropertyLength", "TopWidth", "Dimensions", "Top horizontal width")
params.TopWidth = 17.05
params.addProperty("App::PropertyLength", "BottomWidth", "Dimensions", "Bottom horizontal width")
params.BottomWidth = 12.0
params.addProperty("App::PropertyLength", "MainThickness", "Dimensions", "Main vertical thickness")
params.MainThickness = 4.0
params.addProperty("App::PropertyLength", "TopThickness", "Dimensions", "Top horizontal thickness")
params.TopThickness = 3.61
params.addProperty("App::PropertyLength", "BottomThickness", "Dimensions", "Bottom horizontal thickness")
params.BottomThickness = 3.0
params.addProperty("App::PropertyLength", "MainDepth", "Dimensions", "Main depth")
params.MainDepth = 72.56
params.addProperty("App::PropertyLength", "TopDepth", "Dimensions", "Top depth")
params.TopDepth = 80.61
params.addProperty("App::PropertyLength", "BottomDepth", "Dimensions", "Bottom depth")
params.BottomDepth = 83.61
params.addProperty("App::PropertyLength", "MainRadius", "Dimensions", "Main fillet radius")
params.MainRadius = 10.0
params.addProperty("App::PropertyLength", "TopRadius", "Dimensions", "Top fillet radius")
params.TopRadius = 3.0
params.addProperty("App::PropertyLength", "BottomRadius", "Dimensions", "Bottom fillet radius")
params.BottomRadius = 3.0
params.addProperty("App::PropertyLength", "MainHoleDiameter", "Dimensions", "Main hole diameter")
params.MainHoleDiameter = 4.0
params.addProperty("App::PropertyLength", "TopHoleDiameter", "Dimensions", "Top hole diameter")
params.TopHoleDiameter = 2.0
params.addProperty("App::PropertyLength", "BottomHoleDiameter", "Dimensions", "Bottom hole diameter")
params.BottomHoleDiameter = 2.0
params.addProperty("App::PropertyLength", "MainHoleOffset", "Dimensions", "Main hole offset from top")
params.MainHoleOffset = 14.07
params.addProperty("App::PropertyLength", "TopHoleOffset", "Dimensions", "Top hole offset from top")
params.TopHoleOffset = 14.07
params.addProperty("App::PropertyLength", "BottomHoleOffset", "Dimensions", "Bottom hole offset from top")
params.BottomHoleOffset = 14.07
params.addProperty("App::PropertyLength", "MainHoleSpacing", "Dimensions", "Main hole spacing")
params.MainHoleSpacing = 12.0
params.addProperty("App::PropertyLength", "TopHoleSpacing", "Dimensions", "Top hole spacing")
params.TopHoleSpacing = 12.0
params.addProperty("App::PropertyLength", "BottomHoleSpacing", "Dimensions", "Bottom hole spacing")
params.BottomHoleSpacing = 12.0
params.addProperty("App::PropertyLength", "MainHoleCount", "Dimensions", "Main hole count")
params.MainHoleCount = 3
params.addProperty("App::PropertyLength", "TopHoleCount", "Dimensions", "Top hole count")
params.TopHoleCount = 3
params.addProperty("App::PropertyLength", "BottomHoleCount", "Dimensions", "Bottom hole count")
params.BottomHoleCount = 3
params.addProperty("App::PropertyLength", "MainHolePosition", "Dimensions", "Main hole position")
params.MainHolePosition = 14.07
params.addProperty("App::PropertyLength", "TopHolePosition", "Dimensions", "Top hole position")
params.TopHolePosition = 14.07
params.addProperty("App::PropertyLength", "BottomHolePosition", "Dimensions", "Bottom hole position")
params.BottomHolePosition = 14.07
params.addProperty("App::PropertyLength", "MainHoleAngle", "Dimensions", "Main hole angle")
params.MainHoleAngle = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngle", "Dimensions", "Top hole angle")
params.TopHoleAngle = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngle", "Dimensions", "Bottom hole angle")
params.BottomHoleAngle = 45.0
params.addProperty("App::PropertyLength", "MainHoleRadius", "Dimensions", "Main hole radius")
params.MainHoleRadius = 2.0
params.addProperty("App::PropertyLength", "TopHoleRadius", "Dimensions", "Top hole radius")
params.TopHoleRadius = 1.0
params.addProperty("App::PropertyLength", "BottomHoleRadius", "Dimensions", "Bottom hole radius")
params.BottomHoleRadius = 1.0
params.addProperty("App::PropertyLength", "MainHoleDepth", "Dimensions", "Main hole depth")
params.MainHoleDepth = 4.0
params.addProperty("App::PropertyLength", "TopHoleDepth", "Dimensions", "Top hole depth")
params.TopHoleDepth = 4.0
params.addProperty("App::PropertyLength", "BottomHoleDepth", "Dimensions", "Bottom hole depth")
params.BottomHoleDepth = 4.0
params.addProperty("App::PropertyLength", "MainHoleLength", "Dimensions", "Main hole length")
params.MainHoleLength = 4.0
params.addProperty("App::PropertyLength", "TopHoleLength", "Dimensions", "Top hole length")
params.TopHoleLength = 4.0
params.addProperty("App::PropertyLength", "BottomHoleLength", "Dimensions", "Bottom hole length")
params.BottomHoleLength = 4.0
params.addProperty("App::PropertyLength", "MainHoleWidth", "Dimensions", "Main hole width")
params.MainHoleWidth = 4.0
params.addProperty("App::PropertyLength", "TopHoleWidth", "Dimensions", "Top hole width")
params.TopHoleWidth = 4.0
params.addProperty("App::PropertyLength", "BottomHoleWidth", "Dimensions", "Bottom hole width")
params.BottomHoleWidth = 4.0
params.addProperty("App::PropertyLength", "MainHoleHeight", "Dimensions", "Main hole height")
params.MainHoleHeight = 4.0
params.addProperty("App::PropertyLength", "TopHoleHeight", "Dimensions", "Top hole height")
params.TopHoleHeight = 4.0
params.addProperty("App::PropertyLength", "BottomHoleHeight", "Dimensions", "Bottom hole height")
params.BottomHoleHeight = 4.0
params.addProperty("App::PropertyLength", "MainHoleX", "Dimensions", "Main hole X")
params.MainHoleX = 14.07
params.addProperty("App::PropertyLength", "TopHoleX", "Dimensions", "Top hole X")
params.TopHoleX = 14.07
params.addProperty("App::PropertyLength", "BottomHoleX", "Dimensions", "Bottom hole X")
params.BottomHoleX = 14.07
params.addProperty("App::PropertyLength", "MainHoleY", "Dimensions", "Main hole Y")
params.MainHoleY = 14.07
params.addProperty("App::PropertyLength", "TopHoleY", "Dimensions", "Top hole Y")
params.TopHoleY = 14.07
params.addProperty("App::PropertyLength", "BottomHoleY", "Dimensions", "Bottom hole Y")
params.BottomHoleY = 14.07
params.addProperty("App::PropertyLength", "MainHoleZ", "Dimensions", "Main hole Z")
params.MainHoleZ = 14.07
params.addProperty("App::PropertyLength", "TopHoleZ", "Dimensions", "Top hole Z")
params.TopHoleZ = 14.07
params.addProperty("App::PropertyLength", "BottomHoleZ", "Dimensions", "Bottom hole Z")
params.BottomHoleZ = 14.07
params.addProperty("App::PropertyLength", "MainHoleAngleX", "Dimensions", "Main hole angle X")
params.MainHoleAngleX = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleX", "Dimensions", "Top hole angle X")
params.TopHoleAngleX = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleX", "Dimensions", "Bottom hole angle X")
params.BottomHoleAngleX = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleY", "Dimensions", "Main hole angle Y")
params.MainHoleAngleY = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleY", "Dimensions", "Top hole angle Y")
params.TopHoleAngleY = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleY", "Dimensions", "Bottom hole angle Y")
params.BottomHoleAngleY = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleZ", "Dimensions", "Main hole angle Z")
params.MainHoleAngleZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleZ", "Dimensions", "Top hole angle Z")
params.TopHoleAngleZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleZ", "Dimensions", "Bottom hole angle Z")
params.BottomHoleAngleZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXY", "Dimensions", "Main hole angle XY")
params.MainHoleAngleXY = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXY", "Dimensions", "Top hole angle XY")
params.TopHoleAngleXY = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXY", "Dimensions", "Bottom hole angle XY")
params.BottomHoleAngleXY = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXZ", "Dimensions", "Main hole angle XZ")
params.MainHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXZ", "Dimensions", "Top hole angle XZ")
params.TopHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXZ", "Dimensions", "Bottom hole angle XZ")
params.BottomHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleYZ", "Dimensions", "Main hole angle YZ")
params.MainHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleYZ", "Dimensions", "Top hole angle YZ")
params.TopHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleYZ", "Dimensions", "Bottom hole angle YZ")
params.BottomHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXYZ", "Dimensions", "Main hole angle XYZ")
params.MainHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXYZ", "Dimensions", "Top hole angle XYZ")
params.TopHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXYZ", "Dimensions", "Bottom hole angle XYZ")
params.BottomHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXZ", "Dimensions", "Main hole angle XZ")
params.MainHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXZ", "Dimensions", "Top hole angle XZ")
params.TopHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXZ", "Dimensions", "Bottom hole angle XZ")
params.BottomHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleYZ", "Dimensions", "Main hole angle YZ")
params.MainHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleYZ", "Dimensions", "Top hole angle YZ")
params.TopHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleYZ", "Dimensions", "Bottom hole angle YZ")
params.BottomHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXYZ", "Dimensions", "Main hole angle XYZ")
params.MainHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXYZ", "Dimensions", "Top hole angle XYZ")
params.TopHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXYZ", "Dimensions", "Bottom hole angle XYZ")
params.BottomHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXZ", "Dimensions", "Main hole angle XZ")
params.MainHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXZ", "Dimensions", "Top hole angle XZ")
params.TopHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXZ", "Dimensions", "Bottom hole angle XZ")
params.BottomHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleYZ", "Dimensions", "Main hole angle YZ")
params.MainHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleYZ", "Dimensions", "Top hole angle YZ")
params.TopHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleYZ", "Dimensions", "Bottom hole angle YZ")
params.BottomHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXYZ", "Dimensions", "Main hole angle XYZ")
params.MainHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXYZ", "Dimensions", "Top hole angle XYZ")
params.TopHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXYZ", "Dimensions", "Bottom hole angle XYZ")
params.BottomHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXZ", "Dimensions", "Main hole angle XZ")
params.MainHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXZ", "Dimensions", "Top hole angle XZ")
params.TopHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXZ", "Dimensions", "Bottom hole angle XZ")
params.BottomHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleYZ", "Dimensions", "Main hole angle YZ")
params.MainHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleYZ", "Dimensions", "Top hole angle YZ")
params.TopHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleYZ", "Dimensions", "Bottom hole angle YZ")
params.BottomHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXYZ", "Dimensions", "Main hole angle XYZ")
params.MainHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXYZ", "Dimensions", "Top hole angle XYZ")
params.TopHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXYZ", "Dimensions", "Bottom hole angle XYZ")
params.BottomHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXZ", "Dimensions", "Main hole angle XZ")
params.MainHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXZ", "Dimensions", "Top hole angle XZ")
params.TopHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleXZ", "Dimensions", "Bottom hole angle XZ")
params.BottomHoleAngleXZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleYZ", "Dimensions", "Main hole angle YZ")
params.MainHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleYZ", "Dimensions", "Top hole angle YZ")
params.TopHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "BottomHoleAngleYZ", "Dimensions", "Bottom hole angle YZ")
params.BottomHoleAngleYZ = 45.0
params.addProperty("App::PropertyLength", "MainHoleAngleXYZ", "Dimensions", "Main hole angle XYZ")
params.MainHoleAngleXYZ = 45.0
params.addProperty("App::PropertyLength", "TopHoleAngleXYZ", "Dimensions", "Top hole
