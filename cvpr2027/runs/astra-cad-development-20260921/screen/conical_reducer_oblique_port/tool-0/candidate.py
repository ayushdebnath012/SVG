r0, r1, h = 18.0, 46.0, 58.0
seam = 0.47
slant = math.sqrt(h*h + (r1-r0)*(r1-r0))
k = (r1-r0)/slant
rho0, rho1 = r0/k, r1/k
half_angle = math.pi*k

# Grid spacing is below 0.114 mm in each developed direction.
x = np.linspace(-2.0, 110.0, 1001)
y = np.linspace(-108.0, 108.0, 1901)
U, V = np.meshgrid(x, y)
rho = np.hypot(U, V)
phi = np.arctan2(V, U)
theta = seam + (phi + half_angle)/k
r = k*rho
Z = (rho-rho0)*h/slant
X = r*np.cos(theta)
Y = r*np.sin(theta)

# Retained annular sector, bounded by the two seam rays.
field = np.minimum(rho-rho0, rho1-rho)
field = np.minimum(field, U*math.sin(half_angle)-np.abs(V)*math.cos(half_angle))

# Remove every point inside the infinite cylinder, not just one wall crossing.
norm = math.sqrt(1.0 + 0.35**2 + 0.55**2)
nx, ny, nz = 1.0/norm, 0.35/norm, 0.55/norm
dx, dy, dz = X-4.0, Y-5.0, Z-29.0
along = dx*nx + dy*ny + dz*nz
distance = np.sqrt(np.maximum(dx*dx + dy*dy + dz*dz - along*along, 0.0))
field = np.minimum(field, distance-14.0)
svg = contour_svg(x, y, field)