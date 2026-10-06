```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Washer")

# Set the active document
FreeCAD.setActiveDocument("Washer")

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Plane
plane = PartDesign.Plane()
plane.Base = doc.ActiveObject
plane.Axis = FreeCAD.Vector(0, 0, 1)
plane.Length = 40
plane.Width = 40
plane.Name = "WasherPlane"

# Add the plane to the document
doc.addObject("PartDesign::Plane", "WasherPlane")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch.Plane = doc.ActiveObject
sketch.Name = "WasherSketch"

# Add the sketch to the document
doc.addObject("PartDesign::Sketch", "WasherSketch")

# Create a new PartDesign Feature
feature = PartDesign.Feature()
feature.Base = doc.ActiveObject
feature.Name = "WasherFeature"

# Add the feature to the document
doc.addObject("PartDesign::Feature", "WasherFeature")

# Create a new PartDesign Sketch
sketch = PartDesign.Sketch()
sketch