"""Modèle physique 2D de l'image au plan de polymérisation (LCD MSLA ou DLP).

Même modèle que le simulateur web :
  dose = expo * somme_k  w_k(x) * (PSF_k * image)       (convolution = flou optique)
  polymérisé  <=>  dose > seuil                           (seuil = 0,5, expo = E0 / (2 Ec))
La PSF d'un pixel est un disque (cône de lumière du LCD) convolué par une gaussienne
(diffusion verre + résine, ou flou d'objectif pour le DLP).
Tout est vectorisé (B images à la fois) avec des FFT.
"""
import numpy as np
from scipy.special import j1

N = 128
THR = 0.5


def psf_freq(R_px, sg_px, n=N):
    """Fonction de transfert (réelle, paire) d'un disque de rayon R_px convolué par une gaussienne sg_px.
    n : taille (entier) ou (hauteur, largeur) pour des tranches de taille quelconque."""
    ny, nx = (n, n) if np.isscalar(n) else n
    fy, fx = np.fft.fftfreq(ny), np.fft.fftfreq(nx)
    rho = np.sqrt(fx[None, :] ** 2 + fy[:, None] ** 2)
    arg = 2 * np.pi * R_px * rho
    pill = np.where(arg < 1e-9, 1.0, 2 * j1(np.maximum(arg, 1e-12)) / np.maximum(arg, 1e-12))
    gau = np.exp(-2 * np.pi ** 2 * sg_px ** 2 * rho ** 2)
    return pill * gau


def hat_weights(n=N):
    """Poids linéaires gauche / centre / droite (flou qui varie sur le champ). n : taille ou (hauteur, largeur)."""
    ny, nx = (n, n) if np.isscalar(n) else n
    t = 2 * (np.arange(nx) + 0.5) / nx
    w = np.stack([np.maximum(0, 1 - t), 1 - np.abs(t - 1), np.maximum(0, t - 1)])
    return np.broadcast_to(w[:, None, :], (3, ny, nx)).copy()


WS = hat_weights()


def forward_dose(x, H, expo, ws=None):
    """x : (B,N,N) image envoyée au LCD (0..1). H : (B,K,N,N) ou (K,N,N) transferts. Retourne la dose."""
    X = np.fft.fft2(x)[:, None]
    if H.ndim == 3:
        H = H[None]
    conv = np.fft.ifft2(X * H).real                      # (B,K,N,N)
    w = (WS if ws is None and x.shape[-2:] == (N, N) else hat_weights(x.shape[-2:]) if ws is None else ws) if H.shape[1] == 3 else np.ones((1,) + x.shape[-2:])
    dose = (conv * w[None]).sum(1)
    return np.asarray(expo).reshape(-1, 1, 1) * dose


def printed(x, H, expo):
    return forward_dose(x, H, expo) > THR


def optimize(target, H, expo, iters=120, lr=0.05, steep=0.06, ws=None, x0=None):
    """Enseignant : cherche l'image qui, une fois floutée, polymérise exactement la cible (Adam, pixels bornés)."""
    t = target.astype(np.float64)
    x = t.copy() if x0 is None else x0.copy()
    if H.ndim == 3:
        H = H[None]
    expo_b = np.asarray(expo, dtype=np.float64).reshape(-1, 1, 1)
    w = (ws if ws is not None else hat_weights(t.shape[-2:])) if H.shape[1] == 3 else np.ones((1,) + t.shape[-2:])
    m = np.zeros_like(x); v = np.zeros_like(x)
    for i in range(1, iters + 1):
        dose = forward_dose(x, H, expo)
        cu = 1 / (1 + np.exp(-(dose - THR) / steep))
        g = (cu - t) * cu * (1 - cu) / steep * expo_b
        G = np.fft.fft2(w[None] * g[:, None])               # (B,K,N,N)
        grad = np.fft.ifft2(G * np.conj(H)).real.sum(1)
        m = 0.9 * m + 0.1 * grad
        v = 0.999 * v + 0.001 * grad ** 2
        x = np.clip(x - lr * (m / (1 - 0.9 ** i)) / (np.sqrt(v / (1 - 0.999 ** i)) + 1e-8), 0, 1)
    return x
