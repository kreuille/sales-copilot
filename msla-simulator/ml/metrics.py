"""Mesures de précision : pixels faux et écart de contour (µm)."""
import numpy as np
from scipy import ndimage as ndi


def boundary(mask):
    return mask & ~ndi.binary_erosion(mask, border_value=0)


def contour_dev(printed, target, pitch_um, cap_px=12):
    """Retourne (rms_um, p95_um, pixels_faux_pourcent) pour une paire (imprimé, cible) booléennes 2D."""
    bt, bp = boundary(target), boundary(printed)
    wrong = 100.0 * np.mean(printed != target) / max(1e-9, target.mean()) * target.mean() if target.any() else 0.0
    wrong = 100.0 * (printed != target).sum() / max(1, target.sum())
    if not bt.any() or not bp.any():
        return cap_px * pitch_um, cap_px * pitch_um, wrong
    d_to_p = ndi.distance_transform_edt(~bp)[bt]
    d_to_t = ndi.distance_transform_edt(~bt)[bp]
    d = np.minimum(np.concatenate([d_to_p, d_to_t]), cap_px) * pitch_um
    return float(np.sqrt(np.mean(d ** 2))), float(np.percentile(d, 95)), float(wrong)
