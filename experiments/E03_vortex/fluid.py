"""3-D incompressible Navier–Stokes on a face-staggered Cartesian mesh (unit density).

Centred momentum fluxes, midpoint RK2 with two pressure projections, explicit viscosity.
Wall normals are prescribed, wall tangents reflect evenly (odd at the jet inlet).
The pressure inverse uses the eigenvalues of the *same discrete* divergence/gradient.
"""
import numpy as np
from scipy import fft, ndimage


def along(a, axis, start=None, stop=None):
    s = [slice(None)] * a.ndim
    s[axis] = slice(start, stop)
    return a[tuple(s)]


def average(a, axis):
    return (along(a, axis, 1) + along(a, axis, None, -1)) * 0.5


class Tank:
    def __init__(self, n, length=6., viscosity=.05, periodic=(), inlet=False):
        self.n, self.length, self.nu = n, length, viscosity
        self.h = length / n
        self.periodic = tuple(periodic)
        self.walls = tuple(i for i in range(3) if i not in periodic)
        self.inlet = inlet
        self.zero_plane = np.zeros((n, n))
        self.origin = np.array([-length/2, -length/2, 0.])
        self.axes = [self.origin[i] + self.h*(np.arange(n)+.5) for i in range(3)]
        eigenvalues = []
        for axis in range(3):
            factor = np.pi / (n if axis in periodic else 2*n)
            eigenvalues.append(-4*np.sin(factor*np.arange(n))**2 / self.h**2)
        spectrum = sum(np.meshgrid(*eigenvalues, indexing="ij", sparse=True))
        spectrum[0, 0, 0] = 1
        self.inverse_lap = 1 / spectrum
        self.inverse_lap[0, 0, 0] = 0

    def coords(self, component=None):
        axes = self.axes.copy()
        if component is not None:
            axes[component] = self.origin[component] + self.h*np.arange(self.n+1)
        return np.meshgrid(*axes, indexing="ij", sparse=True)

    def zeros(self):
        return [np.zeros(tuple(self.n + (axis == i) for axis in range(3))) for i in range(3)]

    def boundary(self, u, port):
        for i, q in enumerate(u):
            q = np.moveaxis(q, i, 0)
            if i in self.periodic:
                q[-1] = q[0]
            elif i == 2 and port is not None:
                q[0], q[-1] = port, port.mean()
            else:
                q[0] = q[-1] = 0

    def extend(self, q, axis, component):
        """One ghost value on each end, respecting face vs centre location."""
        v = np.moveaxis(q, axis, 0)
        if axis in self.periodic:
            lo, hi = (v[-2], v[1]) if component == axis else (v[-1], v[0])
        elif component == axis:
            lo, hi = 2*v[0]-v[1], 2*v[-1]-v[-2]
        else:
            lo = -v[0] if self.inlet and axis == 2 else v[0]
            hi = v[-1]
        return np.moveaxis(np.concatenate((lo[None], v, hi[None])), 0, axis)

    def divergence(self, u):
        return sum(np.diff(q, axis=i) for i, q in enumerate(u)) / self.h

    def project(self, u, port=None, dt=1.):
        self.boundary(u, port)
        b = self.divergence(u) / dt
        if self.walls:
            b = fft.dctn(b, type=2, axes=self.walls, norm="ortho")
        if self.periodic:
            b = fft.fftn(b, axes=self.periodic)
        p = b*self.inverse_lap
        if self.periodic:
            p = fft.ifftn(p, axes=self.periodic).real
        if self.walls:
            p = fft.idctn(p, type=2, axes=self.walls, norm="ortho")
        for i, q in enumerate(u):
            along(q, i, 1, -1)[:] -= (dt/self.h)*np.diff(p, axis=i)
            if i in self.periodic:
                v, pp = np.moveaxis(q, i, 0), np.moveaxis(p, i, 0)
                v[0] -= (dt/self.h)*(pp[0]-pp[-1])
                v[-1] = v[0]
        return p

    def rhs(self, u):
        convection, diffusion = [], []
        for i, q in enumerate(u):
            adv, visc = np.zeros_like(q), np.zeros_like(q)
            for j in range(3):
                ghost = self.extend(q, j, i)
                face_value = average(ghost, j)
                advector = face_value if j == i else average(self.extend(u[j], i, j), i)
                adv -= np.diff(advector*face_value, axis=j) / self.h
                visc += np.diff(ghost, n=2, axis=j) * (self.nu/self.h**2)
            if i in self.walls:
                for term in (adv, visc):
                    v = np.moveaxis(term, i, 0)
                    v[0] = v[-1] = 0.
            convection.append(adv)
            diffusion.append(visc)
        return convection, diffusion

    def inner(self, a, b):
        total = 0.
        for i, (v, w) in enumerate(zip(a, b)):
            uv = np.moveaxis(v*w, i, 0)
            total += uv[1:-1].sum() + .5*(uv[0].sum()+uv[-1].sum())
        return float(total*self.h**3)

    def step(self, u, dt, mid_port=None, end_port=None):
        a, v = self.rhs(u)
        mid = [q + (.5*dt)*(f+g) for q, f, g in zip(u, a, v)]
        self.project(mid, mid_port, dt/2)
        a, v = self.rhs(mid)
        new = [q + dt*(f+g) for q, f, g in zip(u, a, v)]
        p = self.project(new, end_port, dt)
        # Pressure work from integration by parts on the staggered mesh.
        port_work = float(((p[:, :, 0]*mid[2][:, :, 0]).sum()
                          -(p[:, :, -1]*mid[2][:, :, -1]).sum())*self.h**2) if self.inlet else 0.
        normal_work = 0.
        if self.inlet:
            for k in (0, -1):
                normal_work += float((mid[2][:,:,k]*(new[2][:,:,k]-u[2][:,:,k])).sum() * .5*self.h**3)
        work = np.array([dt*self.inner(mid, a), dt*self.inner(mid, v), dt*port_work, normal_work])
        return new, p, mid, work

    def centers(self, u):
        return np.array([average(q, i) for i, q in enumerate(u)])

    def curl(self, vel):
        # Centred differences at interior cell centres, second-order one-sided at boundaries.
        def d(i, j):
            if j in self.periodic:
                return (np.roll(vel[i], -1, j) - np.roll(vel[i], 1, j))/(2*self.h)
            return np.gradient(vel[i], self.h, axis=j, edge_order=2)
        return np.array([d(2, 1)-d(1, 2), d(0, 2)-d(2, 0), d(1, 0)-d(0, 1)])

    def sample(self, vel, points):
        indices = ((points-self.origin)/self.h-.5).T
        return np.column_stack([ndimage.map_coordinates(q, indices, order=1, mode="nearest")
                                for q in vel])


