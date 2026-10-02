R = 29.0
height = 84.0
seam = 0.31
half_width = math.pi * R
# Sub-0.10 mm mesh in the isometric flat coordinates.
x = np.linspace(-half_width - 0.5, half_width + 0.5, 1901)
y = np.linspace(-height/2 - 0.5, height/2 + 0.5, 901)
U = x[None, :]
V = y[:, None]
theta = seam + (U + half_width)/R
X = R * np.cos(theta)
Y = R * np.sin(theta)
Z = V + height/2
# Positive precisely in the rectangular sheet before drilling.
field = np.minimum(half_width - np.abs(U), height/2 - np.abs(V))
bores = [([5.0, 0.0, 37.0], [1.0, 0.37, 0.61], 12.0),
         ([-4.0, 7.0, 62.0], [0.24, 1.0, -0.32], 8.0)]
for point, axis, radius in bores:
    n = np.array(axis, dtype=float)
    n = n / np.linalg.norm(n)
    dx = X - point[0]
    dy = Y - point[1]
    dz = Z - point[2]
    along = dx*n[0] + dy*n[1] + dz*n[2]
    distance_squared = dx*dx + dy*dy + dz*dz - along*along
    clearance = np.sqrt(np.maximum(distance_squared, 0.0)) - radius
    field = np.minimum(field, clearance)
# Interpolated zero contours become actual closed SVG vector paths.
svg = contour_svg(x, y, field)