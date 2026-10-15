import os
import FreeCAD
import PartDesign
import Sketcher
import Part

def create_part(doc, is_edit=False):
    body = doc.addObject('PartDesign::Body', 'Body')
    
    # 1. Base Pad
    sketch_base = doc.addObject('Sketcher::SketchObject', 'SketchBase')
    body.addObject(sketch_base)
    # Correct attachment in FreeCAD 1.1 PartDesign
    sketch_base.AttachmentSupport = [(doc.XY_Plane, '')]
    doc.recompute()
    
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
    body.addObject(pad)
    doc.recompute()

    # 2. Stepped slot from rear edge of top face
    sketch_slot = doc.addObject('Sketcher::SketchObject', 'SketchSlot')
    body.addObject(sketch_slot)
    sketch_slot.AttachmentSupport = [(pad.Shape.Faces[4], '')]
    doc.recompute()
    
    w_ov = 52.0
    depth = 55.0
    
    sketch_slot.addGeometry(Part.LineSegment(
        FreeCAD.Vector(-w_ov/2, s/2, 0), FreeCAD.Vector(w_ov/2, s/2, 0)), False)
    sketch_slot.addGeometry(Part.LineSegment(
        FreeCAD.Vector(w_ov/2, s/2, 0), FreeCAD.Vector(w_ov/2, s/2 - depth, 0)), False)
    sketch_slot.addGeometry(Part.LineSegment(
        FreeCAD.Vector(w_ov/2, s/2 - depth, 0), FreeCAD.Vector(-w_ov/2, s/2 - depth, 0)), False)
    sketch_slot.addGeometry(Part.LineSegment(
        FreeCAD.Vector(-w_ov/2, s/2 - depth, 0), FreeCAD.Vector(-w_ov/2, s/2, 0)), False)
    
    pocket_slot = doc.addObject('PartDesign::Pocket', 'SlotPocket')
    pocket_slot.Profile = sketch_slot
    pocket_slot.Length = 6.0
    body.addObject(pocket_slot)
    doc.recompute()

    if is_edit:
        sketch_front_slot = doc.addObject('Sketcher::SketchObject', 'SketchFrontSlot')
        body.addObject(sketch_front_slot)
        sketch_front_slot.AttachmentSupport = [(pad.Shape.Faces[4], '')]
        doc.recompute()
        
        ts_w = 11.0
        ts_l = 25.6
        sketch_front_slot.addGeometry(Part.LineSegment(
            FreeCAD.Vector(-ts_w/2, -s/2, 0), FreeCAD.Vector(ts_w/2, -s/2, 0)), False)
        sketch_front_slot.addGeometry(Part.LineSegment(
            FreeCAD.Vector(ts_w/2, -s/2, 0), FreeCAD.Vector(ts_w/2, -s/2 + ts_l, 0)), False)
        sketch_front_slot.addGeometry(Part.LineSegment(
            FreeCAD.Vector(ts_w/2, -s/2 + ts_l, 0), FreeCAD.Vector(-ts_w/2, -s/2 + ts_l, 0)), False)
        sketch_front_slot.addGeometry(Part.LineSegment(
            FreeCAD.Vector(-ts_w/2, -s/2 + ts_l, 0), FreeCAD.Vector(-ts_w/2, -s/2, 0)), False)
        
        front_pocket = doc.addObject('PartDesign::Pocket', 'FrontSlotPocket')
        front_pocket.Profile = sketch_front_slot
        front_pocket.Length = 5.5
        body.addObject(front_pocket)
        doc.recompute()

    return doc

def create_files():
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    stem = os.path.splitext(os.path.basename(script_path))[0]
    
    # Base model
    doc_base = FreeCAD.newDocument('BaseDoc')
    create_part(doc_base, is_edit=False)
    doc_base.recompute()
    base_path = os.path.join(script_dir, f'{stem}_base.FCStd')
    doc_base.saveAs(base_path)
    FreeCAD.closeDocument('BaseDoc')
    
    # Edit model
    doc_edit = FreeCAD.newDocument('EditDoc')
    create_part(doc_edit, is_edit=True)
    doc_edit.recompute()
    edit_path = os.path.join(script_dir, f'{stem}_edit.FCStd')
    doc_edit.saveAs(edit_path)
    FreeCAD.closeDocument('EditDoc')

if __name__ == '__main__':
    create_files()
