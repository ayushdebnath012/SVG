"""Planar rigid-body mechanism kinematics and statics for the mechanism-design grader.

Bodies move in the x-z plane; every revolute axis is parallel to y. Each body's local frame coincides with the global
frame in the submitted reference pose, so a body's pose q = (x, z, phi) is its displacement from that pose.

Joints (points are global coordinates in the reference pose, mm):
  revolute  {parts: [a, b], origin: [x, y, z]}                 2 equations
  prismatic {parts: [a, b], origin, axis: [ux, 0, uz]}          2 equations (no relative rotation, no lateral slip)
  fixed     {parts: [a, b]}                                     3 equations
  gear      {parts: [a, b], ratio}                              1 equation: phi_a = ratio * phi_b
  distance  {parts: [a, b], point_a, point_b}                   driven: |P_a - P_b| = input value (e.g. a lead screw)

Statics uses the constraint Jacobian: J^T lam = -Q, where Q is the generalised external force. A revolute's two
multipliers are the pin force components (force on the first part); a distance joint's multiplier is the axial force
in the driving member, negative in tension (it pulls the two points together).
"""
from __future__ import annotations

import math

import numpy as np


def rot(phi: float) -> np.ndarray:
    c, s = math.cos(phi), math.sin(phi)
    return np.array([[c, -s], [s, c]])


def drot(phi: float) -> np.ndarray:
    c, s = math.cos(phi), math.sin(phi)
    return np.array([[-s, -c], [c, -s]])


def xz(p) -> np.ndarray:
    return np.array([float(p[0]), float(p[2])])


