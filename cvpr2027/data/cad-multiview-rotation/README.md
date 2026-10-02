# Multiview machining edit discovery

Created 22 September 2026 to search for substantive drawing failures after
earlier geometry, native CAD and functional sizing controls passed.

The task rotates twelve B bores 23 degrees about a stated physical datum,
changes them from 8 mm blind holes to 12 mm through holes, and deepens two
counterbores from 4 to 9 mm. All three views, feature identities, labels,
leaders and notes must remain consistent. The plate and four A bores are
protected. Source SVG coordinates and explicit view conventions provide the
full specification. The final design retains at least 4 mm between holes.

The original fixture uses editable circles and lines. A paired export under
`../cad-flattened-multiview` combines geometry into compound paths while
retaining the same physical object, annotations and task. This is a paired
representation experiment, not two independent object families. Both build
scripts freeze separate manifests before API calls. No target is supplied to
the API or to the arithmetic and inspection tools.

Generation uses `gpt-6-astra`, high effort, 24,000 output tokens per turn, at most
five API turns and four generic arithmetic/inspection calls. This is a bounded
configuration, not a claim about unlimited model capability. Original requests,
responses, usage, candidate SVGs and grades are retained. Account balance is not
available; reported tokens do not imply a known dollar cost.

Geometry is checked as the union of sampled primitive/path boundaries rather
than by element IDs or required path ordering. Coincident hidden edges and
equivalent curve decompositions cannot create a geometric failure merely by
being represented differently. The stated tolerance is 0.1 mm; discrete
sampling adds an explicit 0.0125 mm allowance. Geometric source equivalence
between exports was checked before testing. Font/layout raster equality is
not asserted.

Annotation positions are diagnostics, not automatic hard-case evidence.
Alternate valid leaders and synonymous notes require review. The initial
primitive result, for example, used radial leaders ending on the hole rims;
that layout was checked and accepted in a separate adjudication record.

A hard-case admission requires three independent completed high-effort
geometric failures plus reference, grader and visual review. Incomplete calls,
operational errors, formatting/interface errors, valid alternative geometry,
and annotation-only deviations are excluded. Repaired intermediate outputs
do not count. An unchanged physical object that fails only after export must
be described as representation-sensitive, not as a new impossible shape.

Validation uses geometry, material clearance and cross-view correspondence.
No FEM is claimed: the task specifies machining geometry without structural
loads or material properties. No new training uses these evaluation cases.

Reproduction from the workspace root, using fresh output directories:

```
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m unittest discover -s cvpr2027/tests -p test_cad_multiview_rotation.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m unittest discover -s cvpr2027/tests -p test_cad_flattened_multiview.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python cvpr2027/scripts/cad_multiview_rotation.py run --output /tmp/new-primitive-trial --sample 1
OPENBLAS_NUM_THREADS=1 .venv/bin/python cvpr2027/scripts/cad_flattened_multiview.py run --output /tmp/new-compound-trial --sample 1
```

The build commands deliberately refuse to overwrite frozen manifests. The
arithmetic tool supports numeric expressions and trigonometry, with no file or
network access. Existing environment-based API credentials are used without
embedding them in experiment files.
