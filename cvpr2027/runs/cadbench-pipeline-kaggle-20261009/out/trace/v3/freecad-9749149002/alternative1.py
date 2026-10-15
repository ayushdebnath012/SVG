"""
Front Wheel Linkage Arm - PartDesign script for FreeCAD 1.1.0
Based on engineering drawing: 9749149002.png
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import PartDesign
import Math


def main():
    # Create a new document
    doc = App.newDocument("FrontWheelLinkage")
    App.setLastDocument(doc)
    
    # Create the main Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Add parameters for key dimensions
    params = body.newObject("App::VarSet", "Parameters")
    
    # Main dimensions from drawing
    params.addProperty("App::PropertyLength", "length1", "Dimensions", "Main length")
    params.length1 = 159.7
    params.addProperty("App::PropertyLength", "length2", "Dimensions", "Taper length")
    params.length2 = 200.3
    params.addProperty("App::PropertyLength", "length3", "Dimensions", "Section length")
    params.length3 = 31.5
    params.addProperty("App::PropertyLength", "length4", "Dimensions", "Taper section")
    params.length4 = 37.5
    params.addProperty("App::PropertyLength", "length5", "Dimensions", "Final section")
    params.length5 = 48.7
    params.addProperty("App::PropertyLength", "length6", "Dimensions", "Extension length")
    params.length6 = 56
    params.addProperty("App::PropertyLength", "length7", "Dimensions", "Right extension")
    params.length7 = 32.78
    params.addProperty("App::PropertyLength", "diameter_main", "Dimensions", "Main diameter")
    params.diameter_main = 24.21
    params.addProperty("App::PropertyLength", "diameter_shaft", "Dimensions", "Shaft diameter")
    params.diameter_shaft = 19.5
    params.addProperty("App::PropertyLength", "diameter_pin", "Dimensions", "Pin diameter")
    params.diameter_pin = 12.0
    params.addProperty("App::PropertyLength", "radius_chamfer", "Dimensions", "Chamfer radius")
    params.radius_chamfer = 2.5
    params.addProperty("App::PropertyLength", "radius_fillet", "Dimensions", "Fillet radius")
    params.radius_fillet = 1.75
    params.addProperty("App::PropertyAngle", "angle_left", "Dimensions", "Left angle")
    params.angle_left = 129
    params.addProperty("App::PropertyAngle", "angle_right", "Dimensions", "Right angle")
    params.angle_right = 231
    
    # Create planes
    XY_Plane = doc.addObject("PartDesign::Plane", "XY_Plane")
    XY_Plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    doc.recompute()
    
    XZ_Plane = doc.addObject("PartDesign::Plane", "XZ_Plane")
    XZ_Plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 90, 0))
    doc.recompute()
    
    YZ_Plane = doc.addObject("PartDesign::Plane", "YZ_Plane")
    YZ_Plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(90, 0, 0))
    doc.recompute()
    
    # Create axes
    X_Axis = doc.addObject("PartDesign::Axis", "X_Axis")
    X_Axis.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    X_Axis.XDirection = App.Vector(1, 0, 0)
    doc.recompute()
    
    Y_Axis = doc.addObject("PartDesign::Axis", "Y_Axis")
    Y_Axis.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    Y_Axis.YDirection = App.Vector(0, 1, 0)
    doc.recompute()
    
    Z_Axis = doc.addObject("PartDesign::Axis", "Z_Axis")
    Z_Axis.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    Z_Axis.ZDirection = App.Vector(0, 0, 1)
    doc.recompute()
    
    # Main sketch on XY plane (left side view)
    sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_Main")
    sketch_main.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement2 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement3 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement4 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement5 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement6 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement7 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement8 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement9 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement10 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement11 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement12 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement13 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement14 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement15 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement16 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement17 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement18 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement19 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement20 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement21 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement22 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement23 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement24 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement25 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement26 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement27 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement28 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement29 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement30 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement31 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement32 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement33 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement34 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement35 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement36 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement37 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement38 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement39 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement40 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement41 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement42 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement43 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement44 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement45 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement46 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement47 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement48 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement49 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement50 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement51 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement52 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement53 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement54 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement55 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement56 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement57 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement58 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement59 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement60 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement61 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement62 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement63 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement64 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement65 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement66 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement67 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement68 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement69 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement70 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement71 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement72 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement73 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement74 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement75 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement76 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement77 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement78 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement79 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement80 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement81 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement82 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement83 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement84 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement85 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement86 = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_main.Placement8
