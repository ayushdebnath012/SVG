# Published rigging plate collection

One original geometry with seven published loading variants. Original source README.md and LICENSE are untouched. STEP imports as one valid solid with 145 faces; millimetre extents agree with the original drawing. Original drawing PDF, SolidWorks source, STEP, all 28 load/result PNGs and overview retained. No original raw saved result file or solver input deck found.

catalog.json records 21 original plot scalar labels (seven peak von Mises stress, seven peak total deformation, seven minimum safety factor) with file/hash provenance. They are FEM reference values, not frontier-model scores. Images and rounded labels cannot support nodal field-error scoring. No CAD generation, solver execution or model call performed.

Known source discrepancies: Test4 load differs between README and folder; plotted Tests1/4/7 safety factors fall below one despite README's passed statement; nonzero minimum total displacement in Tests1/5 needs support/rotation review. Source strength labels are not verified experimental breaking loads. Seven variants count as one geometry family. Zero certified benchmark admissions. No COMSOL required.

Original source: https://github.com/mpangch/OpenRiggingPlate, pinned revision in download-manifest.json. CERN-OHL-S-2.0 source license retained. CAD validity does not establish physical correctness of the reference simulation.
