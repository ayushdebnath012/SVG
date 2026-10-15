# History

The current design was reached through a small number of design stages. Only the initial design is kept as a file; the
others are described here for context.

| Design | What it was | What it taught |
|---|---|---|
| [Initial design](initial_design/README.md) (Aug 2026) | An earlier blade with two manifold bores and 32 passage legs, built in SolidWorks. Superseded; the file is kept | A passage network that is connected to itself is not a cooling circuit, and a cooling layout is only as good as the blade shape around it. Its outer shape was about 1.8–1.9 times as thick as intended and had no leading-edge radius |
| Second design (Oct 2026) | A new blade designed from the stage velocity triangles, with two root-fed circuits, film cooling and, after refinement, a flared shank and an explicit trailing-edge exit. Not published as a file | Features must be placed from the exact section at their own radius; a volume check alone does not show a blind hole, so the exported solid has to be examined directly |
| Previous design | The second design with the hole set reduced from 94 to 91 holes and its geometry examined on the exported solid. Not published as a file | Three hole geometries were unsound, found only because the exported solid was examined; faceted rib surfaces left 3,846 faces |
| **Current design** | The previous design with smooth rib surfaces: 1,542 faces, same holes, pins, slots and passages | The current CAD model, in [`../cad/`](../cad/README.md) |

## Earlier states of this repository

An earlier version of this repository, published on GitHub in August 2026, presented the initial design as its subject.
Its claims were geometric (passage connectivity, wall thickness, ligaments) and they remain true for that solid; they were
not claims about a working cooling system, and they are no longer the subject of this repository.

## Not kept

Intermediate CAD files and working notes from the development are not published. The decisions that came out of them are
in [`../design/decisions.md`](../design/decisions.md).
