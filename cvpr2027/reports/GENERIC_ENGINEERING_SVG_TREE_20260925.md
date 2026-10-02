# Generic engineering SVG parsing and editing

Date: 25 September 2026

## What was built

The SVG editor now treats a drawing as a general XML/DOM tree. It does not assume that the drawing is a truss. The same parser and patch executor can therefore handle building plans, furniture drawings, mechanical parts, circuit diagrams, piping diagrams and other safe SVG drawings.

For each SVG, the parser records:

- every SVG element and its attributes and text;
- the parent-child relationship between elements;
- each element's position among its siblings;
- stable SVG `id` values when present;
- local links such as `href="#part"` and `url(#arrow)`;
- simple bounding-box hints and hashes for path or polyline geometry.

These relationships establish contact between SVG-tree nodes. A correspondence step aligns the source and proposed target trees using element type, stable IDs, attributes, text, geometry and local child structure. It is independent of the engineering meaning of the drawing.

## Edit pipeline

```text
original SVG
  -> parse into a safe scene graph
  -> obtain a proposed edited SVG
  -> match source nodes to target nodes
  -> derive a small, typed patch
  -> validate the patch
  -> apply it to the original tree
  -> parse the actual result again
  -> check exact target-tree equality and SVG references
  -> run the engineering verifier for that drawing family, when available
```

Patch version 3 supports attribute changes, attribute removal, text changes, element deletion, complete `d`/`points` geometry replacement, and insertion of a safe SVG subtree at an exact child position. The executor keeps source node identifiers stable while operations are applied, which prevents insertion or deletion from changing the meaning of later operations.

Inserted content is restricted to ordinary SVG elements. Scripts, event handlers, `foreignObject`, embedded objects and external URLs are rejected. Local SVG references are allowed and checked after the edit. Duplicate XML IDs and dangling local references are reported.

## Verified multi-domain benchmark

Five deliberately different SVG families were exercised end to end:

| Drawing | Representative edit | Result |
|---|---|---:|
| Building plan | extend a wall, insert a door group, rename a room | exact |
| Table | change dimensions and insert a second leg | exact |
| Mechanical part | change an outline, add a hole, edit a note | exact |
| Circuit | reroute a polyline, add a component, change voltage text | exact |
| Piping | extend a pipe and insert a valve subtree with a local marker reference | exact |

Results: **5/5 output trees exactly match their targets**, with **0 dangling references** and **0 duplicate XML IDs**. The saved benchmark includes every source SVG, target SVG, edited SVG, scene graph, correspondence, patch, result and SHA-256 manifest.

## Engineering verification boundary

SVG parsing and patching can be generic. Engineering verification cannot be one universal calculation because the governing model changes with the drawing:

| Drawing family | Suitable verifier |
|---|---|
| Truss | axial finite-element analysis and equilibrium |
| Beam or frame | beam/frame FEM, stress, deflection and buckling |
| Plate or shell | plate/shell FEM, stress, buckling and geometry rules |
| Mechanical part | tolerances, interference, section properties, stress or fatigue |
| Circuit | connectivity, KCL/KVL, SPICE or rule checks |
| Piping | graph continuity, pressure drop, flow conservation and code rules |
| Thermal drawing | conduction network or thermal FEM |
| Building plan | topology, clearance, accessibility and applicable code rules |

The project already verifies generated trusses with axial FEM and perforated plates with manufacturing-geometry checks. The generic SVG layer gives every future family the same parser, correspondence, patch, provenance and integrity checks. Each new family then adds a semantic importer and the correct solver or rule checker.

The current generic command takes a source SVG and a proposed target SVG. It deterministically derives and validates the patch. Natural-language edit inference is a separate model or rule layer; its proposed result must still pass this deterministic pipeline before it is accepted.

## Current limits

The matcher follows SVG hierarchy and sibling order. Large reorderings or reparenting may be represented as delete-plus-insert instead of a semantic move. Visual equivalence under arbitrary transforms, CSS stylesheets, clipping, masks and path-level geometric similarity is not yet proved. A drawing can also be syntactically correct while being physically invalid unless a suitable family verifier is installed.

## Reproducible command

```bash
PYTHONPATH=cvpr2027/scripts:cvpr2027/src .venv/bin/python \
  cvpr2027/scripts/svg_scene_edit.py \
  --source source.svg \
  --target proposed-target.svg \
  --out output-directory
```

The main implementation is in `src/svgpatchlab/core/correspondence.py`. Focused regression cases are in `tests/test_svg_generic_correspondence.py`. Saved results are in `runs/svg-generic-tree-v1/`.
