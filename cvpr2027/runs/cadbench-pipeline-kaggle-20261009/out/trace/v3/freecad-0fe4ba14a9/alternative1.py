import FreeCAD as App
import Part
from pathlib import Path
import Sketcher
import math

# --- Configuration ---
# Parameters defined at the top of the script for clarity, 
# though they will also be stored in the document objects.
config = {
    "rod_outer_diameter": 30.0,
    "rod_cross_section_length": 30.0,
    "rod_cross_section_width": 30.0,
    "rod_end_body_length": 40.0,
    "rectangular_slot_width": 7.0,
    "rectangular_slot_count": 3,
    "spacing_distance_between_rectangular_slots": 15.0,
    "first_slot_left_edge_x_offset": 210.0,
    "clevis_pin_hole_diameter": 15.0,
    "clevis_slot_end_arc_radius": 15.66,
    "clevis_slot_end_arc_center_x": -233.58
}

# --- Document Setup ---
doc = App.newDocument("LinkageRod")
doc.Label = "LinkageRod"

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# --- Feature 1: Main Cylindrical Stock ---
# We create a full cylinder that encompasses the entire part length.
# Length = 2 * (distance to end of lugs)
# End of lugs X = clevis_slot_end_arc_center_x (negative) + radius (positive? No, center is negative, radius extends to positive side)
# Wait, the description says "left semicircle is centered on the rod axis at X = clevis_slot_end_arc_center_x".
# clevis_slot_end_arc_center_x = -233.58.
# The arc radius is 15.66.
# So the arc spans from X = -233.58 - 15.66 to X = -233.58 + 15.66? 
# Usually "end of part" implies the tip. If the center is at -233.58 and it's a "rounded end", the tip is likely at -233.58 - 15.66 = -249.24.
# The other end is symmetric about X=0, so tip at +249.24.
# Total length needed = 498.48 mm.

