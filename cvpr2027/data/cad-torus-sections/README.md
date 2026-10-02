# Toroidal-pipe section discovery

Two adaptive CAD tasks (generation/editing) added after the six gear/cam/manifold
cases passed. The requested object is hollow curved pipe with a drilled access
port, cut by an oblique plane; boundaries are non-conic. The geometry is defined
by solid membership in XYZ, with an explicit plane basis. No flow or FEM plot.

The prompt/reference/policy manifest was frozen before calls. The original
0.5 mm geometric tolerance remains unchanged. Both Astra screening outputs
passed and therefore are not candidates for repeated-failure confirmation.
A separate precision requirement has a separate manifest and prompts; it cannot
change these results.

Reference material masks use the implicit torus and cylinder equations. Contour
exports use numerical tracing plus bounded polygon simplification. Tests include
a closed-form horizontal annular section, refined implicit boundary residuals,
rendered export versus solid membership, and detection of a stale edit.
