"""Réseau (U-Net conditionné par le procédé) qui corrige l'image avant projection.

Principe : le simulateur de la page est différentiable. On l'insère dans la boucle d'entraînement :
    cible -> réseau -> image corrigée -> simulateur (flou, seuil de polymérisation) -> résultat imprimé simulé
et on minimise l'écart entre le résultat simulé et la cible. Aucun « enseignant » n'est nécessaire, et les données
(géométries + paramètres de procédé tirés au hasard) sont générées à la volée : on peut voir des millions d'exemples
sans rien stocker.

  python -m msla_ml.train_unet --steps 40000 --batch 32 --kind mix --out compensator
  (GPU recommandé ; non exécuté dans l'environnement où ce fichier a été écrit : PyTorch n'y est pas installé)

Pour un usage réel :
  1. recalez le simulateur sur votre machine (calibrate.py) et réduisez la plage de randomisation autour de ces valeurs ;
  2. entraînez ; 3. vérifiez sur des pièces imprimées (la simulation ne remplace jamais cette étape).
"""
import argparse, time
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import IterableDataset, DataLoader
from . import shapes, processes as pr, metrics, sim

N = 128
COND = 5   # R_px, sg_px, m0, m2, expo


def psf_freq_t(R, sg, n=N):
    """R, sg : (B,K) -> transferts (B,K,n,n), même formule que sim.psf_freq."""
    f = torch.fft.fftfreq(n, device=R.device)
    rho = torch.sqrt(f[None, :] ** 2 + f[:, None] ** 2)[None, None]
    arg = 2 * np.pi * R[..., None, None] * rho
    safe = torch.clamp(arg, min=1e-6)
    pill = torch.where(arg < 1e-6, torch.ones_like(arg), 2 * torch.special.bessel_j1(safe) / safe)
    return pill * torch.exp(-2 * np.pi ** 2 * sg[..., None, None] ** 2 * rho ** 2)


def hat_t(n=N, device='cpu'):
    t = 2 * (torch.arange(n, device=device) + 0.5) / n
    w = torch.stack([torch.clamp(1 - t, min=0), 1 - (t - 1).abs(), torch.clamp(t - 1, min=0)])
    return w[:, None, :].expand(3, n, n)


def dose_t(x, cond, ws):
    """x (B,1,N,N) ; cond (B,5) = [R, sg, m0, m2, expo]. Retourne la dose (B,1,N,N)."""
    R, sg, m0, m2, ex = [cond[:, i] for i in range(5)]
    m = torch.stack([m0, torch.ones_like(m0), m2], 1)
    H = psf_freq_t(R[:, None] * m, sg[:, None] * m)
    conv = torch.fft.ifft2(torch.fft.fft2(x) * H).real            # (B,3,N,N)
    return ex[:, None, None, None] * (conv * ws[None]).sum(1, keepdim=True)


class Stream(IterableDataset):
    def __init__(self, kind, gap_min, seed):
        self.kind, self.gap_min, self.seed = kind, gap_min, seed

    def __iter__(self):
        info = torch.utils.data.get_worker_info()
        rng = np.random.default_rng(self.seed + (info.id if info else 0) * 7919)
        while True:
            k = self.kind if self.kind != 'mix' else rng.choice(['lcd', 'dlp'])
            p = pr.lcd_params(rng, gap_min=self.gap_min) if k == 'lcd' else pr.dlp_params(rng)
            R, sg, m = pr.sigma_R(p)
            t = shapes.random_shape(rng).astype(np.float32)
            yield torch.from_numpy(t)[None], torch.tensor([R, sg, m[0], m[2], p['dose'] / 2], dtype=torch.float32)


class Block(nn.Module):
    def __init__(s, cin, cout):
        super().__init__()
        s.c1, s.c2 = nn.Conv2d(cin, cout, 3, padding=1), nn.Conv2d(cout, cout, 3, padding=1)
        s.n = nn.GroupNorm(8, cout); s.f = nn.Linear(64, 2 * cout)

    def forward(s, x, c):
        h = F.gelu(s.n(s.c1(x)))
        g, b = s.f(c).chunk(2, 1)
        return F.gelu(s.c2(h * (1 + g[:, :, None, None]) + b[:, :, None, None]))


