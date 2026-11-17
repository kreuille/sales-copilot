"""Corrige un dossier de tranches PNG (blanc = polymériser) avant projection.

  python -m msla_ml.compensate_slices tranches/ sortie/ --process lcd --gap 1.5 --div 3 --dmax 3 --pitch 50 --dose 2.3
  python -m msla_ml.compensate_slices tranches/ sortie/ --process dlp --sig-lens 15 --edge 0.8 --pitch 50 --dose 2.3
  python -m msla_ml.compensate_slices ... --params machine_calibree.json     # paramètres issus de calibrate.py

Méthode : optimisation image par image (borne haute de ce qu'un réseau appris peut atteindre).
Coût : plusieurs secondes par tranche 1080p sur CPU ; un réseau appris (train_unet.py) fait la même chose en quelques ms sur GPU.
"""
import argparse, glob, json, os
import numpy as np
from PIL import Image
from . import sim, processes as pr

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--process', default='lcd', choices=['lcd', 'dlp'])
    ap.add_argument('--gap', type=float, default=1.5); ap.add_argument('--div', type=float, default=3.0); ap.add_argument('--dmax', type=float, default=20.0)
    ap.add_argument('--sig-lens', type=float, default=15.0); ap.add_argument('--edge', type=float, default=0.8); ap.add_argument('--vari', type=float, default=0.3)
    ap.add_argument('--pitch', type=float, default=50.0); ap.add_argument('--blocker', type=float, default=0.3); ap.add_argument('--dose', type=float, default=2.3)
    ap.add_argument('--iters', type=int, default=120); ap.add_argument('--params', help='JSON {sg_px, R_px, expo} issu de calibrate.py')
    a = ap.parse_args()
    os.makedirs(a.dst, exist_ok=True)
    if a.params:
        q = json.load(open(a.params)); R, sg, mult, expo = q.get('R_px', 0.0), q['sg_px'], (1, 1, 1), q.get('expo', a.dose / 2)
    else:
        p = (pr.lcd_params(None, gap=a.gap, div=a.div, dmax=a.dmax, pitch=a.pitch, blocker=a.blocker, wl=405.0, dose=a.dose, vari=a.vari)
             if a.process == 'lcd' else pr.dlp_params(None, sig_lens=a.sig_lens, edge=a.edge, pitch=a.pitch, blocker=a.blocker, wl=405.0, dose=a.dose))
        R, sg, mult = pr.sigma_R(p); expo = a.dose / 2
        print('flou équivalent : %.0f µm (%.2f px)' % (pr.sigma_eff_um(p), pr.sigma_eff_um(p) / a.pitch))
        if a.process == 'lcd': print('allongement du temps d\'exposition par la grille : x%.1f' % (1 / pr.light_loss(p)))
    for f in sorted(glob.glob(os.path.join(a.src, '*.png'))):
        t = np.asarray(Image.open(f).convert('L'), float) > 127
        H = np.stack([sim.psf_freq(R * m, sg * m, t.shape) for m in mult])
        x = sim.optimize(t[None].astype(float), H, expo, a.iters)[0]
        Image.fromarray((x * 255).astype(np.uint8)).save(os.path.join(a.dst, os.path.basename(f)))
        print(os.path.basename(f), 'ok', flush=True)
