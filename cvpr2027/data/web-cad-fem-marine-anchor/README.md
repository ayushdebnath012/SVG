# Published complex marine anchor CAD/FEM extension

One modular helical anchor family with native DesignModeler CAD and three saved static ANSYS load sets. Source: https://data.openei.org/submissions/8695 (MHKDR 697), Carlos Lopez, Hong Zhou, Dilip Maniar / Stress Engineering Services; CC BY 4.0. Original 208.68 MiB Initial Anchor Analysis.wbpz includes 381681664-byte file.rst, SYS.agdb, ds.dat and solve.out. Source log states DISTRIBUTED ANSYS RUN COMPLETED.

The AGDB is HDF5 with serialized Parasolid and native object data. Original SolidWorks/Parasolid design files also downloaded. No original STEP found in selected files and no independent native BREP import completed. Native CAD is present; geometry validity/case correspondence is not certified.

Read saved RST with ansys-mapdl-reader 0.56.0 without launching ANSYS or any FEM solve: 407855 mesh nodes, 150143 elements, 3 result sets. Each displacement table has 6 DOFs and all finite values. Extracted NPZs retain original node IDs, mesh coordinates and displacement/stress arrays unchanged. Translation uses the first three DOFs. Source input units imply inch and psi; binary header says User Defined.

Stress extraction contains fully finite rows at 89139 nodes and missing rows at 318716 nodes. Preserve the NaN mask; do not score missing nodes as zero stress. Region/element-support mapping remains to be checked. The labels 1,2,3 are static result/load-step labels, not a transient time series.

The original DOE CSV has 92 finite rows, but separate native CAD files are not provided/matched for every row. These are not 92 new CAD/FEM pairs. Selected design CAD variants must not be assumed paired to the baseline RST. The optimized 2.23GB Workbench archive has not been downloaded.

ZIP includes original Workbench and ancillary source archives, original CAD variants and exact extracted NPZ fields plus provenance/audits. Raw RST and baseline CAD can be extracted from the Workbench archive at members recorded in catalog.json; expanded duplicate raw RST is omitted from the share ZIP to avoid copying the same data twice.

Report CAD images are unchanged publisher figures; field plots show saved reference values only. No CAD, FEM solution, model trial or benchmark question generated locally. No COMSOL used. One candidate family, zero benchmark-certified admissions, no newly verified original dimensioned drawing.