def ring_velocity(radius, height, circulation, core, ring_radius=1., sections=64):
    """Axisymmetric components at (r, z) relative to ring centre, midpoint line quadrature."""
    radial = np.zeros(np.broadcast_shapes(radius.shape, height.shape))
    axial = np.zeros_like(radial)
    for angle in 2*np.pi*(np.arange(sections)+.5)/sections:
        c = np.cos(angle)
        d2 = radius**2 + ring_radius**2 - 2*radius*ring_radius*c + height**2 + core**2
        weight = (circulation*ring_radius/(2*sections)) / (d2*np.sqrt(d2))
        radial += weight*height*c
        axial += weight*(ring_radius-radius*c)
    return radial, axial


def initial_rings(tank, rings):
    u = tank.zeros()
    for i in range(3):
        x, y, z = tank.coords(i)
        radius = np.hypot(x, y)[:, :, 0]
        # Equal radii share the exact same analytic field, reducing quadrature size.
        values, indices = np.unique(radius, return_inverse=True)
        for height, strength, core in rings:
            ur, uz = ring_velocity(values[:, None], z.ravel()[None, :]-height, strength, core)
            if i == 2:
                u[i] += uz[indices.reshape(radius.shape)]
            else:
                unit = (x if i == 0 else y)/np.maximum(radius[:, :, None], 1e-30)
                u[i] += ur[indices.reshape(radius.shape)]*unit
    tank.project(u)
    return u
