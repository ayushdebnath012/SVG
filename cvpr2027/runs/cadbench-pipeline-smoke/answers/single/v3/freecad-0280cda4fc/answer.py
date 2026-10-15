import os
import FreeCAD
import PartDesign
import Sketcher
import Part

def build_base(doc):
    body = doc.addObject('PartDesign::Body', 'Body')
    
    # 1. Base Pad
    sketch_base = doc.addObject('Sketcher::SketchObject', 'SketchBase')
    sketch_base.Support = (doc.XY_Plane, [''])
    doc.recompute()
    
    # Square centered or at origin? Usually centered on origin or corner. Let's center on origin.
    # base_side_length = 60
    s = 60.0
    sketch_base.addGeometry(Part.LineSegment(
        FreeCAD.Vector(-s/2, -s/2, 0), FreeCAD.Vector(s/2, -s/2, 0)), False)
    sketch_base.addGeometry(Part.LineSegment(
        FreeCAD.Vector(s/2, -s/2, 0), FreeCAD.Vector(s/2, s/2, 0)), False)
    sketch_base.addGeometry(Part.LineSegment(
        FreeCAD.Vector(s/2, s/2, 0), FreeCAD.Vector(-s/2, s/2, 0)), False)
    sketch_base.addGeometry(Part.LineSegment(
        FreeCAD.Vector(-s/2, s/2, 0), FreeCAD.Vector(-s/2, -s/2, 0)), False)
    
    pad = doc.addObject('PartDesign::Pad', 'BasePad')
    pad.Profile = sketch_base
    pad.Length = 80.0
    body.addCnx(pad)
    doc.recompute()
    
    # 2. Stepped slot from rear edge of top face
    # Let's assume top face is XY at Z = 80 (since pad extrudes along +Z by 80)
    sketch_slot = doc.addObject('Sketcher::SketchObject', 'SketchSlot')
    sketch_slot.Support = (doc.YZ_Plane, ['']) # Or top face XY plane at Z=80
    # Actually, let's use XY plane with offset 80, or reference top face.
    # Let's attach to XY plane with Z=80.
    sketch_slot.MapMode = 'FlatFace'
    # To keep it simple and robust, let's sketch on XY plane and use Pad/Pocket with offset or map to top face.
    # Let's map to top face of pad: Pad.Faces[5] typically, or just use XY plane with Z position.
    
    return doc

def create_files():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stem = 'answer'
    
    # Base model
    doc_base = FreeCAD.newDocument('BaseDoc')
    build_base(doc_base)
    base_path = os.path.join(script_dir, f'{stem}_base.FCStd')
    doc_base.saveAs(base_path)
    FreeCAD.closeDocument('BaseDoc')
    
    # Edit model
    doc_edit = FreeCAD.newDocument('EditDoc')
    build_base(doc_edit)
    # Apply edits here...
    edit_path = os.path.join(script_dir, f'{stem}_edit.FCStd')
    doc_edit.saveAs(edit_path)
    FreeCAD.closeDocument('EditDoc')

if __name__ == '__main__':
    create_files()
