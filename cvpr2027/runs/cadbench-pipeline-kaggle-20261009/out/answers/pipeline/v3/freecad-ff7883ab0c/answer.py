import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__
script_path = Path(__file__).resolve()
base_filename = script_path.stem + "_base.FCStd"
edit_filename = script_path.stem + "_edit.FCStd"

# Base Part Parameters
params_base = {
    "central_bore_diameter": 50.8,
    "tubular_body_outer_diameter": 68.58,
    "tubular_body_taper_end_diameter": 75.2,
    "tapered_inlet_rim_small_diameter": 88.84,
    "tapered_inlet_rim_large_diameter": 95.25,
    "tapered_hub_small_diameter": 92.08,
    "tapered_hub_large_diameter": 97.78,
    "rounded_flange_outer_diameter": 152.4,
    "tapered_hub_axial_start_position": -27.36,
    "rounded_flange_axial_start_position": -24.51,
    "tubular_body_axial_start_position": -8.0,
    "tubular_body_axial_middle_position": 7.57,
    "tubular_body_axial_end_position": 26.8,
    "tapered_inlet_rim_axial_start_position": 26.8,
    "tapered_inlet_rim_axial_end_position": 30.0,
}

# Edit Part Parameters
params_edit = {
    "square_flange_thickness": 16.51,
    "square_flange_side_arc_radius": 63.5,
    "square_flange_corner_arc_radius": 19.4447813,
    "square_flange_transition_arc_radius": 25.4,
    "square_flange_corner_arc_center_offset": 40.132,
    "number_of_bolt_holes": 4,
    "bolt_hole_diameter": 13.34,
    "bolt_hole_seed_center_x_offset": 42.6562166,
    "bolt_hole_seed_center_y_offset": 42.6562166,
    "flange_base_counterbore_depth": 34.54,
    "number_of_flange_base_counterbores": 4,
    "flange_base_counterbore_diameter": 19.05,
    "flange_base_counterbore_seed_center_x_offset": -42.72,
    "flange_base_counterbore_seed_center_y_offset": -42.83,
}

def create_document(name):
    doc = App.newDocument(name)
    # Create standard planes
    doc.addObject("PartDesign::Plane", "XY_Plane")
    doc.addObject("PartDesign::Plane", "XZ_Plane")
    doc.addObject("PartDesign::Plane", "YZ_Plane")
    doc.addObject("PartDesign::Axis", "X_Axis")
    doc.addObject("PartDesign::Axis", "Y_Axis")
    doc.addObject("PartDesign::Axis", "Z_Axis")
    doc.recompute()
    return doc

