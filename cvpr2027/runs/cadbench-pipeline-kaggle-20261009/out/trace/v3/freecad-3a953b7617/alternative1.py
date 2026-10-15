from pathlib import Path
import FreeCAD as App, Part, Sketcher, PartDesign

# Initialize Document
doc = App.newDocument("SlottedMountingFrame")

# Add Base Plane
basePlane = doc.addObject("PartDesign::Plane", "XY_Plane")
doc.recompute()

# Add Parameters (Named Variables)
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "OuterWidth", "Dimensions", "155.72")
params.OuterWidth = 155.72
params.addProperty("App::PropertyLength", "InnerWidth", "Dimensions", "140.0")
params.InnerWidth = 140.0
params.addProperty("App::PropertyLength", "LeftStubLength", "Dimensions", "61.51")
params.LeftStubLength = 61.51
params.addProperty("App::PropertyLength", "RightStubLength", "Dimensions", "70.19")
params.RightStubLength = 70.19
params.addProperty("App::PropertyLength", "StubWidth", "Dimensions", "50.12")
params.StubWidth = 50.12
params.addProperty("App::PropertyLength", "StubThickness", "Dimensions", "16.0")
params.StubThickness = 16.0
params.addProperty("App::PropertyLength", "FrameThickness", "Dimensions", "3.5")
params.FrameThickness = 3.5
params.addProperty("App::PropertyLength", "MainBodyThickness", "Dimensions", "4.0")
params.MainBodyThickness = 4.0
params.addProperty("App::PropertyLength", "MainBodyInnerWidth", "Dimensions", "125.5")
params.MainBodyInnerWidth = 125.5
params.addProperty("App::PropertyLength", "MainBodyHeight", "Dimensions", "35.0")
params.MainBodyHeight = 35.0
params.addProperty("App::PropertyLength", "StubInnerHeight", "Dimensions", "37.5")
params.StubInnerHeight = 37.5
params.addProperty("App::PropertyLength", "StubInnerWidth", "Dimensions", "44.0")
params.StubInnerWidth = 44.0
params.addProperty("App::PropertyLength", "CornerRadius", "Dimensions", "2.5")
params.CornerRadius = 2.5
params.addProperty("App::PropertyLength", "SlotWidth", "Dimensions", "4.0")
params.SlotWidth = 4.0
params.addProperty("App::PropertyLength", "SlotLength", "Dimensions", "18.0")
params.SlotLength = 18.0
params.addProperty("App::PropertyLength", "SlotSpacing", "Dimensions", "3.0")
params.SlotSpacing = 3.0
params.addProperty("App::PropertyLength", "CornerChamfer", "Dimensions", "1.5")
params.CornerChamfer = 1.5
params.addProperty("App::PropertyLength", "SlotDepth", "Dimensions", "1.5")
params.SlotDepth = 1.5
params.addProperty("App::PropertyLength", "StubSlotDepth", "Dimensions", "1.5")
params.StubSlotDepth = 1.5
params.addProperty("App::PropertyLength", "StubSlotWidth", "Dimensions", "6.0")
params.StubSlotWidth = 6.0
params.addProperty("App::PropertyLength", "StubSlotSpacing", "Dimensions", "3.0")
params.StubSlotSpacing = 3.0
params.addProperty("App::PropertyLength", "StubCutoutWidth", "Dimensions", "35.0")
params.StubCutoutWidth = 35.0
params.addProperty("App::PropertyLength", "StubCutoutThickness", "Dimensions", "3.5")
params.StubCutoutThickness = 3.5
params.addProperty("App::PropertyLength", "StubCutoutDepth", "Dimensions", "1.5")
params.StubCutoutDepth = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius", "Dimensions", "2.5")
params.StubCutoutRadius = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth2", "Dimensions", "1.5")
params.StubCutoutDepth2 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius2", "Dimensions", "2.5")
params.StubCutoutRadius2 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth3", "Dimensions", "1.5")
params.StubCutoutDepth3 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius3", "Dimensions", "2.5")
params.StubCutoutRadius3 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth4", "Dimensions", "1.5")
params.StubCutoutDepth4 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius4", "Dimensions", "2.5")
params.StubCutoutRadius4 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth5", "Dimensions", "1.5")
params.StubCutoutDepth5 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius5", "Dimensions", "2.5")
params.StubCutoutRadius5 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth6", "Dimensions", "1.5")
params.StubCutoutDepth6 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius6", "Dimensions", "2.5")
params.StubCutoutRadius6 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth7", "Dimensions", "1.5")
params.StubCutoutDepth7 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius7", "Dimensions", "2.5")
params.StubCutoutRadius7 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth8", "Dimensions", "1.5")
params.StubCutoutDepth8 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius8", "Dimensions", "2.5")
params.StubCutoutRadius8 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth9", "Dimensions", "1.5")
params.StubCutoutDepth9 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius9", "Dimensions", "2.5")
params.StubCutoutRadius9 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth10", "Dimensions", "1.5")
params.StubCutoutDepth10 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius10", "Dimensions", "2.5")
params.StubCutoutRadius10 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth11", "Dimensions", "1.5")
params.StubCutoutDepth11 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius11", "Dimensions", "2.5")
params.StubCutoutRadius11 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth12", "Dimensions", "1.5")
params.StubCutoutDepth12 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius12", "Dimensions", "2.5")
params.StubCutoutRadius12 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth13", "Dimensions", "1.5")
params.StubCutoutDepth13 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius13", "Dimensions", "2.5")
params.StubCutoutRadius13 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth14", "Dimensions", "1.5")
params.StubCutoutDepth14 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius14", "Dimensions", "2.5")
params.StubCutoutRadius14 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth15", "Dimensions", "1.5")
params.StubCutoutDepth15 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius15", "Dimensions", "2.5")
params.StubCutoutRadius15 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth16", "Dimensions", "1.5")
params.StubCutoutDepth16 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius16", "Dimensions", "2.5")
params.StubCutoutRadius16 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth17", "Dimensions", "1.5")
params.StubCutoutDepth17 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius17", "Dimensions", "2.5")
params.StubCutoutRadius17 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth18", "Dimensions", "1.5")
params.StubCutoutDepth18 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius18", "Dimensions", "2.5")
params.StubCutoutRadius18 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth19", "Dimensions", "1.5")
params.StubCutoutDepth19 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius19", "Dimensions", "2.5")
params.StubCutoutRadius19 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth20", "Dimensions", "1.5")
params.StubCutoutDepth20 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius20", "Dimensions", "2.5")
params.StubCutoutRadius20 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth21", "Dimensions", "1.5")
params.StubCutoutDepth21 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius21", "Dimensions", "2.5")
params.StubCutoutRadius21 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth22", "Dimensions", "1.5")
params.StubCutoutDepth22 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius22", "Dimensions", "2.5")
params.StubCutoutRadius22 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth23", "Dimensions", "1.5")
params.StubCutoutDepth23 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius23", "Dimensions", "2.5")
params.StubCutoutRadius23 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth24", "Dimensions", "1.5")
params.StubCutoutDepth24 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius24", "Dimensions", "2.5")
params.StubCutoutRadius24 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth25", "Dimensions", "1.5")
params.StubCutoutDepth25 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius25", "Dimensions", "2.5")
params.StubCutoutRadius25 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth26", "Dimensions", "1.5")
params.StubCutoutDepth26 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius26", "Dimensions", "2.5")
params.StubCutoutRadius26 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth27", "Dimensions", "1.5")
params.StubCutoutDepth27 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius27", "Dimensions", "2.5")
params.StubCutoutRadius27 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth28", "Dimensions", "1.5")
params.StubCutoutDepth28 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius28", "Dimensions", "2.5")
params.StubCutoutRadius28 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth29", "Dimensions", "1.5")
params.StubCutoutDepth29 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius29", "Dimensions", "2.5")
params.StubCutoutRadius29 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth30", "Dimensions", "1.5")
params.StubCutoutDepth30 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius30", "Dimensions", "2.5")
params.StubCutoutRadius30 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth31", "Dimensions", "1.5")
params.StubCutoutDepth31 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius31", "Dimensions", "2.5")
params.StubCutoutRadius31 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth32", "Dimensions", "1.5")
params.StubCutoutDepth32 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius32", "Dimensions", "2.5")
params.StubCutoutRadius32 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth33", "Dimensions", "1.5")
params.StubCutoutDepth33 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius33", "Dimensions", "2.5")
params.StubCutoutRadius33 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth34", "Dimensions", "1.5")
params.StubCutoutDepth34 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius34", "Dimensions", "2.5")
params.StubCutoutRadius34 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth35", "Dimensions", "1.5")
params.StubCutoutDepth35 = 1.5
params.addProperty("App::PropertyLength", "StubCutoutRadius35", "Dimensions", "2.5")
params.StubCutoutRadius35 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth36", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius36", "Dimensions", "2.5")
params.StubCutoutRadius36 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth37", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius37", "Dimensions", "2.5")
params.StubCutoutRadius37 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth38", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius38", "Dimensions", "2.5")
params.StubCutoutRadius38 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth39", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius39", "Dimensions", "2.5")
params.StubCutoutRadius39 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth40", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius40", "Dimensions", "2.5")
params.StubCutoutRadius40 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth41", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius41", "Dimensions", "2.5")
params.StubCutoutRadius41 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth42", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius42", "Dimensions", "2.5")
params.StubCutoutRadius42 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth43", "Dimensions", "1.5")
params.addProperty("App::PropertyLength", "StubCutoutRadius43", "Dimensions", "2.5")
params.StubCutoutRadius43 = 2.5
params.addProperty("App::PropertyLength", "StubCutoutDepth44", "Dimensions", "1.5")
params.addProperty("
