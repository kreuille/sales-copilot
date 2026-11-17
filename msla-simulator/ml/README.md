# msla_ml : données, apprentissage et correction d'images pour LCD (MSLA) et DLP

Ce dossier accompagne le simulateur web. Il contient le **même modèle physique**, mais vectorisé pour produire
beaucoup de données et entraîner un modèle qui corrige les images **avant projection**.

## Ce que c'est, et ce que ce n'est pas
- Le modèle simule **l'image au plan de polymérisation** : flou optique (cône de lumière + diffusion pour le LCD, objectif
  pour le DLP), variation du flou sur le champ, dose, seuil de polymérisation.
- Il n'est **pas parfait** et ne peut pas l'être : un modèle appris sur des données simulées corrige le **simulateur**.
  Il ne corrigera votre machine que dans la mesure où le simulateur lui ressemble. Il faut donc :
  1. imprimer des mires, les mesurer, **recaler** le modèle (`calibrate.py`) ;
  2. entraîner autour de ces valeurs (réduire la randomisation) ;
  3. **vérifier sur des pièces imprimées**. La simulation ne remplace jamais cette étape.
- Le modèle est en 2D (plan XY d'une tranche). Le retrait, le décollement du film et la hauteur Z restent dans le simulateur web.

## Contenu
| Fichier | Rôle |
|---|---|
| `sim.py` | Modèle direct (FFT, dose, seuil) et correction optimale par optimisation (« enseignant ») |
| `processes.py` | Procédés LCD (distance ≥ 1,5 mm imposée par défaut) et DLP, avec randomisation de domaine |
| `shapes.py` | Géométries aléatoires : mires, trous, anneaux, polygones, couronnes avec fissures et contacts, formes organiques |
| `metrics.py` | Écart de contour (µm), pixels faux |
| `gen_dataset.py` | Génération massive de jeux de données en fragments `.npz` (parallèle) |
| `recoverability.py` | Mesure ce que la correction récupère selon le flou (résultat : `recoverability.json`) |
| `train_unet.py` | U-Net conditionné par le procédé, entraîné avec le simulateur différentiable dans la boucle (PyTorch) |
| `compensate_slices.py` | Corrige un dossier de tranches PNG |
| `calibrate.py` | Recale le flou, le rayon de cône et l'exposition sur une mire mesurée |

## Utilisation
```bash
pip install numpy scipy pillow          # suffisant pour tout sauf train_unet.py
pip install torch                       # pour train_unet.py (GPU recommandé)

# 1. Jeu de données (cible, paramètres, image corrigée optimale, mesures avant/après)
python -m msla_ml.gen_dataset --n 20000 --kind mix --out data/ --workers 8
python -m msla_ml.gen_dataset --n 1000000 --kind lcd --gap-min 1.5 --no-teacher --out cibles/    # cibles + paramètres seulement

# 2. Ce que la correction peut récupérer selon le flou
python -m msla_ml.recoverability

# 3. Réseau de correction, données générées à la volée (rien à stocker)
python -m msla_ml.train_unet --steps 40000 --batch 32 --kind mix --out compensator

# 4. Recalage sur votre machine, puis correction de vos tranches
python -m msla_ml.calibrate cible.png mesure.png --pitch 50
python -m msla_ml.compensate_slices tranches/ sortie/ --process lcd --params machine.json
```

## Débits mesurés (CPU, 4 coeurs)
- `gen_dataset` avec enseignant (3 PSF, 110 itérations) : environ 4 échantillons/s avec 2 processus. Un million d'exemples
  demande donc plusieurs dizaines d'heures de CPU : pour cette quantité, utilisez `train_unet.py` sur GPU, qui n'a pas besoin de stocker.
- `gen_dataset --no-teacher` : des centaines d'échantillons/s (cibles et paramètres seulement).

## Ce que les mesures montrent (`recoverability.json`, pas de 50 µm)
Écart de contour RMS sur 80 géométries variées, selon le flou σ (en pixels) :

| σ (px) | σ (µm) | sans correction | filtre linéaire appris | correction optimale |
|---|---|---|---|---|
| 0,5 | 25 | 1,6 µm | 0,3 µm | 0 µm |
| 0,75 | 38 | 66 µm | 18 µm | 0 µm |
| 1,0 | 50 | 70 µm | 68 µm | 10 µm |
| 1,5 | 75 | 138 µm | 133 µm | 14 µm |
| 2,0 | 100 | 188 µm | 168 µm | 19 µm |
| 3,0 | 150 | 252 µm | 246 µm | 102 µm |
| 4,0 | 200 | 295 µm | 289 µm | 158 µm |

1. Un filtre **linéaire** appris n'apporte presque rien dès que σ dépasse 1 pixel : la polymérisation est un **seuil**, non linéaire.
   Il faut un modèle non linéaire (le U-Net).
2. La **correction optimale** (borne haute d'un réseau) récupère l'essentiel jusqu'à σ ≈ 2 px, puis échoue : au-delà de
   3 px, l'information des détails fins est perdue, aucune image corrigée ne peut la rendre.
3. Un LCD à 1,5 mm ne peut donc égaler le DLP que si l'optique ramène σ vers 1 pixel (≈ 50 µm) ou moins.

## Non vérifié
`train_unet.py` n'a pas pu être exécuté là où il a été écrit (PyTorch absent) : sa syntaxe est vérifiée, pas son
entraînement. Les autres scripts ont été exécutés (jeu de données de 64 échantillons, `recoverability`, `calibrate`,
`compensate_slices`).