# Let's define the "End X" coordinate explicitly based on the parameters.
# Left Center X = -233.58. Radius = 15.66.
# Tip X (Left) = -233.58 - 15.66 = -249.24.
# Tip X (Right) = 249.24.
# Total Length = 498.48.
# Note: The slot starts at first_slot_left_edge_x_offset = 210.0.
# 210 < 249.24, so the slots are within the rounded region logic or near it.
# The prompt says "extends outward beyond the rounded end". 
# 210 is less than 249.24. Wait. 
# If the center is -233.58, and the radius is 15.66, the circle equation is (x - (-233.58))^2 + y^2 <= R^2.
# The max X on this circle is -233.58 + 15.66 = -217.92.
# The prompt says "extends outward beyond the rounded end". 
# If the slot starts at X = 210, it is on the positive side.
# Let's re-read carefully: "The left semicircle is centered on the rod axis at X = clevis_slot_end_arc_center_x".
# "extends outward beyond the rounded end".
# If the left end is the rounded one, and the slot extends *beyond* it, the slot must be at X < -217.92?
# But the parameter is "first_slot_left_edge_x_offset = 210.0". This is positive.
# This implies the "Left" in the parameter name might refer to the left side of the *slot sequence* or the prompt implies the part is oriented differently, OR the "Left" end is actually at positive X?
# Let's look at the symmetry: "two ends are symmetric about the plane X = 0".
# If Left Center = -233.58, Right Center = +233.58.
# Left Tip = -249.24. Right Tip = +249.24.
# Slot start X = 210. This is on the Right side (between 0 and 249.24).
# Why does the prompt say "extends outward beyond the rounded end"? 
# Maybe the "Left" end is the one at Positive X? No, "Left" usually means negative.
# Let's reconsider the "Left" vs "Right" naming in the prompt vs standard conventions.
# If the slot starts at +210, it is near the Right end (Tip +249).
# If the prompt says "extends outward beyond the rounded end", maybe the rounded end is at X > 210? 
# If the center is -233.58, the circle is entirely in negative X.
# If the slot is at +210, it is nowhere near the left rounded end.
# Hypothesis: The prompt description "left semicircle... at X = -233.58" defines the geometry.
# The slot "extends outward beyond the rounded end" might be a description of the slot's *action* relative to the *other* end? 
# OR, more likely, the prompt implies the slot starts at X=210, goes to the right, and the rounded end is at X > 210?
# If the rounded end is at X > 210, then the center must be > 210.
# But the parameter `clevis_slot_end_arc_center_x` is explicitly -233.58.
# This is a contradiction in the text provided vs the numbers.
# However, the prompt also says: "The three cutting profiles are centered at Z = -15, 0, and 15 mm...".
# And "first_slot_left_edge_x_offset = 210.0".
# Let's assume the numbers are the ground truth for the geometry construction.
# Geometry:
# 1. Main Cylinder: Length 498.48 (-249.24 to +249.24).
# 2. Slots: Start at X = 210.
# If the slot starts at 210, it is inside the cylinder (since 210 < 249.24).
# Does it extend "beyond" the rounded end? 
# If the rounded end is at +249.24, the slot (starting at 210) is inside.
# Maybe "extends outward" means the slot width goes past the boundary of the *root* of the lug?
# Let's just follow the coordinates.
# Slot Left Edge X = 210.
# Slot Width = 7.
# Slot Right Edge X = 217.
# This is a short slot near the right end.
# What about the "extends outward beyond the rounded end" phrase? 
# Perhaps the "rounded end" refers to the *transition*? 
# Or maybe I should interpret "Left" in "first_slot_left_edge" as "Left edge of the slot".
# Yes, "first_slot_left_edge_x_offset" likely means the X-coordinate of the left edge of the first slot.
# So Slot X range: [210, 217].
# This is well within the Right tip [0, 249.24].
# Does it "extend beyond the rounded end"? 
# If the rounded end is the *transition* region? No, the transition is at the ends.
# Maybe the "rounded end" is the *start* of the lug? 
# Let's ignore the confusing textual description of "beyond" if the numbers don't align, and trust the numbers.
# BUT, wait. "extends outward beyond the rounded end" might mean the slot goes *outside* the cylinder? 
# "Each cut starts at the absolute X distance... extends outward beyond the rounded end".
# If the cylinder ends at 249.24, and the slot is 210-217, it is inside.
# Unless the cylinder is longer? 
# "The cylindrical material envelope applies to the entire finished part".
# If the slot extends *beyond* the rounded end, it must go past X=249.24.
# If the slot starts at 210 and has width 7, it ends at 217. That's not beyond 249.
# Is it possible the slot is *vertical*? "rectangular cutting profiles... transverse".
# "Each cut starts at the absolute X distance... extends outward".
# Maybe the slot is along Y? No, "transverse" usually means perpendicular to the main axis (X).
# Let's re-read the slot centering: "centered as a group about Z = 0".
# "The central profile creates one complete 7 mm slot." -> Z range -3.5 to 3.5.
# "The outer two profiles intersect only the lower and upper surfaces". -> Z range -18.5 to -11.5 and 11.5 to 18.5.
# These are transverse cuts (along Y axis) at specific X locations.
# If the slot is at X=210 to 217, it is a chunk of material removed.
# Why "extends beyond the rounded end"?
# Maybe the "rounded end" is at X = 217? No, the arc center is -233.
# Maybe the prompt implies the part is reversed? 
# If Center = -233.58, and Radius = 15.66.
# Circle: (x + 233.58)^2 + y^2 = 15.66^2.
# Max X = -217.92. Min X = -249.24.
# Slot at X=210 is far away.
# Could "clevis_slot_end_arc_center_x" be the center of the *Right* end? 
# "The left semicircle is centered on the rod axis at X = clevis_slot_end_arc_center_x".
# If the left end is at -233.58, the right end is at +233.58.
# Slot at +210 is near the Right end.
# Maybe the description "extends outward beyond the rounded end" applies to the *other* end?
# Or maybe the "Left" slot is actually at X = -210? 
# But the parameter is `first_slot_left_edge_x_offset = 210.0`.
# Let's assume the parameter value 210 is the X coordinate.
# And let's assume the description "extends outward beyond the rounded end" is either:
# 1. Referring to the slot extending past the *transition* region into the lug.
# 2. A slightly inaccurate description where the slot is just inside the tip.
# 3. Implying the slot goes from 210 to 217, and the "rounded end" is considered to be at 210? No.
# 
# Let's consider the "symmetric about X=0" part.
# If there is a slot at +210, there must be a slot at -210?
# "At each end, ... subtract rectangular_slot_count parallel transverse rectangular cutting profiles."
# "Each cut starts at the absolute X distance first_slot_left_edge_x_offset from the origin".
# Does "absolute X distance" mean |X|? Or just the coordinate value?
# "extends outward beyond the rounded end".
# If the left end is at -249, and the slot is at -210 (symmetric to +210), then the slot is at -210 to -203.
# This is also inside the cylinder (-249 to -217.92 tip).
# Wait, -203 is > -217.92. So -203 is *outside* the rounded end circle?
# Yes! The rounded end (left) ends at -217.92. The slot at -203 is further right (towards center).
# So the slot is *inside* the cylinder, but maybe "beyond the rounded end" means beyond the *start* of the rounded end?
# No, "beyond the end" usually means past the tip.
# 
# Let's try a different interpretation:
# Maybe the "Left" end is the one at Positive X? (Unlikely).
# Maybe the "rounded end" is not the tip of the cylinder?
# "An outward-facing semicircle... defines the rounded trimming boundary".
# This confirms the tip is the semicircle.
# 
# Let's reconsider the "extends outward beyond the rounded end" phrase.
# Could it mean the slot *width* extends beyond the boundary of the lug *root*?
# Or maybe the slot *starts* at 210 and goes *outward* (in the direction of the end)?
# If the end is at +249, outward is +X.
# Slot: 210 -> 217.
# This is "inward" from the tip (249).
# 
# Is it possible the parameter `clevis_slot_end_arc_center_x` is actually the *tip* coordinate?
# No, it says "centered ... at X = ...".
# 
# Let's look at the numbers again.
# Tip X = 249.24.
# Slot X = 210.
# Gap = 39 mm.
# This seems like a reasonable location for a slot on a lug.
# The phrase "extends outward beyond the rounded end" is the only thing that doesn't fit.
# However, "extends outward" could describe the *cut* direction? No, it's transverse.
# Maybe it means "extends outward [from the center] beyond the [start of the] rounded end"?
# Start of rounded end = -217.92 (Left) and +217.92 (Right).
# Slot at +210 is just inside +217.92.
# Slot at -210 is just inside -217.92.
# So the slots are located in the region where the cylinder *starts* to round off?
# Yes! The cylinder is straight until X = +/- 217.92, then it rounds.
# The slots are at +/- 210.
# So the slots are *inside* the straight section, near the transition.
# "extends outward beyond the rounded end" -> Maybe "extends outward [from the center] to the [region of the] rounded end"?
# Or maybe the prompt implies the slot *overlaps* the rounded end?
# If the slot was at 220, it would be on the rounded end.
# But 210 is safe.
# 
# Okay, I will proceed with the explicit numbers:
# Slot X position: 210.
# Slot Width: 7.
# Slot is a transverse cut (along Y).
# 
# Wait, "extends outward beyond the rounded end" might mean the slot *continues* past the rounded end?
# If the slot is a "cutting profile", maybe it's not a through-cut?
# "passes completely across Y". It is a through-cut.
# If it's a through-cut, it removes material from X=210 to X=217.
# This does not remove material at X=249.
# Unless... the slot is *longitudinal*?
# "rectangular_slot_count parallel transverse rectangular cutting profiles".
# Transverse means perpendicular to the rod axis.
# So it's a slice at X=210.
# 
# Let's assume the text "extends outward beyond the rounded end" is a distractor or poorly phrased, and the numbers (210, 7) are the truth.
# Also, "The outer two profiles intersect only the lower and upper surfaces".
# Cylinder diameter = 30. Radius = 15.
# Slot Z centers: -18.5, 0, 18.5. Width 7.
# Z ranges: [-18.5, -11.5], [-3.5, 3.5], [11.5, 18.5].
# Cylinder Z range: [-15, 15].
# Central slot [-3.5, 3.5] is inside [-15, 15]. -> Complete slot.
# Outer slots: [-18.5, -11.5]. Overlap with [-15, 15] is [-15, -11.5].
# This creates a "surface cut" (partial depth).
# This matches the description perfectly.
# So the geometry is consistent with the numbers.
# The only confusing part is "extends outward beyond the rounded end".
# Given the slot is at 210 and the rounded end starts at 217.92, the slot is *just before* the rounded end begins.
# Perhaps "beyond" means "towards the end"?
# Regardless, the numeric parameters define the CAD model.

# --- Planes ---
# We need planes for:
# 1. Base Sketch (XY plane at X=0) -> Pad to make the full cylinder.
# 2. End Sketches (YZ planes
