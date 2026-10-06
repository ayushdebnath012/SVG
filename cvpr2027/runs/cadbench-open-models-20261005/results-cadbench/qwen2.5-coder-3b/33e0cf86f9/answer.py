```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HalfMoonKey")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(0, 0, 0))

# Add the sketch to the body
body.addObject(sketch)

# Create a new PartDesign Circle
circle = PartDesign.Circle()
circle.Radius = 2.0  # Diameter / 2
circle.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(0, 0, 0))

# Add the circle to the sketch
sketch.addObject(circle)

# Create a new PartDesign Line
line = PartDesign.Line()
line.StartPoint = FreeCAD.Vector(0, 0, 0)
line.EndPoint = FreeCAD.Vector(0, 1.4, 0)  # Moon height

# Add the line to the sketch
sketch.addObject(line)

# Create a new PartDesign Line
line2 = PartDesign.Line()
line2.StartPoint = FreeCAD.Vector(0, 1.4, 0)
line2.EndPoint = FreeCAD.Vector(2.0, 1.4, 0)  # Diameter / 2

# Add the line to the sketch
sketch.addObject(line2)

# Create a new PartDesign Line
line3 = PartDesign.Line()
line3.StartPoint = FreeCAD.Vector(2.0, 1.4, 0)
line3.EndPoint = FreeCAD.Vector(2.0, 0, 0)  # Diameter / 2

# Add the line to the sketch
sketch.addObject(line3)

# Create a new PartDesign Line
line4 = PartDesign.Line()
line4.StartPoint = FreeCAD.Vector(2.0, 0, 0)
line4.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2

# Add the line to the sketch
sketch.addObject(line4)

# Create a new PartDesign Line
line5 = PartDesign.Line()
line5.StartPoint = FreeCAD.Vector(0, 0, 0)
line5.EndPoint = FreeCAD.Vector(0, 0, 1.0)  # Key thickness

# Add the line to the sketch
sketch.addObject(line5)

# Create a new PartDesign Line
line6 = PartDesign.Line()
line6.StartPoint = FreeCAD.Vector(0, 0, 1.0)
line6.EndPoint = FreeCAD.Vector(0, 1.4, 1.0)  # Moon height + key thickness

# Add the line to the sketch
sketch.addObject(line6)

# Create a new PartDesign Line
line7 = PartDesign.Line()
line7.StartPoint = FreeCAD.Vector(0, 1.4, 1.0)
line7.EndPoint = FreeCAD.Vector(2.0, 1.4, 1.0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line7)

# Create a new PartDesign Line
line8 = PartDesign.Line()
line8.StartPoint = FreeCAD.Vector(2.0, 1.4, 1.0)
line8.EndPoint = FreeCAD.Vector(2.0, 0, 1.0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line8)

# Create a new PartDesign Line
line9 = PartDesign.Line()
line9.StartPoint = FreeCAD.Vector(2.0, 0, 1.0)
line9.EndPoint = FreeCAD.Vector(0, 0, 1.0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line9)

# Create a new PartDesign Line
line10 = PartDesign.Line()
line10.StartPoint = FreeCAD.Vector(0, 0, 1.0)
line10.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line10)

# Create a new PartDesign Line
line11 = PartDesign.Line()
line11.StartPoint = FreeCAD.Vector(0, 0, 0)
line11.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line11)

# Create a new PartDesign Line
line12 = PartDesign.Line()
line12.StartPoint = FreeCAD.Vector(0, 0, 0)
line12.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line12)

# Create a new PartDesign Line
line13 = PartDesign.Line()
line13.StartPoint = FreeCAD.Vector(0, 0, 0)
line13.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line13)

# Create a new PartDesign Line
line14 = PartDesign.Line()
line14.StartPoint = FreeCAD.Vector(0, 0, 0)
line14.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line14)

# Create a new PartDesign Line
line15 = PartDesign.Line()
line15.StartPoint = FreeCAD.Vector(0, 0, 0)
line15.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line15)

# Create a new PartDesign Line
line16 = PartDesign.Line()
line16.StartPoint = FreeCAD.Vector(0, 0, 0)
line16.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line16)

# Create a new PartDesign Line
line17 = PartDesign.Line()
line17.StartPoint = FreeCAD.Vector(0, 0, 0)
line17.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line17)

# Create a new PartDesign Line
line18 = PartDesign.Line()
line18.StartPoint = FreeCAD.Vector(0, 0, 0)
line18.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line18)

# Create a new PartDesign Line
line19 = PartDesign.Line()
line19.StartPoint = FreeCAD.Vector(0, 0, 0)
line19.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line19)

# Create a new PartDesign Line
line20 = PartDesign.Line()
line20.StartPoint = FreeCAD.Vector(0, 0, 0)
line20.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line20)

# Create a new PartDesign Line
line21 = PartDesign.Line()
line21.StartPoint = FreeCAD.Vector(0, 0, 0)
line21.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line21)

# Create a new PartDesign Line
line22 = PartDesign.Line()
line22.StartPoint = FreeCAD.Vector(0, 0, 0)
line22.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line22)

# Create a new PartDesign Line
line23 = PartDesign.Line()
line23.StartPoint = FreeCAD.Vector(0, 0, 0)
line23.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line23)

# Create a new PartDesign Line
line24 = PartDesign.Line()
line24.StartPoint = FreeCAD.Vector(0, 0, 0)
line24.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line24)

# Create a new PartDesign Line
line25 = PartDesign.Line()
line25.StartPoint = FreeCAD.Vector(0, 0, 0)
line25.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line25)

# Create a new PartDesign Line
line26 = PartDesign.Line()
line26.StartPoint = FreeCAD.Vector(0, 0, 0)
line26.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line26)

# Create a new PartDesign Line
line27 = PartDesign.Line()
line27.StartPoint = FreeCAD.Vector(0, 0, 0)
line27.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line27)

# Create a new PartDesign Line
line28 = PartDesign.Line()
line28.StartPoint = FreeCAD.Vector(0, 0, 0)
line28.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line28)

# Create a new PartDesign Line
line29 = PartDesign.Line()
line29.StartPoint = FreeCAD.Vector(0, 0, 0)
line29.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line29)

# Create a new PartDesign Line
line30 = PartDesign.Line()
line30.StartPoint = FreeCAD.Vector(0, 0, 0)
line30.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line30)

# Create a new PartDesign Line
line31 = PartDesign.Line()
line31.StartPoint = FreeCAD.Vector(0, 0, 0)
line31.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line31)

# Create a new PartDesign Line
line32 = PartDesign.Line()
line32.StartPoint = FreeCAD.Vector(0, 0, 0)
line32.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line32)

# Create a new PartDesign Line
line33 = PartDesign.Line()
line33.StartPoint = FreeCAD.Vector(0, 0, 0)
line33.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line33)

# Create a new PartDesign Line
line34 = PartDesign.Line()
line34.StartPoint = FreeCAD.Vector(0, 0, 0)
line34.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line34)

# Create a new PartDesign Line
line35 = PartDesign.Line()
line35.StartPoint = FreeCAD.Vector(0, 0, 0)
line35.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line35)

# Create a new PartDesign Line
line36 = PartDesign.Line()
line36.StartPoint = FreeCAD.Vector(0, 0, 0)
line36.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line36)

# Create a new PartDesign Line
line37 = PartDesign.Line()
line37.StartPoint = FreeCAD.Vector(0, 0, 0)
line37.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line37)

# Create a new PartDesign Line
line38 = PartDesign.Line()
line38.StartPoint = FreeCAD.Vector(0, 0, 0)
line38.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line38)

# Create a new PartDesign Line
line39 = PartDesign.Line()
line39.StartPoint = FreeCAD.Vector(0, 0, 0)
line39.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line39)

# Create a new PartDesign Line
line40 = PartDesign.Line()
line40.StartPoint = FreeCAD.Vector(0, 0, 0)
line40.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line40)

# Create a new PartDesign Line
line41 = PartDesign.Line()
line41.StartPoint = FreeCAD.Vector(0, 0, 0)
line41.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line41)

# Create a new PartDesign Line
line42 = PartDesign.Line()
line42.StartPoint = FreeCAD.Vector(0, 0, 0)
line42.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line42)

# Create a new PartDesign Line
line43 = PartDesign.Line()
line43.StartPoint = FreeCAD.Vector(0, 0, 0)
line43.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line43)

# Create a new PartDesign Line
line44 = PartDesign.Line()
line44.StartPoint = FreeCAD.Vector(0, 0, 0)
line44.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line44)

# Create a new PartDesign Line
line45 = PartDesign.Line()
line45.StartPoint = FreeCAD.Vector(0, 0, 0)
line45.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line45)

# Create a new PartDesign Line
line46 = PartDesign.Line()
line46.StartPoint = FreeCAD.Vector(0, 0, 0)
line46.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line46)

# Create a new PartDesign Line
line47 = PartDesign.Line()
line47.StartPoint = FreeCAD.Vector(0, 0, 0)
line47.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line47)

# Create a new PartDesign Line
line48 = PartDesign.Line()
line48.StartPoint = FreeCAD.Vector(0, 0, 0)
line48.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line48)

# Create a new PartDesign Line
line49 = PartDesign.Line()
line49.StartPoint = FreeCAD.Vector(0, 0, 0)
line49.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line49)

# Create a new PartDesign Line
line50 = PartDesign.Line()
line50.StartPoint = FreeCAD.Vector(0, 0, 0)
line50.EndPoint = FreeCAD.Vector(0, 0, 0)  # Diameter / 2 + key thickness

# Add the line to the sketch
sketch.addObject(line50)

# Create a new PartDesign Line
line51 = PartDesign.Line()
line51.StartPoint = FreeCAD.Vector(0, 0, 0)
line51.EndPoint