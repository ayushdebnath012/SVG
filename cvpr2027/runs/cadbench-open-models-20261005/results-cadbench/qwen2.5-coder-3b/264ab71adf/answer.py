import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("DiscSpring")

# Set the active document
FreeCAD.setActiveDocument("DiscSpring")

# Create a new PartDesign body
body = PartDesign.Body()

# Create a new conical disc
disc = PartDesign.Disc()
disc.Radius1 = 4.2  # inner diameter
disc.Radius2 = 8.0  # outer diameter
disc.Height = 0.6  # overall height
disc.Thickness = 0.4  # thickness with bearing flat
disc.ConeHeight = 0.2  # cone height
disc.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the disc to the body
body.addObject(disc)

# Create a new bearing flat
bearing_flat = PartDesign.BearingFlat()
bearing_flat.Radius = 4.2  # inner diameter
bearing_flat.Height = 0.4  # thickness with bearing flat
bearing_flat.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the bearing flat to the body
body.addObject(bearing_flat)

# Create a new bearing flat
bearing_flat = PartDesign.BearingFlat()
bearing_flat.Radius = 8.0  # outer diameter
bearing_flat.Height = 0.4  # thickness with bearing flat
bearing_flat.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the bearing flat to the body
body.addObject(bearing_flat)

# Create a new solid from the body
solid = body.makeSolid()

# Add the solid to the document
doc.addObject("Part::Feature", "DiscSpringSolid")
doc["DiscSpringSolid"].Shape = solid

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument("DiscSpring")
