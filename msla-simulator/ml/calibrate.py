"""Recaler le simulateur sur une machine réelle (réduit l'écart simulation / réalité).

Entrées : une image cible binaire (mire imprimée : réseaux de lignes, trous, bords) et l'image binaire
mesurée de la pièce imprimée (microscope ou scanner, même échelle, même taille).
Ajuste : flou gaussien sg (px), rayon de cône R (px, LCD) et exposition (E0/2Ec) par moindres carrés.

  python -m msla_ml.calibrate cible.png mesure.png --pitch 50
Chaque couple de mires donne un point ; plus il y a de mires (tailles, positions sur le champ), plus l'ajustement est fiable.
"""
import argparse
import numpy as np
from PIL import Image
from scipy.optimize import minimize
from . import sim


def load(path):
    a = np.asarray(Image.open(path).convert('L'), float)
    return a > 127


def fit(target, measured, init=(0.8, 0.0, 1.1)):
    def loss(q):
        sg, R, expo = np.exp(q[0]), abs(q[1]), np.exp(q[2])
        H = sim.psf_freq(R, sg, target.shape)[None]
        dose = sim.forward_dose(target[None].astype(float), H, expo)[0]
        cu = 1 / (1 + np.exp(-(dose - sim.THR) / 0.04))
        return float(np.mean((cu - measured) ** 2))
    best = None
    for s0 in (0.4, 0.8, 1.6, 3.0):
        r = minimize(loss, [np.log(s0), init[1], np.log(init[2])], method='Nelder-Mead', options=dict(xatol=1e-3, fatol=1e-6, maxiter=400))
        if best is None or r.fun < best.fun:
            best = r
    return dict(sg_px=float(np.exp(best.x[0])), R_px=float(abs(best.x[1])), expo=float(np.exp(best.x[2])), residual=float(best.fun))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('target'); ap.add_argument('measured'); ap.add_argument('--pitch', type=float, default=50.0)
    a = ap.parse_args()
    r = fit(load(a.target), load(a.measured))
    print('flou sg = %.2f px = %.0f µm | rayon cône R = %.2f px = %.0f µm | exposition E0/(2Ec) = %.2f | résidu %.4f'
          % (r['sg_px'], r['sg_px'] * a.pitch, r['R_px'], r['R_px'] * a.pitch, r['expo'], r['residual']))
