"""Combien d'erreur une correction d'image peut-elle récupérer selon le flou ?
Pour chaque flou sigma (en pixels), on mesure sur des géométries variées :
  - sans correction ;
  - correction optimale par optimisation (enseignant, borne haute) ;
  - correction apprise (filtre de Wiener appris sur des paires cible -> enseignant).
Sortie : tableau CSV + JSON utilisé par le simulateur web (efficacité de la compensation).
"""
import json, sys, time
import numpy as np
from multiprocessing import Pool
from . import sim, shapes, metrics

PITCH = 50.0


def run(sig_px, n_train=160, n_test=80, expo=1.15, iters=110, seed=1):
    rng = np.random.default_rng(seed)
    H = sim.psf_freq(0.0, sig_px)[None]                  # une seule PSF (K=1)
    train = np.stack([shapes.random_shape(rng) for _ in range(n_train)])
    test = np.stack([shapes.random_shape(rng) for _ in range(n_test)])
    xt = np.concatenate([sim.optimize(train[i:i + 16], H, expo, iters) for i in range(0, n_train, 16)])
    T = np.fft.fft2(train.astype(float)); X = np.fft.fft2(xt)
    W = (np.conj(T) * X).sum(0) / ((np.abs(T) ** 2).sum(0) + 1e-3 * n_train)
    out = {}
    cands = {'sans': test.astype(float),
             'enseignant': np.concatenate([sim.optimize(test[i:i + 16], H, expo, iters) for i in range(0, n_test, 16)]),
             'appris': np.clip(np.fft.ifft2(W * np.fft.fft2(test.astype(float))).real, 0, 1)}
    for k, x in cands.items():
        pr = sim.printed(x, H, expo)
        m = np.array([metrics.contour_dev(pr[i], test[i], PITCH) for i in range(n_test)])
        out[k] = dict(rms=float(np.sqrt((m[:, 0] ** 2).mean())), p95=float(np.percentile(m[:, 0], 95)), faux=float(m[:, 2].mean()))
    out['sigma_px'] = sig_px
    out['sigma_um'] = sig_px * PITCH
    return out


if __name__ == '__main__':
    sigmas = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]
    t0 = time.time()
    with Pool(4) as p:
        res = p.map(run, sigmas)
    print('durée', round(time.time() - t0), 's')
    print('sigma_px sigma_um | RMS contour um : sans / appris / enseignant | pixels faux %% : sans / appris / enseignant')
    for r in res:
        print('%5.2f %6.0f | %7.1f %7.1f %7.1f | %6.2f %6.2f %6.2f' % (r['sigma_px'], r['sigma_um'], r['sans']['rms'], r['appris']['rms'], r['enseignant']['rms'],
                                                                      r['sans']['faux'], r['appris']['faux'], r['enseignant']['faux']))
    json.dump(res, open('recoverability.json', 'w'), indent=1)
