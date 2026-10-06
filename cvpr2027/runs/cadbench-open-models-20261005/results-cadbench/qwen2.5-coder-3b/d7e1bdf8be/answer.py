```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HeadedPin")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Create a cylindrical shaft
shaft = PartDesign.Cylinder(doc, "Shaft", 3, 6)

# Create a head
head = PartDesign.Cylinder(doc, "Head", 5, 1)

# Create a chamfer on the head
chamfer = PartDesign.Chamfer(doc, "Chamfer", head, 1, 30)

# Create a fillet on the chamfer
fillet = PartDesign.Fillet(doc, "Fillet", chamfer, 0.5)

# Create a boss to attach the head to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, head, 0.5)

# Create a hole in the head
hole = PartDesign.Hole(doc, "Hole", head, 1)

# Create a fillet on the hole
fillet = PartDesign.Fillet(doc, "Fillet", hole, 0.5)

# Create a boss to attach the hole to the head
boss = PartDesign.Boss(doc, "Boss", head, hole, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss = PartDesign.Boss(doc, "Boss", shaft, boss, 0.5)

# Create a fillet on the boss
fillet = PartDesign.Fillet(doc, "Fillet", boss, 0.5)

# Create a boss to attach the boss to the shaft
boss =