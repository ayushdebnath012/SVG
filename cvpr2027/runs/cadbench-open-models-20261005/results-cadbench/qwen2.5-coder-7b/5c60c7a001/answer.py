import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the parameters
section_diameters = [10, 15, 20, 40, 30, 25]
section_lengths = [40, 30, 40, 10, 20, 25]

# Create the first section
prev_end = FreeCAD.Vector(0, 0, 0)
for i in range(6):
    # Create a cylindrical section
    section = body.newObject("PartDesign::Cylinder", f"Section_{i+1}")
    section.Radius = section_diameters[i] / 2
    section.Height = section_lengths[i]
    section.Placement.Base = prev_end
    section.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)
    
    # Create a flush shoulder
    shoulder = body.newObject("PartDesign::Pocket", f"Shoulder_{i+1}")
    shoulder.Base = section
    shoulder.Length = 1
    shoulder.Direction = FreeCAD.Vector(0, 0, 1)
    shoulder.Placement.Base = prev_end + FreeCAD.Vector(0, 0, section_lengths[i])
    shoulder.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)
    
    # Update the previous end position
    prev_end += FreeCAD.Vector(0, 0, section_lengths[i] + 1)

# Save the document
doc.saveAs("/app/answer.FCStd")