class UNet(nn.Module):
    def __init__(s, ch=(32, 64, 128, 256)):
        super().__init__()
        s.cond = nn.Sequential(nn.Linear(COND, 64), nn.GELU(), nn.Linear(64, 64), nn.GELU())
        s.e = nn.ModuleList([Block(1, ch[0]), Block(ch[0], ch[1]), Block(ch[1], ch[2]), Block(ch[2], ch[3])])
        s.d = nn.ModuleList([Block(ch[3] + ch[2], ch[2]), Block(ch[2] + ch[1], ch[1]), Block(ch[1] + ch[0], ch[0])])
        s.out = nn.Conv2d(ch[0], 1, 1)

    def forward(s, t, cond):
        c = s.cond(cond)
        h, skips = t, []
        for i, b in enumerate(s.e):
            h = b(h, c)
            if i < 3:
                skips.append(h); h = F.avg_pool2d(h, 2)
        for b, sk in zip(s.d, reversed(skips)):
            h = b(torch.cat([F.interpolate(h, scale_factor=2, mode='bilinear', align_corners=False), sk], 1), c)
        return torch.sigmoid(s.out(h) + 3.0 * (2 * t - 1))      # part de l'identité (image = cible)


def evaluate(net, kind, gap_min, device, n=128, seed=12345):
    rng = np.random.default_rng(seed); ws = hat_t(device=device)
    net.eval(); out = []
    for _ in range(n):
        p = pr.lcd_params(rng, gap_min=gap_min) if kind == 'lcd' else pr.dlp_params(rng)
        R, sg, m = pr.sigma_R(p)
        t = shapes.random_shape(rng).astype(np.float32)
        tt = torch.from_numpy(t)[None, None].to(device); cond = torch.tensor([[R, sg, m[0], m[2], p['dose'] / 2]], dtype=torch.float32, device=device)
        with torch.no_grad():
            x = net(tt, cond)
            a, b = dose_t(tt, cond, ws) > 0.5, dose_t(x, cond, ws) > 0.5
        out.append([metrics.contour_dev(a[0, 0].cpu().numpy(), t > 0.5, p['pitch'])[0], metrics.contour_dev(b[0, 0].cpu().numpy(), t > 0.5, p['pitch'])[0]])
    net.train()
    o = np.array(out)
    return float(np.sqrt((o[:, 0] ** 2).mean())), float(np.sqrt((o[:, 1] ** 2).mean()))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', type=int, default=20000); ap.add_argument('--batch', type=int, default=32); ap.add_argument('--lr', type=float, default=2e-3)
    ap.add_argument('--kind', default='mix', choices=['lcd', 'dlp', 'mix']); ap.add_argument('--gap-min', type=float, default=1.5)
    ap.add_argument('--workers', type=int, default=4); ap.add_argument('--out', default='compensator'); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    net = UNet().to(dev); opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.steps)
    dl = DataLoader(Stream(a.kind, a.gap_min, a.seed), batch_size=a.batch, num_workers=a.workers)
    ws = hat_t(device=dev); t0 = time.time()
    for step, (t, cond) in enumerate(dl, 1):
        t, cond = t.to(dev), cond.to(dev)
        steep = 0.15 - 0.10 * min(1.0, step / (0.7 * a.steps))        # seuil de plus en plus net
        x = net(t, cond)
        cu = torch.sigmoid((dose_t(x, cond, ws) - sim.THR) / steep)
        loss = F.binary_cross_entropy(cu, t)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        if step % 200 == 0:
            print('étape %d loss %.4f (%.0f s)' % (step, loss.item(), time.time() - t0), flush=True)
        if step % 2000 == 0 or step == a.steps:
            for k in (['lcd', 'dlp'] if a.kind == 'mix' else [a.kind]):
                r0, r1 = evaluate(net, k, a.gap_min, dev)
                print('   %s : écart de contour RMS sans correction %.1f µm -> avec le réseau %.1f µm' % (k, r0, r1), flush=True)
        if step >= a.steps:
            break
    torch.save(net.state_dict(), a.out + '.pt')
    net.eval().cpu()
    torch.onnx.export(net, (torch.zeros(1, 1, N, N), torch.zeros(1, COND)), a.out + '.onnx', input_names=['cible', 'procede'], output_names=['image_corrigee'],
                      dynamic_axes={'cible': {0: 'b'}, 'procede': {0: 'b'}, 'image_corrigee': {0: 'b'}}, opset_version=17)
    print('modèle enregistré :', a.out + '.pt', a.out + '.onnx')
