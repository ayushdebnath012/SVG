Runtime base: [official FEniCS DOLFINx v0.9.0 package](https://github.com/FEniCS/dolfinx/pkgs/container/dolfinx%2Fdolfinx/287932245?tag=v0.9.0).
The base is pinned by its published digest. Gmsh and meshio are explicitly versioned.
OS packages are resolved at build time; retain the built image ID for every run.

Build with `docker build -t engineering-fem-runtime:0.9.0-gmsh4.15.2 cvpr2027/runtime/engineering-fem`.
The image has not been built on this host: Docker is unavailable. The runner refuses
execution without its isolation preflight and records this as an infrastructure block.
