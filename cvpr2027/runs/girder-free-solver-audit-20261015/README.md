# Plate-girder solver audit

No API calls. Original Astra-authored C3D20R level_0 mesh, material and supports unchanged. All nodal loads scaled by 0.1. CalculiX 2.23 run with OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, CCX_NPROC_STIFFNESS=1, CCX_NPROC_EQUATION_SOLVER=1. Completed in 145 seconds.

First diagnostic factor 4.063106 maps to 0.4063106 at original loading, -1.359% from source 0.41191; within 5%. Original solver returned 1.873548 and skipped this earlier mode. Load scaling and threading were changed together, so attribution to either alone remains unisolated. Matches symptoms reported in CalculiX issue #74.

Remove this case from confirmed persistent capability failures. This evaluator intervention does not count as an unmodified Astra success. Original runs preserved. See audit.json for input hashes. model.inc is a symlink to frozen original mesh.
