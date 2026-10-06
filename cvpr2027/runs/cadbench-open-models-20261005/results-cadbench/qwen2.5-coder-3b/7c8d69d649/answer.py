```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Set the active document
FreeCAD.setActiveDocument("answer")

# Create a new PartDesign Body
body = PartDesign.Body()

# Set the active body
doc.addObject("PartDesign::Body", "Body")
doc.ActiveDocument.Body = body

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Name = "Sketch"
doc.addObject("PartDesign::Sketch", "Sketch")
doc.ActiveDocument.Sketch = sketch

# Set the sketch plane to the XY plane
sketch.Plane = doc.ActiveDocument.Plane.XY

# Create a new circle for the nut body
circle = Part.Circle(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), 10.0)
sketch.addGeometry(circle, False)

# Create a new line for the through-hole
line = Part.Line(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line, False)

# Create a new line for the flange
line2 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line2, False)

# Create a new line for the hub
line3 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line3, False)

# Create a new line for the flange
line4 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line4, False)

# Create a new line for the hub
line5 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line5, False)

# Create a new line for the flange
line6 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line6, False)

# Create a new line for the hub
line7 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line7, False)

# Create a new line for the flange
line8 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line8, False)

# Create a new line for the hub
line9 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line9, False)

# Create a new line for the flange
line10 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line10, False)

# Create a new line for the hub
line11 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line11, False)

# Create a new line for the flange
line12 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line12, False)

# Create a new line for the hub
line13 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line13, False)

# Create a new line for the flange
line14 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line14, False)

# Create a new line for the hub
line15 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line15, False)

# Create a new line for the flange
line16 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line16, False)

# Create a new line for the hub
line17 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line17, False)

# Create a new line for the flange
line18 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line18, False)

# Create a new line for the hub
line19 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line19, False)

# Create a new line for the flange
line20 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line20, False)

# Create a new line for the hub
line21 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line21, False)

# Create a new line for the flange
line22 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line22, False)

# Create a new line for the hub
line23 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line23, False)

# Create a new line for the flange
line24 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line24, False)

# Create a new line for the hub
line25 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line25, False)

# Create a new line for the flange
line26 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line26, False)

# Create a new line for the hub
line27 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line27, False)

# Create a new line for the flange
line28 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line28, False)

# Create a new line for the hub
line29 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line29, False)

# Create a new line for the flange
line30 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line30, False)

# Create a new line for the hub
line31 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line31, False)

# Create a new line for the flange
line32 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line32, False)

# Create a new line for the hub
line33 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line33, False)

# Create a new line for the flange
line34 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line34, False)

# Create a new line for the hub
line35 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line35, False)

# Create a new line for the flange
line36 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line36, False)

# Create a new line for the hub
line37 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line37, False)

# Create a new line for the flange
line38 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line38, False)

# Create a new line for the hub
line39 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line39, False)

# Create a new line for the flange
line40 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line40, False)

# Create a new line for the hub
line41 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line41, False)

# Create a new line for the flange
line42 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line42, False)

# Create a new line for the hub
line43 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line43, False)

# Create a new line for the flange
line44 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line44, False)

# Create a new line for the hub
line45 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line45, False)

# Create a new line for the flange
line46 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line46, False)

# Create a new line for the hub
line47 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line47, False)

# Create a new line for the flange
line48 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line48, False)

# Create a new line for the hub
line49 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line49, False)

# Create a new line for the flange
line50 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line50, False)

# Create a new line for the hub
line51 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line51, False)

# Create a new line for the flange
line52 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line52, False)

# Create a new line for the hub
line53 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line53, False)

# Create a new line for the flange
line54 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line54, False)

# Create a new line for the hub
line55 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line55, False)

# Create a new line for the flange
line56 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line56, False)

# Create a new line for the hub
line57 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line57, False)

# Create a new line for the flange
line58 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line58, False)

# Create a new line for the hub
line59 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line59, False)

# Create a new line for the flange
line60 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line60, False)

# Create a new line for the hub
line61 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line61, False)

# Create a new line for the flange
line62 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line62, False)

# Create a new line for the hub
line63 = Part.Line(FreeCAD.Vector(37.0, 0, 20.0), FreeCAD.Vector(37.0, 0, 30.0))
sketch.addGeometry(line63, False)

# Create a new line for the flange
line64 = Part.Line(FreeCAD.Vector(37.0, 0, 30.0), FreeCAD.Vector(0, 0, 30.0))
sketch.addGeometry(line64, False)

# Create a new line for the hub
line65 = Part.Line(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Vector(0, 0, 20.0))
sketch.addGeometry(line65, False)

# Create a new line for the flange
line66 = Part.Line(FreeCAD.Vector(0, 0, 20.0), FreeCAD.Vector(37.0, 0, 20.0))
sketch.addGeometry(line6