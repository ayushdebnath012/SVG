using CapriccioSimulation
using Ferrite
using WriteVTK
using LAMMPS
using MPI
using TimerOutputs

###############
# Preparation #
###############

MPI.Init()
rank = MPI.Comm_rank(MPI.COMM_WORLD)

##############
# Parameters #
##############

tol = 1e-07
maxiter = 10
md_steps = 50
anchor_stiffness = 1
material = Hooke(31.676276890116206, 0.406137698950698)
fe_output_freq = 500

load_steps = vcat(zeros(0), 4.0e-6:4.0e-6:1.0)

lammps_prm = Dict(
    "anchor_stiffness" => anchor_stiffness/2,
    "timestep" => 0.01,
    "boundary_beads" => 0,
    "boundary_x" => 's',
    "boundary_y" => 's',
    "boundary_z" => 'p',
    "constraint_x" => 0,
    "constraint_y" => 0,
    "constraint_z" => 1,
    "Tstart" => 0.3,
    "Tend" => 0.3,
    "dpd_friction_coeff" => 1.0,
    "initial_energy_minimization" => "no",
    "initial_velocities" => "yes",
    "wall_reflect" => "no",
    "anchorforce_avg_every" => 1,
    "anchorforce_avg_repeat" => md_steps,
    "anchorforce_output" => md_steps,
    "obsregion_x" => 40,
    "obsregion_y" => 40,
    "obsregion_z" => 25,
    "output" => 10,
    "trj_out" => 25000,
    "nbCutoff" => 2.5,
    "neighListCutoff" => 4.0,
    "neighListUpdate" => 1,
    "bond_breakage" => 1,
    "Neverybreak" => 10,
    "Rmax1" => 1.1,
    "break_probability" => 0.9,
    "break_seed" => 49829
)

#################
# FE Definition #
#################

grid = load_grid("input/GTPm.inp")

ΓN = union(
     	getfacetset(grid, "LOAD_1"),
	getfacetset(grid, "LOAD_2"),
)

dof = vector_dof_handler(grid, :u, ["FE", "BD"])

facetvalues = facet_values(dof)

ch = ConstraintHandler(dof)

Boun1 = getnodeset(grid, "BOUN_1")
add!(ch, Dirichlet(:u, Boun1, x-> 0, 3))

close!(ch)

α_fun(ξ) = ξ == 1. ? 1. : 0.35ξ

alpha = AlphaHandler(grid, [
    "FE" => 1.0,
    "MD" => 0.0,
    "BD" => NaN
    ], α_fun)

proj = projector(dof)

#################
# MD Definition #
#################

lmp = LMP(["-sf", "opt", "-log", "output/log.lammps"])
set_variables!(lmp, lammps_prm)
command(lmp, "include input/GTPm.lmp")
anchor = AnchorAtoms(lmp, "anchor", dof, anchor_stiffness)

##################
# Run Simulation #
##################

K_ext = get_embeded_stiffness(anchor)

if iszero(rank)
    pvd = paraview_collection("output/fe-md-simulation")
end

assembler = create_assembler(material, dof, alpha)
u = system_vector(dof)

for (step, load) in enumerate(load_steps)
    @timeit "FEMD-Iteratrion" begin
        @timeit "set displacements" set_displacements!(anchor, u)
        @timeit "run md" run_md!(lmp, md_steps)
        @timeit "gather anchorforces" f_ext = get_anchorforces(anchor, "f_anchorforce_avg")
	traction(x) = Vec(1.0*sign(x[1])*load,0.0,0.0);
	assemble_external_forces!(f_ext, dof, ΓN, facetvalues, traction);
        @timeit "update constraints" update!(ch, load)
        @timeit "solve fe" global u = solve_fe!(u, assembler, ch, K_ext, f_ext; tol, maxiter)

        if iszero(rank) && iszero(step % fe_output_freq)
            @timeit "write solution" VTKGridFile("output/fe-md-simulation-$step", dof) do vtk
                write_solution(vtk, dof, u)
                f = compute_forces(assembler, u) + K_ext * u - f_ext
                write_solution(vtk, dof, f, "forces")
                σ = compute_stresses(assembler, u)
                σ_nodes = project(proj, σ)
                write_projection(vtk, proj, σ_nodes, "stress")

                pvd[get_ntimestep(lmp)] = vtk
            end
        end
    end

    if iszero(rank)
        print_timer(linechars = :ascii)
    end
end

if iszero(rank)
    vtk_save(pvd)
end

MPI.Finalize()
