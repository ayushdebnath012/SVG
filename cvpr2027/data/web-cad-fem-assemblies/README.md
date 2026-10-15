# Web CAD/FEM frame and kiteboard extension

One native FreeCAD model with embedded numerical CalculiX fields (2356 verified node IDs); one composite kiteboard CAD candidate with published Ansys FEM plots and maximum inverse reserve factor 1.0099. These are two different task families. Neither is benchmark-certified. Catalog records primary source links, hashes, CAD audits and limitations.

No local CAD or FEM solution generation. CAD PNGs inspect original BREP/STEP; frame CSV extracts unchanged saved values and source node IDs. Original frame loads include self-weight and prescribed X displacement -19. The four tiny external FRD test runs use a different mesh and are not paired to the frame or counted as cases. No model trials or accuracy scores.

The Kiteboard SOLVED archive explicitly skips raw result/deck files; its candidate reference is published plots/scalar, not a full numerical field dataset. Native shell CAD and separate core are retained. Version matching and scalar tolerance require review before scoring. No COMSOL dependency; kiteboard replay requires Ansys Mechanical/ACP.

Other downloaded ACP archives are held separately in ../web-cad-fem-acp with archive inventories; no saved raw numerical FEM fields verified. Source copyrights/data-license status in catalog. This is a local research collection; no repository commits or public release performed.