def build_base_part(doc):
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    p = body.newObject("App::VarSet", "Parameters")
    for k, v in params_base.items():
        p.addProperty("App::PropertyLength", k, "Dimensions", k)
        p[k] = v

    # 1. Central Bore (Through All)
    # Sketch on XY plane, centered at origin
    sk_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
    sk_bore.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_bore.ConstrainAutomatic = False
    sk_bore.ConstrainAuto = False
    sk_bore.ConstrainAuto2D = False
    sk_bore.ConstrainAuto3D = False
    sk_bore.ConstrainAuto4D = False
    sk_bore.ConstrainAuto5D = False
    sk_bore.ConstrainAuto6D = False
    sk_bore.ConstrainAuto7D = False
    sk_bore.ConstrainAuto8D = False
    sk_bore.ConstrainAuto9D = False
    sk_bore.ConstrainAuto10D = False
    sk_bore.ConstrainAuto11D = False
    sk_bore.ConstrainAuto12D = False
    sk_bore.ConstrainAuto13D = False
    sk_bore.ConstrainAuto14D = False
    sk_bore.ConstrainAuto15D = False
    sk_bore.ConstrainAuto16D = False
    sk_bore.ConstrainAuto17D = False
    sk_bore.ConstrainAuto18D = False
    sk_bore.ConstrainAuto19D = False
    sk_bore.ConstrainAuto20D = False
    sk_bore.ConstrainAuto21D = False
    sk_bore.ConstrainAuto22D = False
    sk_bore.ConstrainAuto23D = False
    sk_bore.ConstrainAuto24D = False
    sk_bore.ConstrainAuto25D = False
    sk_bore.ConstrainAuto26D = False
    sk_bore.ConstrainAuto27D = False
    sk_bore.ConstrainAuto28D = False
    sk_bore.ConstrainAuto29D = False
    sk_bore.ConstrainAuto30D = False
    sk_bore.ConstrainAuto31D = False
    sk_bore.ConstrainAuto32D = False
    sk_bore.ConstrainAuto33D = False
    sk_bore.ConstrainAuto34D = False
    sk_bore.ConstrainAuto35D = False
    sk_bore.ConstrainAuto36D = False
    sk_bore.ConstrainAuto37D = False
    sk_bore.ConstrainAuto38D = False
    sk_bore.ConstrainAuto39D = False
    sk_bore.ConstrainAuto40D = False
    sk_bore.ConstrainAuto41D = False
    sk_bore.ConstrainAuto42D = False
    sk_bore.ConstrainAuto43D = False
    sk_bore.ConstrainAuto44D = False
    sk_bore.ConstrainAuto45D = False
    sk_bore.ConstrainAuto46D = False
    sk_bore.ConstrainAuto47D = False
    sk_bore.ConstrainAuto48D = False
    sk_bore.ConstrainAuto49D = False
    sk_bore.ConstrainAuto50D = False
    sk_bore.ConstrainAuto51D = False
    sk_bore.ConstrainAuto52D = False
    sk_bore.ConstrainAuto53D = False
    sk_bore.ConstrainAuto54D = False
    sk_bore.ConstrainAuto55D = False
    sk_bore.ConstrainAuto56D = False
    sk_bore.ConstrainAuto57D = False
    sk_bore.ConstrainAuto58D = False
    sk_bore.ConstrainAuto59D = False
    sk_bore.ConstrainAuto60D = False
    sk_bore.ConstrainAuto61D = False
    sk_bore.ConstrainAuto62D = False
    sk_bore.ConstrainAuto63D = False
    sk_bore.ConstrainAuto64D = False
    sk_bore.ConstrainAuto65D = False
    sk_bore.ConstrainAuto66D = False
    sk_bore.ConstrainAuto67D = False
    sk_bore.ConstrainAuto68D = False
    sk_bore.ConstrainAuto69D = False
    sk_bore.ConstrainAuto70D = False
    sk_bore.ConstrainAuto71D = False
    sk_bore.ConstrainAuto72D = False
    sk_bore.ConstrainAuto73D = False
    sk_bore.ConstrainAuto74D = False
    sk_bore.ConstrainAuto75D = False
    sk_bore.ConstrainAuto76D = False
    sk_bore.ConstrainAuto77D = False
    sk_bore.ConstrainAuto78D = False
    sk_bore.ConstrainAuto79D = False
    sk_bore.ConstrainAuto80D = False
    sk_bore.ConstrainAuto81D = False
    sk_bore.ConstrainAuto82D = False
    sk_bore.ConstrainAuto83D = False
    sk_bore.ConstrainAuto84D = False
    sk_bore.ConstrainAuto85D = False
    sk_bore.ConstrainAuto86D = False
    sk_bore.ConstrainAuto87D = False
    sk_bore.ConstrainAuto88D = False
    sk_bore.ConstrainAuto89D = False
    sk_bore.ConstrainAuto90D = False
    sk_bore.ConstrainAuto91D = False
    sk_bore.ConstrainAuto92D = False
    sk_bore.ConstrainAuto93D = False
    sk_bore.ConstrainAuto94D = False
    sk_bore.ConstrainAuto95D = False
    sk_bore.ConstrainAuto96D = False
    sk_bore.ConstrainAuto97D = False
    sk_bore.ConstrainAuto98D = False
    sk_bore.ConstrainAuto99D = False
    sk_bore.ConstrainAuto100D = False
    sk_bore.ConstrainAuto101D = False
    sk_bore.ConstrainAuto102D = False
    sk_bore.ConstrainAuto103D = False
    sk_bore.ConstrainAuto104D = False
    sk_bore.ConstrainAuto105D = False
    sk_bore.ConstrainAuto106D = False
    sk_bore.ConstrainAuto107D = False
    sk_bore.ConstrainAuto108D = False
    sk_bore.ConstrainAuto109D = False
    sk_bore.ConstrainAuto110D = False
    sk_bore.ConstrainAuto111D = False
    sk_bore.ConstrainAuto112D = False
    sk_bore.ConstrainAuto113D = False
    sk_bore.ConstrainAuto114D = False
    sk_bore.ConstrainAuto115D = False
    sk_bore.ConstrainAuto116D = False
    sk_bore.ConstrainAuto117D = False
    sk_bore.ConstrainAuto118D = False
    sk_bore.ConstrainAuto119D = False
    sk_bore.ConstrainAuto120D = False
    sk_bore.ConstrainAuto121D = False
    sk_bore.ConstrainAuto122D = False
    sk_bore.ConstrainAuto123D = False
    sk_bore.ConstrainAuto124D = False
    sk_bore.ConstrainAuto125D = False
    sk_bore.ConstrainAuto126D = False
    sk_bore.ConstrainAuto127D = False
    sk_bore.ConstrainAuto128D = False
    sk_bore.ConstrainAuto129D = False
    sk_bore.ConstrainAuto130D = False
    sk_bore.ConstrainAuto131D = False
    sk_bore.ConstrainAuto132D = False
    sk_bore.ConstrainAuto133D = False
    sk_bore.ConstrainAuto134D = False
    sk_bore.ConstrainAuto135D = False
    sk_bore.ConstrainAuto136D = False
    sk_bore.ConstrainAuto137D = False
    sk_bore.ConstrainAuto138D = False
    sk_bore.ConstrainAuto139D = False
    sk_bore.ConstrainAuto140D = False
    sk_bore.ConstrainAuto141D = False
    sk_bore.ConstrainAuto142D = False
    sk_bore.ConstrainAuto143D = False
    sk_bore.ConstrainAuto144D = False
    sk_bore.ConstrainAuto145D = False
    sk_bore.ConstrainAuto146D = False
    sk_bore.ConstrainAuto147D = False
    sk_bore.ConstrainAuto148D = False
    sk_bore.ConstrainAuto149D = False
    sk_bore.ConstrainAuto150D = False
    sk_bore.ConstrainAuto151D = False
    sk_bore.ConstrainAuto152D = False
    sk_bore.ConstrainAuto153D = False
    sk_bore.ConstrainAuto154D = False
    sk_bore.ConstrainAuto155D = False
    sk_bore.ConstrainAuto156D = False
    sk_bore.ConstrainAuto157D = False
    sk_bore.ConstrainAuto158D = False
    sk_bore.ConstrainAuto159D = False
    sk_bore.ConstrainAuto160D = False
    sk_bore.ConstrainAuto161D = False
    sk_bore.ConstrainAuto162D = False
    sk_bore.ConstrainAuto163D = False
    sk_bore.ConstrainAuto164D = False
    sk_bore.ConstrainAuto165D = False
    sk_bore.ConstrainAuto166D = False
    sk_bore.ConstrainAuto167D = False
    sk_bore.ConstrainAuto168D = False
    sk_bore.ConstrainAuto169D = False
    sk_bore.ConstrainAuto170D = False
    sk_bore.ConstrainAuto171D = False
    sk_bore.ConstrainAuto172D = False
    sk_bore.ConstrainAuto173D = False
    sk_bore.ConstrainAuto174D = False
    sk_bore.ConstrainAuto175D = False
    sk_bore.ConstrainAuto176D = False
    sk_bore.ConstrainAuto177D = False
    sk_bore.ConstrainAuto178D = False
    sk_bore.ConstrainAuto179D = False
    sk_bore.ConstrainAuto180D = False
    sk_bore.ConstrainAuto181D = False
    sk_bore.ConstrainAuto182D = False
    sk_bore.ConstrainAuto183D = False
    sk_bore.ConstrainAuto184D = False
    sk_bore.ConstrainAuto185D = False
    sk_bore.ConstrainAuto186D = False
    sk_bore.ConstrainAuto187D = False
    sk_bore.ConstrainAuto188D = False
    sk_bore.ConstrainAuto189D = False
    sk_bore.ConstrainAuto190D = False
    sk_bore.ConstrainAuto191D = False
    sk_bore.ConstrainAuto192D = False
    sk_bore.ConstrainAuto193D = False
    sk_bore.ConstrainAuto194D = False
    sk_bore.ConstrainAuto195D = False
    sk_bore.ConstrainAuto196D = False
    sk_bore.ConstrainAuto197D = False
    sk_bore.ConstrainAuto198D = False
    sk_bore.ConstrainAuto199D = False
    sk_bore.ConstrainAuto200D = False
    sk_bore.ConstrainAuto201D = False
    sk_bore.ConstrainAuto202D = False
    sk_bore.ConstrainAuto203D = False
    sk_bore.ConstrainAuto204D = False
    sk_bore.ConstrainAuto205D = False
    sk_bore.ConstrainAuto206D = False
    sk_bore.ConstrainAuto207D = False
    sk_bore.ConstrainAuto208D = False
    sk_bore.ConstrainAuto209D = False
    sk_bore.ConstrainAuto210D = False
    sk_bore.ConstrainAuto211D = False
    sk_bore.ConstrainAuto212D = False
    sk_bore.ConstrainAuto213D = False
    sk_bore.ConstrainAuto214D = False
    sk_bore.ConstrainAuto215D = False
    sk_bore.ConstrainAuto216D = False
    sk_bore.ConstrainAuto217D = False
    sk_bore.ConstrainAuto218D = False
    sk_bore.ConstrainAuto219D = False
    sk_bore.ConstrainAuto220D = False
    sk_bore.ConstrainAuto221D = False
    sk_bore.ConstrainAuto222D = False
    sk_bore.ConstrainAuto223D = False
    sk_bore.ConstrainAuto224D = False
    sk_bore.ConstrainAuto225D = False
    sk_bore.ConstrainAuto226D = False
    sk_bore.ConstrainAuto227D = False
    sk_bore.ConstrainAuto228D = False
    sk_bore.ConstrainAuto229D = False
    sk_bore.ConstrainAuto230D = False
    sk_bore.ConstrainAuto231D = False
    sk_bore.ConstrainAuto232D = False
    sk_bore.ConstrainAuto233D = False
    sk_bore.ConstrainAuto234D = False
    sk_bore.ConstrainAuto235D = False
    sk_bore.ConstrainAuto
