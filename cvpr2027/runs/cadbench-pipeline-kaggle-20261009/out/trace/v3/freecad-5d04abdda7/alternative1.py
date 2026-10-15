# FreeCAD 1.1.0 - Lathe Tailstock Body Generator
# Based on engineering drawing: 5d04abdda7.png
# Output: answer.FCStd

from pathlib import Path
import FreeCAD as App
import Part
import PartDesign
import Sketcher
import math

def main():
    # --- Initialization ---
    doc = App.newDocument("LatheTailstock")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.makeFlatFace(False)
    
    # --- Parameters ---
    params = body.newObject("App::Property", "Parameters")
    params.addProperty("App::PropertyLength", "BaseDia", "Dimensions", "Base Diameter")
    params.addProperty("App::PropertyLength", "ShaftLen", "Dimensions", "Shaft Length")
    params.addProperty("App::PropertyLength", "ShaftDia", "Dimensions", "Shaft Diameter")
    params.addProperty("App::PropertyLength", "TaperDia", "Dimensions", "Taper Diameter")
    params.addProperty("App::PropertyLength", "TaperLen", "Dimensions", "Taper Length")
    params.addProperty("App::PropertyLength", "ConeDia", "Dimensions", "Cone Diameter")
    params.addProperty("App::PropertyLength", "ConeLen", "Dimensions", "Cone Length")
    params.addProperty("App::PropertyLength", "SlotWidth", "Dimensions", "Slot Width")
    params.addProperty("App::PropertyLength", "SlotDepth", "Dimensions", "Slot Depth")
    params.addProperty("App::PropertyLength", "SlotLen", "Dimensions", "Slot Length")
    params.addProperty("App::PropertyLength", "SlotOffset", "Dimensions", "Slot Offset")
    params.addProperty("App::PropertyLength", "FilletRad", "Dimensions", "General Fillet")
    params.addProperty("App::PropertyAngle", "Angle1", "Dimensions", "Angle 1")
    params.addProperty("App::PropertyAngle", "Angle2", "Dimensions", "Angle 2")
    params.addProperty("App::PropertyLength", "FaceW", "Dimensions", "Face Width")
    params.addProperty("App::PropertyLength", "FaceH", "Dimensions", "Face Height")
    params.addProperty("App::PropertyLength", "FaceL", "Dimensions", "Face Length")
    params.addProperty("App::PropertyLength", "FaceDia", "Dimensions", "Face Diameter")
    params.addProperty("App::PropertyLength", "FaceLen", "Dimensions", "Face Length 2")
    params.addProperty("App::PropertyLength", "CircDia", "Dimensions", "Circular Groove Diameter")
    params.addProperty("App::PropertyLength", "CircW", "Dimensions", "Circular Groove Width")
    params.addProperty("App::PropertyLength", "CircLen", "Dimensions", "Circular Groove Length")
    params.addProperty("App::PropertyLength", "KeywayLen", "Dimensions", "Keyway Length")
    params.addProperty("App::PropertyLength", "KeywayW", "Dimensions", "Keyway Width")
    params.addProperty("App::PropertyLength", "KeywayH", "Dimensions", "Keyway Height")
    params.addProperty("App::PropertyLength", "ConeAngle", "Dimensions", "Cone Angle")
    
    # Set Values from Drawing
    params.BaseDia = 120
    params.ShaftLen = 170
    params.ShaftDia = 40
    params.TaperDia = 210
    params.TaperLen = 35
    params.ConeDia = 28 # Approximate from drawing
    params.ConeLen = 85
    params.SlotWidth = 4
    params.SlotDepth = 14
    params.SlotLen = 40
    params.SlotOffset = 35
    params.FilletRad = 3
    params.Angle1 = 135
    params.Angle2 = 45 # Approximate from drawing
    params.FaceW = 100
    params.FaceH = 35
    params.FaceL = 30 # Approximate from drawing
    params.FaceDia = 56 # Approximate from drawing
    params.FaceLen = 35 # Approximate from drawing
    params.CircDia = 78.4
    params.CircW = 10
    params.CircLen = 100 # Approximate from drawing
    params.KeywayLen = 85
    params.KeywayW = 18
    params.KeywayH = 12 # Approximate from drawing
    params.ConeAngle = 243.4
    
    # --- Features ---

    # 1. Main Body (Shaft)
    sketch1 = body.newObject("PartDesign::SketchObject", "Sketch_Main")
    sketch1.Plane = "XY_Plane"
    sketch1.mapTo3rdAxis("V_Axis", (PartDesign::Face("Base"), "X_Axis"))
    sketch1.mapTo3rdAxis("Z_Axis", (PartDesign::Face("Base"), "Z_Axis"))
    
    # Draw the cross-section of the main body
    sketch1.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.ShaftLen, 0, 0))) # Centerline
    sketch1.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.ShaftLen/2, 0, 0))) # Half width
    sketch1.addGeometry(Part.Circle(App.Vector(params.ShaftLen/2, 0, 0), App.Vector(0, 0, 1), params.ShaftDia/2)) # End face
    sketch1.addGeometry(Part.LineSegment(App.Vector(params.ShaftLen/2, 0, 0), App.Vector(params.ShaftLen, 0, 0))) # Half length
    
    # Constraints
    sketch1.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 0))
    sketch1.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 0, 0))
    sketch1.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 1, params.ShaftLen))
    sketch1.addConstraint(Sketcher.Constraint("Radius", 0, 1, 0, params.ShaftDia/2))
    
    body.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 0, 0))
    body.addConstraint(Sketcher.Constraint("Axis", 0, 0, 0, 0))
    
    pad1 = body.newObject("PartDesign::Pad", "Pad_Main")
    pad1.Profile = "Sketch_Main"
    pad1.Length = params.ShaftLen
    pad1.setExpression("Length", "Parameters.ShaftLen")
    
    # 2. Tapered Section
    sketch2 = body.newObject("PartDesign::SketchObject", "Sketch_Taper")
    sketch2.Plane = "XY_Plane"
    sketch2.mapTo3rdAxis("V_Axis", (PartDesign::Face("Base"), "X_Axis"))
    sketch2.mapTo3rdAxis("Z_Axis", (PartDesign::Face("Base"), "Z_Axis"))
    
    sketch2.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.TaperLen, 0, 0)))
    sketch2.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.TaperLen/2, 0, 0)))
    sketch2.addGeometry(Part.LineSegment(App.Vector(params.TaperLen/2, 0, 0), App.Vector(params.TaperLen, params.TaperDia/2, 0)))
    sketch2.addGeometry(Part.LineSegment(App.Vector(params.TaperLen, params.TaperDia/2, 0), App.Vector(params.TaperLen, 0, 0)))
    sketch2.addGeometry(Part.LineSegment(App.Vector(params.TaperLen, 0, 0), App.Vector(params.TaperLen, 0, 0))) # End face
    
    sketch2.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 0))
    sketch2.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 0, 0))
    sketch2.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 1, params.TaperLen))
    sketch2.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 0, 2, params.TaperDia/2))
    
    body.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 0, 0))
    body.addConstraint(Sketcher.Constraint("Axis", 0, 0, 0, 0))
    
    # Taper feature
    pad2 = body.newObject("PartDesign::Pad", "Pad_Taper")
    pad2.Profile = "Sketch_Taper"
    pad2.Length = params.TaperLen
    pad2.setExpression("Length", "Parameters.TaperLen")
    pad2.setExpression("Length2", "Parameters.TaperLen")
    pad2.setExpression("Length3", "Parameters.TaperLen")
    pad2.setExpression("Length4", "Parameters.TaperLen")
    pad2.setExpression("Length5", "Parameters.TaperLen")
    
    # 3. Cone Section
    sketch3 = body.newObject("PartDesign::SketchObject", "Sketch_Cone")
    sketch3.Plane = "XY_Plane"
    sketch3.mapTo3rdAxis("V_Axis", (PartDesign::Face("Base"), "X_Axis"))
    sketch3.mapTo3rdAxis("Z_Axis", (PartDesign::Face("Base"), "Z_Axis"))
    
    sketch3.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.ConeLen, 0, 0)))
    sketch3.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.ConeLen/2, 0, 0)))
    sketch3.addGeometry(Part.LineSegment(App.Vector(params.ConeLen/2, 0, 0), App.Vector(params.ConeLen, params.ConeDia/2, 0)))
    sketch3.addGeometry(Part.LineSegment(App.Vector(params.ConeLen, params.ConeDia/2, 0), App.Vector(params.ConeLen, 0, 0)))
    sketch3.addGeometry(Part.LineSegment(App.Vector(params.ConeLen, 0, 0), App.Vector(params.ConeLen, 0, 0)))
    
    sketch3.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 0))
    sketch3.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 0, 0))
    sketch3.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 1, params.ConeLen))
    sketch3.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 0, 2, params.ConeDia/2))
    
    body.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 0, 0))
    body.addConstraint(Sketcher.Constraint("Axis", 0, 0, 0, 0))
    
    # Cone feature
    pad3 = body.newObject("PartDesign::Pad", "Pad_Cone")
    pad3.Profile = "Sketch_Cone"
    pad3.Length = params.ConeLen
    pad3.setExpression("Length", "Parameters.ConeLen")
    pad3.setExpression("Length2", "Parameters.ConeLen")
    pad3.setExpression("Length3", "Parameters.ConeLen")
    pad3.setExpression("Length4", "Parameters.ConeLen")
    pad3.setExpression("Length5", "Parameters.ConeLen")
    
    # 4. Face (Top)
    sketch4 = body.newObject("PartDesign::SketchObject", "Sketch_Face")
    sketch4.Plane = "XY_Plane"
    sketch4.mapTo3rdAxis("V_Axis", (PartDesign::Face("Base"), "X_Axis"))
    sketch4.mapTo3rdAxis("Z_Axis", (PartDesign::Face("Base"), "Z_Axis"))
    
    sketch4.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.FaceLen, 0, 0)))
    sketch4.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.FaceLen/2, 0, 0)))
    sketch4.addGeometry(Part.LineSegment(App.Vector(params.FaceLen/2, 0, 0), App.Vector(params.FaceLen, params.FaceH/2, 0)))
    sketch4.addGeometry(Part.LineSegment(App.Vector(params.FaceLen, params.FaceH/2, 0), App.Vector(params.FaceLen, 0, 0)))
    sketch4.addGeometry(Part.LineSegment(App.Vector(params.FaceLen, 0, 0), App.Vector(params.FaceLen, 0, 0)))
    
    sketch4.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 0))
    sketch4.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 0, 0))
    sketch4.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 1, params.FaceLen))
    sketch4.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 0, 2, params.FaceH/2))
    
    body.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 0, 0))
    body.addConstraint(Sketcher.Constraint("Axis", 0, 0, 0, 0))
    
    # Face feature
    pad4 = body.newObject("PartDesign::Pad", "Pad_Face")
    pad4.Profile = "Sketch_Face"
    pad4.Length = params.FaceLen
    pad4.setExpression("Length", "Parameters.FaceLen")
    pad4.setExpression("Length2", "Parameters.FaceLen")
    pad4.setExpression("Length3", "Parameters.FaceLen")
    pad4.setExpression("Length4", "Parameters.FaceLen")
    pad4.setExpression("Length5", "Parameters.FaceLen")
    
    # 5. Circular Groove
    sketch5 = body.newObject("PartDesign::SketchObject", "Sketch_CircGroove")
    sketch5.Plane = "XY_Plane"
    sketch5.mapTo3rdAxis("V_Axis", (PartDesign::Face("Base"), "X_Axis"))
    sketch5.mapTo3rdAxis("Z_Axis", (PartDesign::Face("Base"), "Z_Axis"))
    
    sketch5.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.CircDia/2))
    sketch5.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.CircLen, 0, 0)))
    sketch5.addGeometry(Part.LineSegment(App.Vector(params.CircLen, 0, 0), App.Vector(params.CircLen, 0, 0)))
    
    sketch5.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 0))
    sketch5.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 0, 0))
    sketch5.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 1, params.CircLen))
    sketch5.addConstraint(Sketcher.Constraint("Radius", 0, 1, 0, params.CircDia/2))
    
    body.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 0, 0))
    body.addConstraint(Sketcher.Constraint("Axis", 0, 0, 0, 0))
    
    # Circular Groove feature
    pad5 = body.newObject("PartDesign::Pad", "Pad_CircGroove")
    pad5.Profile = "Sketch_CircGroove"
    pad5.Length = params.CircLen
    pad5.setExpression("Length", "Parameters.CircLen")
    pad5.setExpression("Length2", "Parameters.CircLen")
    pad5.setExpression("Length3", "Parameters.CircLen")
    pad5.setExpression("Length4", "Parameters.CircLen")
    pad5.setExpression("Length5", "Parameters.CircLen")
    
    # 6. Keyway
    sketch6 = body.newObject("PartDesign::SketchObject", "Sketch_Keyway")
    sketch6.Plane = "XY_Plane"
    sketch6.mapTo3rdAxis("V_Axis", (PartDesign::Face("Base"), "X_Axis"))
    sketch6.mapTo3rdAxis("Z_Axis", (PartDesign::Face("Base"), "Z_Axis"))
    
    sketch6.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.KeywayLen, 0, 0)))
    sketch6.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.KeywayLen/2, 0, 0)))
    sketch6.addGeometry(Part.LineSegment(App.Vector(params.KeywayLen/2, 0, 0), App.Vector(params.KeywayLen, params.KeywayH/2, 0)))
    sketch6.addGeometry(Part.LineSegment(App.Vector(params.KeywayLen, params.KeywayH/2, 0), App.Vector(params.KeywayLen, 0, 0)))
    sketch6.addGeometry(Part.LineSegment(App.Vector(params.KeywayLen, 0, 0), App.Vector(params.KeywayLen, 0, 0)))
    
    sketch6.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 0, 0))
    sketch6.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 0,
