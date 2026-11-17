"""Génération massive de données : (géométrie cible, paramètres de procédé, image corrigée optimale, résultats imprimés).

Exemples
  python -m msla_ml.gen_dataset --n 20000 --kind mix --out data/ --workers 8
  python -m msla_ml.gen_dataset --n 1000000 --kind lcd --gap-min 1.5 --no-teacher --out data_cibles/   # cibles + paramètres seulement

Débit mesuré sur 4 coeurs CPU : voir README (la correction optimale coûte ~0,4 s par image avec 3 PSF).
Pour des millions d'exemples, préférez l'entraînement avec simulateur différentiable en ligne (train_unet.py) :
les données sont alors générées à la volée sur GPU, sans rien stocker.
"""
import argparse, os, time
import numpy as np
from multiprocessing import Pool
from . import sim, shapes, processes as pr, metrics

COLS = ['kind', 'pitch', 'R_px', 'sg_px', 'm0', 'm2', 'expo', 'sigma_eff_um', 'light_loss', 'gap_mm', 'div_deg', 'dmax_deg']


def one_shard(args):
    i, n, kind, seed, iters, gap_min, teacher, out = args
    rng = np.random.default_rng(seed * 100003 + i)
    tg, tc, par, met = [], [], [], []
    B = 16
    for s in range(0, n, B):
        b = min(B, n - s)
        ps, Hs, ex = [], [], []
        for _ in range(b):
            k = kind if kind != 'mix' else rng.choice(['lcd', 'dlp'])
            p = pr.lcd_params(rng, gap_min=gap_min) if k == 'lcd' else pr.dlp_params(rng)
            ps.append(p); Hs.append(pr.transfer(p)); ex.append(p['dose'] / 2)
        t = np.stack([shapes.random_shape(rng) for _ in range(b)])
        H = np.stack(Hs); ex = np.array(ex)
        x = sim.optimize(t, H, ex, iters) if teacher else None
        a = sim.printed(t.astype(float), H, ex)
        c = sim.printed(x, H, ex) if teacher else None
        for j in range(b):
            p = ps[j]; R, sg, m = pr.sigma_R(p)
            par.append([p['kind'] == 'dlp', p['pitch'], R, sg, m[0], m[2], ex[j], pr.sigma_eff_um(p), pr.light_loss(p), p.get('gap', 0), p.get('div', 0), p.get('dmax', 0)])
            ma = metrics.contour_dev(a[j], t[j], p['pitch'])
            mc = metrics.contour_dev(c[j], t[j], p['pitch']) if teacher else (np.nan, np.nan, np.nan)
            met.append([ma[0], ma[2], mc[0], mc[2]])
        tg.append(np.packbits(t, axis=-1))
        if teacher:
            tc.append((x * 255).astype(np.uint8))
    d = dict(target=np.concatenate(tg), params=np.array(par, np.float32), metrics=np.array(met, np.float32), columns=np.array(COLS))
    if teacher:
        d['compensated'] = np.concatenate(tc)
    np.savez_compressed(os.path.join(out, 'shard_%05d.npz' % i), **d)
    return n


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=2000); ap.add_argument('--kind', default='mix', choices=['lcd', 'dlp', 'mix'])
    ap.add_argument('--out', default='data'); ap.add_argument('--shard', type=int, default=256); ap.add_argument('--workers', type=int, default=os.cpu_count())
    ap.add_argument('--iters', type=int, default=110); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--gap-min', type=float, default=1.5)
    ap.add_argument('--no-teacher', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    jobs = [(i, min(a.shard, a.n - i * a.shard), a.kind, a.seed, a.iters, a.gap_min, not a.no_teacher, a.out) for i in range((a.n + a.shard - 1) // a.shard)]
    t0 = time.time(); done = 0
    with Pool(a.workers) as p:
        for k in p.imap_unordered(one_shard, jobs):
            done += k
            print('%d / %d échantillons, %.1f /s' % (done, a.n, done / (time.time() - t0)), flush=True)
