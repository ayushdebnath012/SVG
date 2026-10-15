# Task contract (complex CAD + FEM tasks)

Units: millimetres, newtons, MPa unless the task says otherwise. Task input files are read-only in CADFEM_INPUT_DIR.

Deliver main.py (helper .py files allowed). `python main.py` must regenerate, in the working directory, every file the
task asks for: always `results.json`, shaped exactly as the task states, and `part.step` when the task asks for a part.
Only the files written by that clean re-run are graded; numbers alone are not enough, and parts are checked by an
independent finite element analysis. Check your own work (mesh convergence, units, boundary conditions, output keys)
before submitting.
