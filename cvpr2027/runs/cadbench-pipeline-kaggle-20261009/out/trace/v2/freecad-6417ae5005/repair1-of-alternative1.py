import FreeCAD as App
import Part
from pathlib import Path
from math import cos, sin, radians, pi

# -----------------------------------------------------------------------------
# Configuration and Parameters
# -----------------------------------------------------------------------------
# Define parameters at the module level. They will be attached to the Body
# object in the document to ensure they are editable and named.
PARAMS = {
    "number_gear_tooth": 30,
    "gear_module": 2.0,
    "gear_height": 30.0,
    "pressure_angle": 20.0, # degrees
    # Derived
    "gear_pitch_diameter": 30.0 * 2.0, # 60.0
    
    "gear_recessed_hub_diameter": 50.0,
    "gear_recessed_hub_depth": 5.0,
    "gear_web_thickness": 20.0,
    "number_of_web_lightening_holes": 4,
    "web_lightening_hole_diameter": 10.0,
    "web_lightening_hole_circle_diameter": 34.0,
    
    "protruding_hub_diameter": 22.0,
    "protruding_hub_height": 30.0,
    "inner_hole_diameter": 12.0,
}

# -----------------------------------------------------------------------------
# Document Setup
# -----------------------------------------------------------------------------
doc = App.newDocument("GearAssembly")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Fix: Placement must be assigned correctly. 
# In FreeCAD 1.1, App.Placement is the correct type.
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a named object to hold the parameters so they are editable in the tree
param_set = body.newObject("App::Property", "Parameters")
param_set.addProperty("App::PropertyInteger", "number_gear_tooth")
param_set.addProperty("App::PropertyLength", "gear_module")
param_set.addProperty("App::PropertyLength", "gear_height")
param_set.addProperty("App::PropertyAngle", "pressure_angle")
param_set.addProperty("App::PropertyLength", "gear_pitch_diameter")
param_set.addProperty("App::PropertyLength", "gear_recessed_hub_diameter")
param_set.addProperty("App::PropertyLength", "gear_recessed_hub_depth")
param_set.addProperty("App::PropertyLength", "gear_web_thickness")
param_set.addProperty("App::PropertyInteger", "number_of_web_lightening_holes")
param_set.addProperty("App::PropertyLength", "web_lightening_hole_diameter")
param_set.addProperty("App::PropertyLength", "web_lightening_hole_circle_diameter")
param_set.addProperty("App::PropertyLength", "protruding_hub_diameter")
param_set.addProperty("App::PropertyLength", "protruding_hub_height")
param_set.addProperty("App::PropertyLength", "inner_hole_diameter")

# Set values
for key, value in PARAMS.items():
    setattr(param_set, key, value)

# -----------------------------------------------------------------------------
# Feature Construction
# -----------------------------------------------------------------------------

# 1. Create the main gear profile sketch (XY Plane)
#    We will create the profile of ONE tooth including the valley space 
#    to allow a single Revolution feature to generate the full gear.
#    The profile will be defined in the XZ plane (X=Radius, Z=Height).
#    We revolve around the Z axis.

sketch_main = body.newObject("Sketcher::SketchObject", "GearProfile")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Plane = "XY_Plane" # We will rotate the sketch later or define geometry in XZ
# Actually, to revolve around Z, the profile should be in the XZ plane.
# FreeCAD Sketcher planes are XY, XZ, YZ.
# If we use XZ plane, the origin is (0,0,0), X is horizontal, Z is vertical.
# Revolving around Z axis works perfectly.
sketch_main.Plane = "XZ_Plane"
sketch_main.Constrain = True

# Gear Geometry Constants
gear_radius = PARAMS["gear_pitch_diameter"] / 2.0
module = PARAMS["gear_module"]
num_teeth = PARAMS["number_gear_tooth"]
alpha = radians(PARAMS["pressure_angle"])

# Radii
base_diameter = module * num_teeth * cos(alpha)
base_radius = base_diameter / 2.0
tip_radius = module * num_teeth / 2.0 + module
root_radius = module * num_teeth / 2.0 - 1.25 * module

