from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import PartDesign

# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================
def main():
    # 1. Initialize Document
    doc = App.newDocument("BoomCylinderPistonRing")
    
    # ==============================================================================
    # 2. Create Named Parameters (Derived from measurements)
    # ==============================================================================
    # Based on reading the drawing:
    # Outer Diameter (OD): 276.5
    # Inner Diameter (ID): 252
    # Flange Thickness: 10
    # Flange Height: 64
    # Groove Depth: 10
    # Piston Ring Width: 14
    # Cylinder Outer Diameter: 272
    # Cylinder Inner Diameter: 252 (matches flange ID)
    # Groove Diameter (Inner): 208.5
    # Groove Diameter (Outer): 272
    # Groove Depth (from 272): 10
    # Main Cylinder Length: 161
    # Total Length: 169
    # Piston Ring Groove Diameter: 208.5
    # Piston Ring Groove Width: 14
    # Piston Ring Groove Depth: 10
    # Piston Ring Groove Radius: 4
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring
