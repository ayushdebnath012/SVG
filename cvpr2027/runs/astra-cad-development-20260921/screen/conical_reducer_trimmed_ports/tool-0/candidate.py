r0, r1, H = 21.0, 49.0, 61.0
seam = 1.1
L = math.sqrt(H*H + (r1-r0)**2)
s = (r1-r0)/L
rho0, rho1 = r0/s, r1/s
half_angle = math.pi*s
# Physical developed coordinates; the whole sector lies strictly inside this grid.
x = np.linspace(0.0, 120.0, 1601)
y = np.linspace(-116.0, 116.0, 1935)
U = x[None, :]
V = y[:, None]
rho = np.sqrt(U*U + V*V)
phi = np.arctan2(V, U)
# Isometric inverse development of the neutral cone surface.
r = s*rho
Z = (rho-rho0)*(H/L)
theta = seam + math.pi + phi/s
X = r*np.cos(theta)
Y = r*np.sin(theta)
field = np.minimum(rho-rho0, rho1-rho)
field = np.minimum(field, U*math.sin(half_angle)-np.abs(V)*math.cos(half_angle))
field = np.minimum(field, 49.0 + 0.27*X - 0.18*Y - Z)
bores = [((2.0,-3.0,38.0),(1.0,0.41,0.72),15.0), ((12.0,6.0,21.0),(-0.35,1.0,0.18),11.0)]
for point, axis, radius in bores:
    norm = math.sqrt(sum(t*t for t in axis))
    nx, ny, nz = [t/norm for t in axis]
    qx = X-point[0]
    qy = Y-point[1]
    qz = Z-point[2]
    along = nx*qx + ny*qy + nz*qz
    distance = np.sqrt(np.maximum(qx*qx + qy*qy + qz*qz - along*along, 0.0))
    field = np.minimum(field, distance-radius)
svg = contour_svg(x, y, field)