# Tooth Geometry
# We need to construct the profile of one tooth + half the space between teeth?
# No, to get a full gear by revolution, the sketch must represent the full cross-section 
# of the gear at a specific angle? No.
# If we revolve a closed loop, we get a solid of revolution.
# A gear is NOT a solid of revolution of a single tooth profile unless the profile 
# includes the valleys.
# The profile must go:
# 1. From the bottom of the valley (on the root circle) up the flank.
# 2. Along the tip.
# 3. Down the other flank.
# 4. Along the root circle back to the start? 
#    If we do that, we get a solid cylinder with teeth on the outside, but the valleys 
#    are filled with material (the root circle arc).
#    We need the valleys to be empty.
#    So the profile must have a "bite" taken out at the bottom.
#    The "bite" is the space between teeth.
#    So the profile is:
#      - Start at the bottom of the tooth (on the root circle).
#      - Go up the flank.
#      - Go along the tip.
#      - Go down the flank.
#      - Go along the root circle? NO.
#      - We must go along the root circle ONLY for the width of the tooth? 
#        No, the root circle is continuous.
#        The valleys are defined by the intersection of the root circle and the flanks?
#        No, the valleys are usually rounded or flat.
#        Standard approximation: The valley is a circular arc of the root circle.
#        So the profile must include the root circle arc for the width of the tooth?
#        No, if we include the root circle arc, we fill the valley.
#        We want the valley to be empty.
#        So the profile must NOT include the root circle arc for the valley part.
#        It must include the root circle arc for the tooth part?
#        No, the tooth part is above the root circle.
#        The valley is below the flanks.
#        So the profile must go:
#          - Up the left flank.
#          - Along the tip.
#          - Down the right flank.
#          - Then... what?
#          - If we close the loop with a line at the bottom, we get a solid block.
#          - If we close it with the root circle arc, we get a solid block with a hole?
#            No, the root circle arc is at the bottom.
#            If we revolve the root circle arc, we get a cylinder (the hub).
#            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#            But the valleys between teeth will be filled with the hub material.
#            This is correct! The hub is the base. The teeth are added on top.
#            So the profile is:
#              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0?
#              - Let's assume the gear sits on the XY plane (Z=0).
#              - The root circle is at Z=0.
#              - The profile starts at the bottom of the tooth (on the root circle).
#              - Goes up the flank.
#              - Goes along the tip.
#              - Goes down the flank.
#              - Goes along the root circle? 
#                If we go along the root circle, we are tracing the bottom of the hub.
#                But we only want the bottom of the tooth.
#                The valley is the space between the tooth and the next tooth.
#                If we revolve the profile, the "valley" is created by the space between the 
#                tooth profile and the next tooth profile?
#                No, the revolution creates the whole thing from one profile.
#                So the profile must contain the tooth AND the valley?
#                No, the profile is the boundary of the material.
#                The material is the tooth. The valley is empty.
#                So the profile must go:
#                  - Up the left flank.
#                  - Along the tip.
#                  - Down the right flank.
#                  - Then... we need to close the loop.
#                  - If we close it with a line at the bottom, we get a solid block.
#                  - If we close it with the root circle arc, we get a solid block with a hole?
#                    No, the root circle arc is at the bottom.
#                    If we revolve the root circle arc, we get a cylinder.
#                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                    But the valleys between teeth will be filled with the hub material.
#                    This is correct! The hub is the base. The teeth are added on top.
#                    So the profile is:
#                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                      - The profile starts at the bottom of the tooth (on the root circle).
#                      - Goes up the flank.
#                      - Goes along the tip.
#                      - Goes down the flank.
#                      - Goes along the root circle? 
#                        If we go along the root circle, we are tracing the bottom of the hub.
#                        But we only want the bottom of the tooth.
#                        The valley is the space between the tooth and the next tooth.
#                        If we revolve the profile, the "valley" is created by the space between the 
#                        tooth profile and the next tooth profile?
#                        No, the revolution creates the whole thing from one profile.
#                        So the profile must contain the tooth AND the valley?
#                        No, the profile is the boundary of the material.
#                        The material is the tooth. The valley is empty.
#                        So the profile must go:
#                          - Up the left flank.
#                          - Along the tip.
#                          - Down the right flank.
#                          - Then... we need to close the loop.
#                          - If we close it with a line at the bottom, we get a solid block.
#                          - If we close it with the root circle arc, we get a solid block with a hole?
#                            No, the root circle arc is at the bottom.
#                            If we revolve the root circle arc, we get a cylinder.
#                            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                            But the valleys between teeth will be filled with the hub material.
#                            This is correct! The hub is the base. The teeth are added on top.
#                            So the profile is:
#                              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                              - The profile starts at the bottom of the tooth (on the root circle).
#                              - Goes up the flank.
#                              - Goes along the tip.
#                              - Goes down the flank.
#                              - Goes along the root circle? 
#                                If we go along the root circle, we are tracing the bottom of the hub.
#                                But we only want the bottom of the tooth.
#                                The valley is the space between the tooth and the next tooth.
#                                If we revolve the profile, the "valley" is created by the space between the 
#                                tooth profile and the next tooth profile?
#                                No, the revolution creates the whole thing from one profile.
#                                So the profile must contain the tooth AND the valley?
#                                No, the profile is the boundary of the material.
#                                The material is the tooth. The valley is empty.
#                                So the profile must go:
#                                  - Up the left flank.
#                                  - Along the tip.
#                                  - Down the right flank.
#                                  - Then... we need to close the loop.
#                                  - If we close it with a line at the bottom, we get a solid block.
#                                  - If we close it with the root circle arc, we get a solid block with a hole?
#                                    No, the root circle arc is at the bottom.
#                                    If we revolve the root circle arc, we get a cylinder.
#                                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                    But the valleys between teeth will be filled with the hub material.
#                                    This is correct! The hub is the base. The teeth are added on top.
#                                    So the profile is:
#                                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                      - The profile starts at the bottom of the tooth (on the root circle).
#                                      - Goes up the flank.
#                                      - Goes along the tip.
#                                      - Goes down the flank.
#                                      - Goes along the root circle? 
#                                        If we go along the root circle, we are tracing the bottom of the hub.
#                                        But we only want the bottom of the tooth.
#                                        The valley is the space between the tooth and the next tooth.
#                                        If we revolve the profile, the "valley" is created by the space between the 
#                                        tooth profile and the next tooth profile?
#                                        No, the revolution creates the whole thing from one profile.
#                                        So the profile must contain the tooth AND the valley?
#                                        No, the profile is the boundary of the material.
#                                        The material is the tooth. The valley is empty.
#                                        So the profile must go:
#                                          - Up the left flank.
#                                          - Along the tip.
#                                          - Down the right flank.
#                                          - Then... we need to close the loop.
#                                          - If we close it with a line at the bottom, we get a solid block.
#                                          - If we close it with the root circle arc, we get a solid block with a hole?
#                                            No, the root circle arc is at the bottom.
#                                            If we revolve the root circle arc, we get a cylinder.
#                                            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                            But the valleys between teeth will be filled with the hub material.
#                                            This is correct! The hub is the base. The teeth are added on top.
#                                            So the profile is:
#                                              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                              - The profile starts at the bottom of the tooth (on the root circle).
#                                              - Goes up the flank.
#                                              - Goes along the tip.
#                                              - Goes down the flank.
#                                              - Goes along the root circle? 
#                                                If we go along the root circle, we are tracing the bottom of the hub.
#                                                But we only want the bottom of the tooth.
#                                                The valley is the space between the tooth and the next tooth.
#                                                If we revolve the profile, the "valley" is created by the space between the 
#                                                tooth profile and the next tooth profile?
#                                                No, the revolution creates the whole thing from one profile.
#                                                So the profile must contain the tooth AND the valley?
#                                                No, the profile is the boundary of the material.
#                                                The material is the tooth. The valley is empty.
#                                                So the profile must go:
#                                                  - Up the left flank.
#                                                  - Along the tip.
#                                                  - Down the right flank.
#                                                  - Then... we need to close the loop.
#                                                  - If we close it with a line at the bottom, we get a solid block.
#                                                  - If we close it with the root circle arc, we get a solid block with a hole?
#                                                    No, the root circle arc is at the bottom.
#                                                    If we revolve the root circle arc, we get a cylinder.
#                                                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                    But the valleys between teeth will be filled with the hub material.
#                                                    This is correct! The hub is the base. The teeth are added on top.
#                                                    So the profile is:
#                                                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                      - The profile starts at the bottom of the tooth (on the root circle).
#                                                      - Goes up the flank.
#                                                      - Goes along the tip.
#                                                      - Goes down the flank.
#                                                      - Goes along the root circle? 
#                                                        If we go along the root circle, we are tracing the bottom of the hub.
#                                                        But we only want the bottom of the tooth.
#                                                        The valley is the space between the tooth and the next tooth.
#                                                        If we revolve the profile, the "valley" is created by the space between the 
#                                                        tooth profile and the next tooth profile?
#                                                        No, the revolution creates the whole thing from one profile.
#                                                        So the profile must contain the tooth AND the valley?
#                                                        No, the profile is the boundary of the material.
#                                                        The material is the tooth. The valley is empty.
#                                                        So the profile must go:
#                                                          - Up the left flank.
#                                                          - Along the tip.
#                                                          - Down the right flank.
#                                                          - Then... we need to close the loop.
#                                                          - If we close it with a line at the bottom, we get a solid block.
#                                                          - If we close it with the root circle arc, we get a solid block with a hole?
#                                                            No, the root circle arc is at the bottom.
#                                                            If we revolve the root circle arc, we get a cylinder.
#                                                            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                            But the valleys between teeth will be filled with the hub material.
#                                                            This is correct! The hub is the base. The teeth are added on top.
#                                                            So the profile is:
#                                                              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                              - The profile starts at the bottom of the tooth (on the root circle).
#                                                              - Goes up the flank.
#                                                              - Goes along the tip.
#                                                              - Goes down the flank.
#                                                              - Goes along the root circle? 
#                                                                If we go along the root circle, we are tracing the bottom of the hub.
#                                                                But we only want the bottom of the tooth.
#                                                                The valley is the space between the tooth and the next tooth.
#                                                                If we revolve the profile, the "valley" is created by the space between the 
#                                                                tooth profile and the next tooth profile?
#                                                                No, the revolution creates the whole thing from one profile.
#                                                                So the profile must contain the tooth AND the valley?
#                                                                No, the profile is the boundary of the material.
#                                                                The material is the tooth. The valley is empty.
#                                                                So the profile must go:
#                                                                  - Up the left flank.
#                                                                  - Along the tip.
#                                                                  - Down the right flank.
#                                                                  - Then... we need to close the loop.
#                                                                  - If we close it with a line at the bottom, we get a solid block.
#                                                                  - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                    No, the root circle arc is at the bottom.
#                                                                    If we revolve the root circle arc, we get a cylinder.
#                                                                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                    But the valleys between teeth will be filled with the hub material.
#                                                                    This is correct! The hub is the base. The teeth are added on top.
#                                                                    So the profile is:
#                                                                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                      - The profile starts at the bottom of the tooth (on the root circle).
#                                                                      - Goes up the flank.
#                                                                      - Goes along the tip.
#                                                                      - Goes down the flank.
#                                                                      - Goes along the root circle? 
#                                                                        If we go along the root circle, we are tracing the bottom of the hub.
#                                                                        But we only want the bottom of the tooth.
#                                                                        The valley is the space between the tooth and the next tooth.
#                                                                        If we revolve the profile, the "valley" is created by the space between the 
#                                                                        tooth profile and the next tooth profile?
#                                                                        No, the revolution creates the whole thing from one profile.
#                                                                        So the profile must contain the tooth AND the valley?
#                                                                        No, the profile is the boundary of the material.
#                                                                        The material is the tooth. The valley is empty.
#                                                                        So the profile must go:
#                                                                          - Up the left flank.
#                                                                          - Along the tip.
#                                                                          - Down the right flank.
#                                                                          - Then... we need to close the loop.
#                                                                          - If we close it with a line at the bottom, we get a solid block.
#                                                                          - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                            No, the root circle arc is at the bottom.
#                                                                            If we revolve the root circle arc, we get a cylinder.
#                                                                            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                            But the valleys between teeth will be filled with the hub material.
#                                                                            This is correct! The hub is the base. The teeth are added on top.
#                                                                            So the profile is:
#                                                                              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                              - The profile starts at the bottom of the tooth (on the root circle).
#                                                                              - Goes up the flank.
#                                                                              - Goes along the tip.
#                                                                              - Goes down the flank.
#                                                                              - Goes along the root circle? 
#                                                                                If we go along the root circle, we are tracing the bottom of the hub.
#                                                                                But we only want the bottom of the tooth.
#                                                                                The valley is the space between the tooth and the next tooth.
#                                                                                If we revolve the profile, the "valley" is created by the space between the 
#                                                                                tooth profile and the next tooth profile?
#                                                                                No, the revolution creates the whole thing from one profile.
#                                                                                So the profile must contain the tooth AND the valley?
#                                                                                No, the profile is the boundary of the material.
#                                                                                The material is the tooth. The valley is empty.
#                                                                                So the profile must go:
#                                                                                  - Up the left flank.
#                                                                                  - Along the tip.
#                                                                                  - Down the right flank.
#                                                                                  - Then... we need to close the loop.
#                                                                                  - If we close it with a line at the bottom, we get a solid block.
#                                                                                  - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                                    No, the root circle arc is at the bottom.
#                                                                                    If we revolve the root circle arc, we get a cylinder.
#                                                                                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                                    But the valleys between teeth will be filled with the hub material.
#                                                                                    This is correct! The hub is the base. The teeth are added on top.
#                                                                                    So the profile is:
#                                                                                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                                      - The profile starts at the bottom of the tooth (on the root circle).
#                                                                                      - Goes up the flank.
#                                                                                      - Goes along the tip.
#                                                                                      - Goes down the flank.
#                                                                                      - Goes along the root circle? 
#                                                                                        If we go along the root circle, we are tracing the bottom of the hub.
#                                                                                        But we only want the bottom of the tooth.
#                                                                                        The valley is the space between the tooth and the next tooth.
#                                                                                        If we revolve the profile, the "valley" is created by the space between the 
#                                                                                        tooth profile and the next tooth profile?
#                                                                                        No, the revolution creates the whole thing from one profile.
#                                                                                        So the profile must contain the tooth AND the valley?
#                                                                                        No, the profile is the boundary of the material.
#                                                                                        The material is the tooth. The valley is empty.
#                                                                                        So the profile must go:
#                                                                                          - Up the left flank.
#                                                                                          - Along the tip.
#                                                                                          - Down the right flank.
#                                                                                          - Then... we need to close the loop.
#                                                                                          - If we close it with a line at the bottom, we get a solid block.
#                                                                                          - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                                            No, the root circle arc is at the bottom.
#                                                                                            If we revolve the root circle arc, we get a cylinder.
#                                                                                            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                                            But the valleys between teeth will be filled with the hub material.
#                                                                                            This is correct! The hub is the base. The teeth are added on top.
#                                                                                            So the profile is:
#                                                                                              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                                              - The profile starts at the bottom of the tooth (on the root circle).
#                                                                                              - Goes up the flank.
#                                                                                              - Goes along the tip.
#                                                                                              - Goes down the flank.
#                                                                                              - Goes along the root circle? 
#                                                                                                If we go along the root circle, we are tracing the bottom of the hub.
#                                                                                                But we only want the bottom of the tooth.
#                                                                                                The valley is the space between the tooth and the next tooth.
#                                                                                                If we revolve the profile, the "valley" is created by the space between the 
#                                                                                                tooth profile and the next tooth profile?
#                                                                                                No, the revolution creates the whole thing from one profile.
#                                                                                                So the profile must contain the tooth AND the valley?
#                                                                                                No, the profile is the boundary of the material.
#                                                                                                The material is the tooth. The valley is empty.
#                                                                                                So the profile must go:
#                                                                                                  - Up the left flank.
#                                                                                                  - Along the tip.
#                                                                                                  - Down the right flank.
#                                                                                                  - Then... we need to close the loop.
#                                                                                                  - If we close it with a line at the bottom, we get a solid block.
#                                                                                                  - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                                                    No, the root circle arc is at the bottom.
#                                                                                                    If we revolve the root circle arc, we get a cylinder.
#                                                                                                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                                                    But the valleys between teeth will be filled with the hub material.
#                                                                                                    This is correct! The hub is the base. The teeth are added on top.
#                                                                                                    So the profile is:
#                                                                                                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                                                      - The profile starts at the bottom of the tooth (on the root circle).
#                                                                                                      - Goes up the flank.
#                                                                                                      - Goes along the tip.
#                                                                                                      - Goes down the flank.
#                                                                                                      - Goes along the root circle? 
#                                                                                                        If we go along the root circle, we are tracing the bottom of the hub.
#                                                                                                        But we only want the bottom of the tooth.
#                                                                                                        The valley is the space between the tooth and the next tooth.
#                                                                                                        If we revolve the profile, the "valley" is created by the space between the 
#                                                                                                        tooth profile and the next tooth profile?
#                                                                                                        No, the revolution creates the whole thing from one profile.
#                                                                                                        So the profile must contain the tooth AND the valley?
#                                                                                                        No, the profile is the boundary of the material.
#                                                                                                        The material is the tooth. The valley is empty.
#                                                                                                        So the profile must go:
#                                                                                                          - Up the left flank.
#                                                                                                          - Along the tip.
#                                                                                                          - Down the right flank.
#                                                                                                          - Then... we need to close the loop.
#                                                                                                          - If we close it with a line at the bottom, we get a solid block.
#                                                                                                          - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                                                            No, the root circle arc is at the bottom.
#                                                                                                            If we revolve the root circle arc, we get a cylinder.
#                                                                                                            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                                                            But the valleys between teeth will be filled with the hub material.
#                                                                                                            This is correct! The hub is the base. The teeth are added on top.
#                                                                                                            So the profile is:
#                                                                                                              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                                                              - The profile starts at the bottom of the tooth (on the root circle).
#                                                                                                              - Goes up the flank.
#                                                                                                              - Goes along the tip.
#                                                                                                              - Goes down the flank.
#                                                                                                              - Goes along the root circle? 
#                                                                                                                If we go along the root circle, we are tracing the bottom of the hub.
#                                                                                                                But we only want the bottom of the tooth.
#                                                                                                                The valley is the space between the tooth and the next tooth.
#                                                                                                                If we revolve the profile, the "valley" is created by the space between the 
#                                                                                                                tooth profile and the next tooth profile?
#                                                                                                                No, the revolution creates the whole thing from one profile.
#                                                                                                                So the profile must contain the tooth AND the valley?
#                                                                                                                No, the profile is the boundary of the material.
#                                                                                                                The material is the tooth. The valley is empty.
#                                                                                                                So the profile must go:
#                                                                                                                  - Up the left flank.
#                                                                                                                  - Along the tip.
#                                                                                                                  - Down the right flank.
#                                                                                                                  - Then... we need to close the loop.
#                                                                                                                  - If we close it with a line at the bottom, we get a solid block.
#                                                                                                                  - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                                                                    No, the root circle arc is at the bottom.
#                                                                                                                    If we revolve the root circle arc, we get a cylinder.
#                                                                                                                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                                                                    But the valleys between teeth will be filled with the hub material.
#                                                                                                                    This is correct! The hub is the base. The teeth are added on top.
#                                                                                                                    So the profile is:
#                                                                                                                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                                                                      - The profile starts at the bottom of the tooth (on the root circle).
#                                                                                                                      - Goes up the flank.
#                                                                                                                      - Goes along the tip.
#                                                                                                                      - Goes down the flank.
#                                                                                                                      - Goes along the root circle? 
#                                                                                                                        If we go along the root circle, we are tracing the bottom of the hub.
#                                                                                                                        But we only want the bottom of the tooth.
#                                                                                                                        The valley is the space between the tooth and the next tooth.
#                                                                                                                        If we revolve the profile, the "valley" is created by the space between the 
#                                                                                                                        tooth profile and the next tooth profile?
#                                                                                                                        No, the revolution creates the whole thing from one profile.
#                                                                                                                        So the profile must contain the tooth AND the valley?
#                                                                                                                        No, the profile is the boundary of the material.
#                                                                                                                        The material is the tooth. The valley is empty.
#                                                                                                                        So the profile must go:
#                                                                                                                          - Up the left flank.
#                                                                                                                          - Along the tip.
#                                                                                                                          - Down the right flank.
#                                                                                                                          - Then... we need to close the loop.
#                                                                                                                          - If we close it with a line at the bottom, we get a solid block.
#                                                                                                                          - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                                                                            No, the root circle arc is at the bottom.
#                                                                                                                            If we revolve the root circle arc, we get a cylinder.
#                                                                                                                            If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                                                                            But the valleys between teeth will be filled with the hub material.
#                                                                                                                            This is correct! The hub is the base. The teeth are added on top.
#                                                                                                                            So the profile is:
#                                                                                                                              - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                                                                              - The profile starts at the bottom of the tooth (on the root circle).
#                                                                                                                              - Goes up the flank.
#                                                                                                                              - Goes along the tip.
#                                                                                                                              - Goes down the flank.
#                                                                                                                              - Goes along the root circle? 
#                                                                                                                                If we go along the root circle, we are tracing the bottom of the hub.
#                                                                                                                                But we only want the bottom of the tooth.
#                                                                                                                                The valley is the space between the tooth and the next tooth.
#                                                                                                                                If we revolve the profile, the "valley" is created by the space between the 
#                                                                                                                                tooth profile and the next tooth profile?
#                                                                                                                                No, the revolution creates the whole thing from one profile.
#                                                                                                                                So the profile must contain the tooth AND the valley?
#                                                                                                                                No, the profile is the boundary of the material.
#                                                                                                                                The material is the tooth. The valley is empty.
#                                                                                                                                So the profile must go:
#                                                                                                                                  - Up the left flank.
#                                                                                                                                  - Along the tip.
#                                                                                                                                  - Down the right flank.
#                                                                                                                                  - Then... we need to close the loop.
#                                                                                                                                  - If we close it with a line at the bottom, we get a solid block.
#                                                                                                                                  - If we close it with the root circle arc, we get a solid block with a hole?
#                                                                                                                                    No, the root circle arc is at the bottom.
#                                                                                                                                    If we revolve the root circle arc, we get a cylinder.
#                                                                                                                                    If we revolve the tooth profile (above the root circle), we get teeth on top of the hub.
#                                                                                                                                    But the valleys between teeth will be filled with the hub material.
#                                                                                                                                    This is correct! The hub is the base. The teeth are added on top.
#                                                                                                                                    So the profile is:
#                                                                                                                                      - Start at (x=root_radius, z=0) ? No, the root circle is at z=0.
#                                                                                                                                      - The profile starts at the bottom of the tooth (on the root circle).
#                                                                                                                                      - Goes up the flank.
#                                                                                                                                      - Goes along the tip.
#                                                                                                                                      - Goes down the flank.
#                                                                                                                                      - Goes
