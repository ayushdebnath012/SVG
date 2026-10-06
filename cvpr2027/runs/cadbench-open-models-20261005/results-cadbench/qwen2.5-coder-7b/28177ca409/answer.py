import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the key body
key_body = body.newObject("PartDesign::Pad", "KeyBody")
key_body.Length = 14.0
key_body.Profile = Part.makeBox(4.0, 4.0, 4.0)

# Create a PartDesign Feature for the taper
taper = body.newObject("PartDesign::Pocket", "Taper")
taper.Length = 14.0
taper.Profile = Part.makeCylinder(2.0, 14.0)
taper.Profile.Placement.Base = FreeCAD.Vector(0, 0, 4.0)

# Create a PartDesign Feature for the head
head = body.newObject("PartDesign::Pocket", "Head")
head.Length = 7.0
head.Profile = Part.makeCylinder(2.0, 7.0)
head.Profile.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the taper fillet
taper_fillet = body.newObject("PartDesign::Fillet", "TaperFillet")
taper_fillet.Radius = 0.5
taper_fillet.Base = [taper, key_body]
taper_fillet.Edges = [taper.Shape.Edges[0]]

# Create a PartDesign Feature for the head fillet
head_fillet = body.newObject("PartDesign::Fillet", "HeadFillet")
head_fillet.Radius = 0.5
head_fillet.Base = [head, key_body]
head_fillet.Edges = [head.Shape.Edges[0]]

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
