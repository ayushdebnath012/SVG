# Hard CAD geometry discovery pool

Six new tasks: generate/edit an ideal involute gear with keyway, a cycloidal
roller-follower plate cam, and the oblique section of a drilled manifold.
Previous passing table/building/shelf/simple-plate tasks are not rerun here.
This pool is procedural, inspired by relevant CAD task categories. It is NOT
represented as samples imported from a published dataset.

Prompts, complete geometry definitions, tolerances and reference hashes were
frozen before the first API request. Screen configuration is Astra medium,
16,000 completion tokens, one sample per task. Substantive drawing failures are
repeated twice at high effort, 32,000 tokens. Admission needs three evaluable
samples (two high), at least two substantive drawing failures (one high), and
identified visual/evidence review. Budget/format/API failures do not qualify.
Passing tasks are discarded from the selected challenge set.

The desired output is the actual black/white material silhouette on an SVG
engineering sheet. The geometry layer is tagged only to separate material from
annotations. Native curves, groups, transforms, local references, masks and clips
are accepted; no particular path decomposition is required. The scorer renders
the geometry with Chrome and compares it to material-membership references at
4 pixels/mm. A disagreement must lie more than 0.5 mm inside/outside the reference
and exceed 2 mm² total residual area to constitute a geometric failure. Required
numeric dimensions have 0.1 mm tolerance. These are discovery tolerances, not
manufacturing standards. A shape error and a wrong dimension remain distinguishable
in saved score rows and visual reviews.

Reference verification uses:

- Gear polar membership independent of SVG polygon serialization, plus pitch
  tooth-thickness and tooth-count checks.
- Cam analytical normal-offset construction, dense contour sampling and checked
  lower-density export. This is geometry only; no force, contact, acceleration,
  undercut or manufacturability certification is claimed.
- Manifold direct 3D box/cylinder membership evaluated in the cutting plane,
  checked against an independently derived clipped-polygon/ellipse SVG exporter.
- Rendered references, stale edits, shifted geometry and excluded malformed
  inputs. Six new automated tests passed before API screening.

The discovery baseline has no external tools. Failure means failure under this
saved interface and budget, NOT inability of a CAD-tool-using Astra agent. A
numerical exporter is an upper-bound/control baseline and succeeds on these
fully specified tasks. Neither that fact nor hard-case mining is a novel CAD
algorithm. The literature overlap audit specifies what additional evidence a
research contribution would require.