class Mechanism:
    def __init__(self, parts: list[str], ground: str, joints: list[dict], driver: str):
        self.parts = [p for p in parts if p != ground]
        self.ground = ground
        self.idx = {p: i for i, p in enumerate(self.parts)}
        self.joints = joints
        self.driver = driver
        self.n = 3 * len(self.parts)

    def pose(self, q: np.ndarray, part: str) -> tuple[np.ndarray, float]:
        if part == self.ground:
            return np.zeros(2), 0.0
        i = self.idx[part]
        return q[3 * i:3 * i + 2], q[3 * i + 2]

    def point(self, q: np.ndarray, part: str, p0: np.ndarray) -> np.ndarray:
        t, phi = self.pose(q, part)
        return rot(phi) @ p0 + t

    def _rows(self, q: np.ndarray, value: float | None):
        """Residuals and Jacobian rows, each tagged with its joint; the driver row is included when value is given."""
        res, jac, tags = [], [], []

        def d_point(part, p0):          # d(point)/dq, 2 x n
            m = np.zeros((2, self.n))
            if part == self.ground:
                return m
            i = self.idx[part]
            _, phi = self.pose(q, part)
            m[:, 3 * i:3 * i + 2] = np.eye(2)
            m[:, 3 * i + 2] = drot(phi) @ p0
            return m

        def d_phi(part):
            m = np.zeros(self.n)
            if part != self.ground:
                m[3 * self.idx[part] + 2] = 1.0
            return m

        for j in self.joints:
            a, b = j["parts"]
            kind = j["type"]
            if kind == "revolute":
                p0 = xz(j["origin"])
                r = self.point(q, a, p0) - self.point(q, b, p0)
                J = d_point(a, p0) - d_point(b, p0)
                for k in range(2):
                    res.append(r[k]); jac.append(J[k]); tags.append((j["name"], k))
            elif kind == "fixed":
                p0 = np.zeros(2)
                r = self.point(q, a, p0) - self.point(q, b, p0)
                J = d_point(a, p0) - d_point(b, p0)
                for k in range(2):
                    res.append(r[k]); jac.append(J[k]); tags.append((j["name"], k))
                res.append(self.pose(q, a)[1] - self.pose(q, b)[1]); jac.append(d_phi(a) - d_phi(b)); tags.append((j["name"], 2))
            elif kind == "prismatic":
                p0, u0 = xz(j["origin"]), xz(j["axis"])
                u0 = u0 / np.linalg.norm(u0)
                n0 = np.array([-u0[1], u0[0]])
                _, phib = self.pose(q, b)
                nb = rot(phib) @ n0
                d = self.point(q, a, p0) - self.point(q, b, p0)
                res.append(float(nb @ d))
                jac.append(nb @ (d_point(a, p0) - d_point(b, p0)) + (drot(phib) @ n0) @ d * d_phi(b))
                tags.append((j["name"], 0))
                res.append(self.pose(q, a)[1] - phib); jac.append(d_phi(a) - d_phi(b)); tags.append((j["name"], 1))
            elif kind == "gear":
                r_ = float(j["ratio"])
                res.append(self.pose(q, a)[1] - r_ * self.pose(q, b)[1]); jac.append(d_phi(a) - r_ * d_phi(b)); tags.append((j["name"], 0))
            elif kind == "distance":
                if j["name"] != self.driver or value is None:
                    continue
                pa, pb = xz(j["point_a"]), xz(j["point_b"])
                d = self.point(q, a, pa) - self.point(q, b, pb)
                L = float(np.linalg.norm(d))
                res.append(L - value); jac.append((d / L) @ (d_point(a, pa) - d_point(b, pb))); tags.append((j["name"], 0))
            else:
                raise ValueError(f"unknown joint type {kind}")
        return np.array(res), np.array(jac).reshape(len(res), self.n), tags

    def dof(self, q: np.ndarray) -> int:
        _, J, _ = self._rows(q, None)
        return self.n - int(np.linalg.matrix_rank(J, tol=1e-8)) if len(J) else self.n

    def redundant(self, q: np.ndarray) -> int:
        _, J, _ = self._rows(q, None)
        return J.shape[0] - int(np.linalg.matrix_rank(J, tol=1e-8))

    def driver_value(self, q: np.ndarray) -> float:
        j = next(j for j in self.joints if j["name"] == self.driver)
        a, b = j["parts"]
        return float(np.linalg.norm(self.point(q, a, xz(j["point_a"])) - self.point(q, b, xz(j["point_b"]))))

    def solve(self, value: float, q0: np.ndarray, iters: int = 60) -> tuple[np.ndarray, float]:
        q = q0.copy()
        for _ in range(iters):
            r, J, _ = self._rows(q, value)
            if np.max(np.abs(r)) < 1e-9:
                break
            dq = np.linalg.lstsq(J, -r, rcond=None)[0]
            q += dq
        r, _, _ = self._rows(q, value)
        return q, float(np.max(np.abs(r)))

    def sweep(self, start: float, stop: float, steps: int) -> list[tuple[float, np.ndarray, float]]:
        q = np.zeros(self.n)
        out = []
        for v in np.linspace(start, stop, steps):
            q, err = self.solve(float(v), q)
            out.append((float(v), q.copy(), err))
        return out

    def statics(self, q: np.ndarray, loads: list[tuple[str, np.ndarray, np.ndarray]]) -> dict:
        """loads: (part, application point in reference coordinates, force [Fx, Fz] in N). Returns joint forces."""
        value = self.driver_value(q)
        _, J, tags = self._rows(q, value)
        Q = np.zeros(self.n)
        for part, p0, F in loads:
            if part == self.ground:
                continue
            i = self.idx[part]
            t, phi = self.pose(q, part)
            arm = rot(phi) @ p0
            Q[3 * i:3 * i + 2] += F
            Q[3 * i + 2] += arm[0] * F[1] - arm[1] * F[0]
        lam, *_ = np.linalg.lstsq(J.T, -Q, rcond=None)
        resid = float(np.linalg.norm(J.T @ lam + Q))
        unique = int(np.linalg.matrix_rank(J, tol=1e-8)) == J.shape[0]
        forces: dict[str, list[float]] = {}
        for (name, k), v in zip(tags, lam):
            forces.setdefault(name, []).append(float(v))
        return dict(multipliers=forces, residual_N=resid, determinate=unique, J=J, lam=lam, tags=tags)

    def body_loads(self, q: np.ndarray, st: dict, part: str) -> list[tuple[str, np.ndarray, np.ndarray]]:
        """Forces that joints apply to one body: (joint, global point, force [Fx, Fz]); moments of gear/fixed rows dropped."""
        out = []
        if part == self.ground:
            return out
        for j in self.joints:
            if part not in j["parts"] or j["name"] not in st["multipliers"]:
                continue
            lam = st["multipliers"][j["name"]]
            sign = 1.0 if j["parts"][0] == part else -1.0
            if j["type"] == "revolute":
                out.append((j["name"], self.point(q, part, xz(j["origin"])), sign * np.array(lam[:2])))
            elif j["type"] == "distance":
                pa, pb = xz(j["point_a"]), xz(j["point_b"])
                a, b = j["parts"]
                d = self.point(q, a, pa) - self.point(q, b, pb)
                u = d / np.linalg.norm(d)
                pt = self.point(q, part, pa if part == a else pb)
                out.append((j["name"], pt, sign * lam[0] * u))
        return out
