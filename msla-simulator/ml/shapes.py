"""Générateurs de géométries de coupe (binaires 128x128) : mires, trous, anneaux, polygones,
couronnes dentaires avec fissures et jeux de contact, formes organiques."""
import numpy as np
from scipy import ndimage as ndi
from .sim import N

YY, XX = np.mgrid[0:N, 0:N].astype(np.float64)


def _grating(rng):
    w = rng.integers(1, 9); gap = rng.integers(1, 9); ang = rng.choice([0, 45, 90, 135])
    u = {0: XX, 90: YY, 45: (XX + YY) / np.sqrt(2), 135: (XX - YY) / np.sqrt(2)}[int(ang)]
    m = ((u + rng.uniform(0, w + gap)) % (w + gap)) < w
    cx, cy, r = rng.uniform(32, 96), rng.uniform(32, 96), rng.uniform(18, 50)
    return m & (np.maximum(abs(XX - cx), abs(YY - cy)) < r)


def _dots(rng):
    m = np.zeros((N, N), bool)
    for _ in range(rng.integers(3, 20)):
        cx, cy, r = rng.uniform(8, 120), rng.uniform(8, 120), rng.uniform(0.7, 7)
        if rng.random() < 0.5:
            m |= (XX - cx) ** 2 + (YY - cy) ** 2 < r * r
        else:
            m |= (abs(XX - cx) < r) & (abs(YY - cy) < r)
    return m


def _rings(rng):
    m = np.zeros((N, N), bool)
    for _ in range(rng.integers(1, 4)):
        cx, cy = rng.uniform(25, 100), rng.uniform(25, 100)
        r1 = rng.uniform(8, 28); t = rng.uniform(1, 6)
        d = np.hypot(XX - cx, YY - cy)
        m |= (d < r1 + t) & (d > r1)
    return m


def _poly(rng):
    from scipy.spatial import ConvexHull
    m = np.zeros((N, N), bool)
    for _ in range(rng.integers(1, 4)):
        c = rng.uniform(20, 108, 2); pts = c + rng.normal(0, rng.uniform(6, 22), (rng.integers(4, 9), 2))
        try:
            h = ConvexHull(pts)
        except Exception:
            continue
        inside = np.ones((N, N), bool)
        for eq in h.equations:
            inside &= (eq[0] * XX + eq[1] * YY + eq[2]) <= 0
        m |= inside
    if rng.random() < 0.5:                                    # rainures fines
        for _ in range(rng.integers(1, 4)):
            x0, y0 = rng.uniform(10, 118, 2); a = rng.uniform(0, np.pi); w = rng.uniform(0.6, 3)
            d = abs((XX - x0) * np.sin(a) - (YY - y0) * np.cos(a)); L = abs((XX - x0) * np.cos(a) + (YY - y0) * np.sin(a))
            m &= ~((d < w) & (L < rng.uniform(10, 40)))
    return m


def _tooth(rng):
    """Deux couronnes voisines : jeu de contact étroit, fissures, puits."""
    m = np.zeros((N, N), bool)
    gap = rng.uniform(1.5, 6)
    a = rng.uniform(18, 28); b = rng.uniform(30, 44); n = rng.uniform(2.2, 3.2)
    for cx in (64 - a - gap / 2, 64 + a + gap / 2):
        q = (abs(XX - cx) / a) ** n + (abs(YY - 64) / b) ** n
        t = q <= 1
        if rng.random() < 0.8:
            t &= ~((abs(XX - cx) < rng.uniform(0.7, 2.2)) & (abs(YY - 64) < b * 0.75))
        if rng.random() < 0.6:
            t &= ~((abs(YY - 64) < rng.uniform(0.7, 2)) & (abs(XX - cx) < a * 0.7))
        for _ in range(rng.integers(0, 4)):
            px, py = cx + rng.uniform(-a * .7, a * .7), 64 + rng.uniform(-b * .7, b * .7)
            t &= ~((XX - px) ** 2 + (YY - py) ** 2 < rng.uniform(1.2, 4) ** 2)
        m |= t
    return m


def _blob(rng):
    z = ndi.gaussian_filter(rng.normal(size=(N, N)), rng.uniform(3, 9))
    return z > np.quantile(z, rng.uniform(0.35, 0.65))


GENS = [_grating, _dots, _rings, _poly, _tooth, _blob]


def random_shape(rng, weights=None):
    g = GENS[rng.choice(len(GENS), p=weights)]
    m = g(rng)
    if m.sum() < 30 or m.sum() > 0.9 * N * N:
        return random_shape(rng, weights)
    return m
