"""Procédés LCD et DLP avec randomisation de domaine (paramètres tirés au hasard à chaque échantillon)."""
import numpy as np
from .sim import psf_freq, N


def lcd_params(rng, gap_min=1.5, **fix):
    """LCD : le plan de polymérisation est à gap >= gap_min mm de l'écran (rng=None si tout est fixé)."""
    p = dict(kind='lcd', wl=405.0)
    if rng is not None:
        p.update(gap=rng.uniform(gap_min, max(gap_min + 0.5, 3.0)), div=rng.uniform(2, 12), dmax=rng.choice([20, 20, 6, 3, 1.5, 0.8]),
                 pitch=rng.uniform(35, 60), blocker=rng.uniform(0.1, 0.8), dose=rng.uniform(1.6, 3.0), vari=rng.uniform(0, 0.5))
    p.update(fix)
    return p


def dlp_params(rng, **fix):
    p = dict(kind='dlp', wl=405.0)
    if rng is not None:
        p.update(sig_lens=rng.uniform(8, 35), edge=rng.uniform(0, 1.5), pitch=rng.uniform(35, 60), blocker=rng.uniform(0.1, 0.8), dose=rng.uniform(1.6, 3.0))
    p.update(fix)
    return p


def sigma_R(p):
    """(R_px, sg_px, multiplicateurs gauche/centre/droite)."""
    wl, pt = p['wl'], p['pitch']
    s_res = 25 / (1 + 3 * p['blocker']) * (wl / 405) ** 3
    if p['kind'] == 'lcd':
        s_sc = 15 * p['gap'] * (405 / wl) ** 4
        sg = np.hypot(s_sc, s_res) / pt
        R = p['gap'] * 1000 * np.tan(np.radians(min(p['div'], p['dmax']))) / pt
        v = p['vari']
        return R, sg, (1 - v, 1.0, 1 + v)
    s_sc = 4 * (405 / wl) ** 4
    sg = np.sqrt(p['sig_lens'] ** 2 + s_res ** 2 + s_sc ** 2) / pt
    return 0.0, sg, (1 + p['edge'], 1.0, 1 + p['edge'])


def transfer(p, shape=N):
    """Fonctions de transfert (3,ny,nx) pour les zones gauche / centre / droite."""
    R, sg, mult = sigma_R(p)
    return np.stack([psf_freq(R * m, sg * m, shape) for m in mult])


def sigma_eff_um(p):
    R, sg, _ = sigma_R(p)
    return float(np.hypot(R / 2, sg) * p['pitch'])


def light_loss(p):
    """Facteur de temps d'exposition dû à une grille qui coupe les angles supérieurs à dmax (LCD)."""
    if p['kind'] != 'lcd' or p['div'] <= p['dmax']:
        return 1.0
    r = np.radians
    return float((1 - np.cos(r(p['dmax']))) / (1 - np.cos(r(p['div']))))
