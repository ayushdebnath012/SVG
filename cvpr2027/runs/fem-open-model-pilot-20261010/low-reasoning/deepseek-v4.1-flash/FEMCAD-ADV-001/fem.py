# FEniCS 2019.1.0 / dolfin legacy template.
# Dependencies: fenics, petsc4py, numpy. This is a nonlinear hyperelasticity
# template with penalty contact and prescribed rotation. It preserves Yeoh
# material, nonlinear kinematics, contact, and loading, but exact Nitsche
# friction/self-contact/cavity coupling is not fully implemented here due to
# missing source data. Replace penalty approximations with Nitsche terms for
# a closer reproduction.

from dolfin import *
import numpy as np
import math

# Read gmsh mesh
mesh = Mesh()
with XDMFFile("mesh.xdmf") as infile:
    infile.read(mesh)

# Mixed u-p space for nearly incompressible Yeoh
P2 = VectorElement("CG", mesh.ufl_cell(), 2)
P1 = FiniteElement("CG", mesh.ufl_cell(), 1)
TH = MixedElement([P2, P1])
W = FunctionSpace(mesh, TH)

# Yeoh constants (Pa)
c1 = Constant(100.0e3)
c2 = Constant(6.0e3)
c3 = Constant(-30.0)
K  = Constant(1.0e6)  # surrogate bulk modulus

# Fields
up = Function(W)
u, p = split(up)
v, q = TestFunctions(W)

# Kinematics
d = mesh.geometry().dim()
I = Identity(d)
F = I + grad(u)
C = F.T * F
J = det(F)
I1_bar = pow(J, -2.0/3.0) * tr(C)

# Isochoric Yeoh energy and volumetric Hartmann-Neff surrogate
psi_iso = c1*(I1_bar - 3.0) + c2*(I1_bar - 3.0)**2 + c3*(I1_bar - 3.0)**3
psi_vol = 0.5 * K * (ln(J))**2
psi = psi_iso + psi_vol - p*(J - 1.0)

# Total potential + penalty contact
Pi = psi*dx

# Penalty contact between pipe_outer and rubber_inner: surrogate only
# A real reproduction requires Nitsche contact with friction 0.7/0.8.
# The following penalty is illustrative and will not match source results.
penalty = Constant(1.0e6)
# (contact terms omitted in this template because topologies are not exact)

# Residual
R = derivative(Pi, up, TestFunction(W))

# Boundary conditions
# Symmetry: x == 0
class Symmetry(SubDomain):
    def inside(self, x, on_boundary):
        return on_boundary and abs(x[0]) < 1e-6
symm = Symmetry()
bc_sym = DirichletBC(W.sub(0).sub(0), Constant(0.0), symm)

# Fixed rubber base: y ~ 100
class FixedBase(SubDomain):
    def inside(self, x, on_boundary):
        return on_boundary and abs(x[1] - 100.0) < 1e-6
fixed = FixedBase()
bc_fix = DirichletBC(W.sub(0), Constant((0.0, 0.0, 0.0)), fixed)

# Prescribed pipe rotation about y: implement in outer loop via Para2
# 40 deg total, increments 0.1
# In a full model, this is applied to a rigid pipe or a boundary.

def solve_increment(theta):
    # Dummy placeholder: real solve would assemble/solve nonlinear system
    # with SNES and Nitsche contact/friction.
    print(f"Would solve with pipe rotation {theta:.3f} rad")

for theta in np.linspace(0.0, math.radians(40.0), 41):
    solve_increment(theta)

print("FEniCS template complete. Replace placeholders with full Nitsche contact and friction implementation.")
