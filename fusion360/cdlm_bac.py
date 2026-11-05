# -*- coding: utf-8 -*-
"""
Bac CDLM (Continuous Dielectric Liquid Masking) - assemblage paramétrique Fusion 360.

Génère un nouveau document avec les pièces suivantes, empilées de haut en bas :
    1. Cadre supérieur de pression (réservoir de résine), avec un décrochement dans sa face inférieure
    2. Membrane PFA (film), posée au plafond du décrochement
    3. Contre-bride / spacer = PLOT de 1.0 mm qui ENTRE dans le décrochement du cadre (fixation du film)
    4. Joint plat 0.2 mm (étanchéité air entre le plot / le cadre et la base / le verre)
    5. Base optique support (verre)
    + joint torique Ø1.5 et 12 vis M3x8 (pièces de visualisation du montage)

Fixation et tension du film (principe du « petit élément qui rentre dans le grand ») :
  * le film est tendu sur le plot, puis le plot est enfoncé dans le décrochement du cadre : le film est
    PINCÉ RADIALEMENT entre la paroi du plot et celle du décrochement (jeu 0.05 mm < film 0.075 mm), ce
    qui le tend et l'étanche à la périphérie, en dehors des canaux pneumatiques ; l'excédent est détouré ;
  * le plot est tenu par 12 vis M3 propres (taraudées dans le cadre, têtes basses dans la base) ;
  * un joint torique Ø1.5 dans le plafond du décrochement presse le film sur le plot autour de la cuve ;
  * dessous du plot et face du cadre sont coplanaires : le joint plat de 0.2 mm les recouvre ensemble.
Film à 1.2 mm du verre = plot 1.0 + joint plat 0.2 (verre à fleur de la base : 4.6 + joint 0.2 = 4.8).

Principes de robustesse
-----------------------
* AUCUN plan de construction créé (pas de ConstructionPlanes.add), AUCUNE méthode obsolète
  (CurveTreeType, setPositionOnFace...). Toutes les esquisses sont posées sur les plans
  d'origine du composant (xYConstructionPlane, xZConstructionPlane, yZConstructionPlane).
* Les opérations qui ne démarrent pas sur le plan d'esquisse (gorge de la face inférieure,
  fond de cavité, forages latéraux) utilisent le décalage de départ d'une extrusion
  (ExtrudeFeatureInput.startExtent = OffsetStartDefinition) : une seule extrusion, pas de plan.
* Booléens : NewBodyFeatureOperation pour la plaque brute, CutFeatureOperation pour le reste.
* Positionnement : chaque pièce est modélisée dans son repère local (face supérieure à Z=0,
  corps vers -Z) ; l'occurrence est créée avec une Matrix3D de translation Z (empilement).
* Paramètres utilisateur (User Parameters) : épaisseurs et profondeurs sont des paramètres
  Fusion, et les extrusions les référencent par leur nom. Modifier un paramètre dans
  Modify > Change Parameters met à jour les pièces. Les positions/tailles d'esquisse
  (contours, diamètres, matrice de perçage) viennent des constantes ci-dessous : pour
  les modifier, changer la constante et relancer le script.

Unités : constantes en mm ; l'API Fusion travaille en cm (conversion centralisée dans mm()).
Repère : Z vers le haut, dessus du cadre à Z = 0, le bac descend vers -Z.

Utilisation : Fusion 360 > Utilities > Scripts and Add-Ins > "+" > choisir ce fichier > Run.
"""
import math
import traceback

import adsk.core
import adsk.fusion

# =============================================================================
# CONSTANTES GÉOMÉTRIQUES (mm) - dimensions d'esquisse
# =============================================================================
LENGTH_X = 250.0
WIDTH_Y = 170.0

# Matrice de fixation : 20 perçages sur le rectangle situé à EDGE_OFFSET des bords.
# 7 perçages par grand côté (coins inclus) et 5 par petit côté (coins inclus)
# => 2*7 + 2*(5-2) = 20, pas de 39.17 mm (grands côtés) et 38.75 mm (petits côtés) :
# la répartition la plus uniforme possible à 20 perçages sur un rectangle 235 x 155.
# Rangée repoussée vers l'extérieur (7.5 mm du bord au lieu de 10) pour dégager le verre
# 224.6 x 140.6 : 3.25 mm de matière de chaque côté du lamage Ø8.5 (bord / cuve) et entre le
# logement du verre et les avant-trous de la base.
EDGE_OFFSET = 7.5
N_HOLES_X = 7
N_HOLES_Y = 5

D_THROUGH = 4.5       # passage de vis M4
D_COUNTERBORE = 8.5   # lamage tête CHC M4
D_PILOT = 3.3         # avant-trou taraudage M4

VAT_X, VAT_Y, VAT_R = 210.0, 130.0, 10.0          # cuve du cadre (traversante, congés R10)
CAVITY_X, CAVITY_Y = 190.0, 110.0                 # cavité O2 du spacer
# Joint torique UNIQUE, dans la face inférieure du cadre : il presse le film sur la contre-bride.
# Axe médian à 110 x 70 mm (R12), entre la cuve (105 x 65) et la rangée de vis (bord à 115.25).
GROOVE_HALF_X, GROOVE_HALF_Y, GROOVE_CORNER_R, GROOVE_W = 110.0, 70.0, 12.0, 2.0
ORING_CORD = 1.5      # section du joint torique : serrage = 1.5 - gorge 1.15 = 0.35 mm (23 %)
# Plot (contre-bride) qui entre dans le décrochement du cadre. Il englobe la rangée de vis et les canaux
# pneumatiques : la ligne de pincement du film est donc à l'extérieur de tout le reste.
PLUG_HX, PLUG_HY, PLUG_R = 122.5, 81.5, 6.0   # contour du plot (aux murs du cadre : 2.45 mm en X, 3.45 mm en Y)
PINCH_GAP = 0.05                              # jeu radial plot / décrochement (< épaisseur du film : serrage)
M3_LEN, M3_HEAD_D, M3_HEAD_H, M3_SHANK_D = 8.0, 5.5, 2.0, 3.0   # vis M3x8 tête basse (ISO 14580)
D_M3_CLEAR = 3.4      # passage de vis M3 (film, contre-bride)
D_M3_HEAD_HOLE = 5.9  # logement de tête M3 basse Ø5.5 (joint plat, poche de la base) : garde 1.0 mm de joint plat jusqu au pincement
WINDOW_X, WINDOW_Y = 190.0, 110.0                 # fenêtre optique
GLASS_X, GLASS_Y, GLASS_T = 224.6, 140.6, 4.6      # plaque de verre / quartz
GLASS_CORNER_R = 18.6                             # rayon des angles du verre
GLASS_CLEARANCE = 0.3                             # jeu par côté dans le logement
SHOULDER_X = GLASS_X + 2 * GLASS_CLEARANCE        # logement du verre (225.2 x 141.2)
SHOULDER_Y = GLASS_Y + 2 * GLASS_CLEARANCE
SHOULDER_R = GLASS_CORNER_R + GLASS_CLEARANCE     # rayon des angles du logement (18.9)

D_M5_TAP = 4.2        # avant-trou M5 (filetage non modélisé)
D_M3_TAP = 2.5        # avant-trou M3 (filetage non modélisé)
# Circuit pneumatique : le spacer (1.2 mm) ne peut pas recevoir de raccord. Les raccords M5 / M3 sont
# percés dans les flancs de la BASE ; un canal vertical monte de chaque forage jusqu'à une fente
# découpée dans le spacer, qui débouche dans la cavité O2.
# Règle de débit : aucune section ne doit être plus petite que celle du forage taraudé.
#   - le canal vertical a le MÊME diamètre que le forage (pas de rétrécissement) ;
#   - la fente de liaison du spacer est rectangulaire, sa largeur est calculée pour que
#     largeur x Clamp_T >= section du forage (voir connector_width) ;
#   - la liaison débouche directement sur la paroi de la chambre, le répartiteur ne fait que s'y ajouter.
SLOT_W = 1.0          # largeur du répartiteur (fente le long de la paroi)
DISTRIB_LEN = 40.0    # longueur du répartiteur le long de la paroi de la chambre (hors tout)
SLOT_OVERLAP = 0.1    # les fentes débordent de 0.1 mm dans la cavité (vide) pour une ouverture franche
PORT_STOP_Y = 76.0    # axe du canal vertical des voies des grands côtés (|y|)
PORT_STOP_X = 118.0   # axe du canal vertical des voies des petits côtés (|x|)
FLOW_MARGIN = 1.05    # marge de section par rapport au forage

# =============================================================================
# USER PARAMETERS Fusion (nom, valeur en mm, commentaire)
# =============================================================================
USER_PARAMS = [
    ('Frame_H', 60.0, "Hauteur du cadre superieur (50 resine + 10 garde)"),
    ('Counterbore_Depth', 48.0, "Profondeur des lamages Ø8.5 (tetes CHC M4)"),
    ('Membrane_T', 0.075, "Epaisseur membrane PFA (75 um)"),
    ('Clamp_T', 1.0, "Epaisseur de la contre-bride / spacer (rigide)"),
    ('Gasket_T', 0.2, "Epaisseur du joint plat (air)"),
    ('Clamp_Screw_Depth', 8.0, "Profondeur des taraudages M3 de serrage (cadre)"),
    ('Head_Pocket_Depth', 2.5, "Profondeur des poches de tete M3 (base)"),
    ('Groove_D', 1.15, "Profondeur de la gorge de joint torique (cadre)"),
    ('Base_T', 14.0, "Epaisseur de la base optique"),
    ('Shoulder_Depth', 4.8, "Profondeur du logement quartz"),
    ('Pilot_Depth', 10.0, "Profondeur des avant-trous M4 (base)"),
]


def p_mm(name):
    """Valeur numérique (mm) d'un paramètre de USER_PARAMS (pour les calculs Python)."""
    for n, v, _ in USER_PARAMS:
        if n == name:
            return v
    raise KeyError(name)


# =============================================================================
# OUTILS GÉNÉRIQUES
# =============================================================================
def mm(v):
    """mm -> cm (unité interne de l'API Fusion)."""
    return v / 10.0


def P(x, y):
    """Point3D (mm) dans le plan d'une esquisse."""
    return adsk.core.Point3D.create(mm(x), mm(y), 0.0)


def val(v):
    """ValueInput : str -> expression Fusion (ex. 'Frame_H + 1 mm') ; nombre -> mm."""
    if isinstance(v, str):
        return adsk.core.ValueInput.createByString(v)
    return adsk.core.ValueInput.createByReal(mm(v))


def setup_parameters(design):
    """Crée (ou met à jour) les User Parameters."""
    params = design.userParameters
    for name, value, comment in USER_PARAMS:
        expr = '{} mm'.format(value)
        existing = params.itemByName(name)
        if existing:
            existing.expression = expr
        else:
            params.add(name, adsk.core.ValueInput.createByString(expr), 'mm', comment)


def new_sketch(comp, plane, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    return sk


def all_profiles(sk):
    col = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        col.add(sk.profiles.item(i))
    return col


def ring_profile(sk):
    """Profil annulaire (2 boucles) d'une esquisse contenant deux contours imbriqués."""
    for i in range(sk.profiles.count):
        prof = sk.profiles.item(i)
        if prof.profileLoops.count == 2:
            return prof
    raise RuntimeError("Profil annulaire introuvable dans l'esquisse '{}'".format(sk.name))


def axis_and_sign(plane):
    """
    Axe monde (0=X, 1=Y, 2=Z) normal à un plan d'origine et signe de cette normale.
    Évite de supposer l'orientation des plans XZ / YZ.
    """
    n = plane.geometry.normal
    comps = (n.x, n.y, n.z)
    axis = max(range(3), key=lambda i: abs(comps[i]))
    return axis, (1 if comps[axis] > 0 else -1)


def extrude(comp, profiles, depth, operation, plane=None, start=0.0, toward=-1):
    """
    Extrusion à une seule direction d'un profil (ou ObjectCollection de profils).
      plane  : plan d'origine qui porte l'esquisse (défaut : xYConstructionPlane)
      start  : coordonnée MONDE (mm ou expression) de la face de départ sur l'axe normal au plan
               (0 = le plan d'esquisse lui-même)
      toward : sens MONDE de l'extrusion sur cet axe (+1 / -1)
      depth  : profondeur (mm ou expression), toujours positive
    """
    plane = plane or comp.xYConstructionPlane
    _, n_sign = axis_and_sign(plane)

    feats = comp.features.extrudeFeatures
    inp = feats.createInput(profiles, operation)

    if not (isinstance(start, (int, float)) and start == 0):
        if isinstance(start, str):
            offset = start if n_sign > 0 else '-({})'.format(start)
        else:
            offset = start * n_sign
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(val(offset))

    extent = adsk.fusion.DistanceExtentDefinition.create(val(depth))
    along_normal = (toward * n_sign) > 0
    inp.setOneSideExtent(
        extent,
        adsk.fusion.ExtentDirections.PositiveExtentDirection if along_normal
        else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    return feats.add(inp)


def cut(comp, profiles, depth, plane=None, start=0.0, toward=-1):
    return extrude(comp, profiles, depth, adsk.fusion.FeatureOperations.CutFeatureOperation,
                   plane, start, toward)


# --- Esquisses --------------------------------------------------------------------
def draw_rounded_rect(sk, half_x, half_y, r):
    """Rectangle centré à coins arrondis (contour fermé, points chaînés). Dimensions en mm."""
    lines = sk.sketchCurves.sketchLines
    arcs = sk.sketchCurves.sketchArcs
    a, b = half_x, half_y
    q = math.pi / 2.0

    l1 = lines.addByTwoPoints(P(-a + r, -b), P(a - r, -b))                      # bas
    a1 = arcs.addByCenterStartSweep(P(a - r, -b + r), l1.endSketchPoint, q)     # coin bas-droit
    l2 = lines.addByTwoPoints(a1.endSketchPoint, P(a, b - r))                   # droite
    a2 = arcs.addByCenterStartSweep(P(a - r, b - r), l2.endSketchPoint, q)      # coin haut-droit
    l3 = lines.addByTwoPoints(a2.endSketchPoint, P(-a + r, b))                  # haut
    a3 = arcs.addByCenterStartSweep(P(-a + r, b - r), l3.endSketchPoint, q)     # coin haut-gauche
    l4 = lines.addByTwoPoints(a3.endSketchPoint, P(-a, -b + r))                 # gauche
    a4 = arcs.addByCenterStartSweep(P(-a + r, -b + r), l4.endSketchPoint, q)    # coin bas-gauche
    sk.geometricConstraints.addCoincident(a4.endSketchPoint, l1.startSketchPoint)   # fermeture


def draw_rounded_rect_path(sk, half_x, half_y, r):
    """
    Même rectangle arrondi, mais le contour démarre au MILIEU du côté bas (0, -half_y) : le profil du
    balayage (joint torique) est alors esquissé dans le plan YZ d'origine. Retourne la 1re ligne.
    """
    lines = sk.sketchCurves.sketchLines
    arcs = sk.sketchCurves.sketchArcs
    a, b = half_x, half_y
    q = math.pi / 2.0
    l1 = lines.addByTwoPoints(P(0, -b), P(a - r, -b))
    a1 = arcs.addByCenterStartSweep(P(a - r, -b + r), l1.endSketchPoint, q)
    l2 = lines.addByTwoPoints(a1.endSketchPoint, P(a, b - r))
    a2 = arcs.addByCenterStartSweep(P(a - r, b - r), l2.endSketchPoint, q)
    l3 = lines.addByTwoPoints(a2.endSketchPoint, P(-a + r, b))
    a3 = arcs.addByCenterStartSweep(P(-a + r, b - r), l3.endSketchPoint, q)
    l4 = lines.addByTwoPoints(a3.endSketchPoint, P(-a, -b + r))
    a4 = arcs.addByCenterStartSweep(P(-a + r, -b + r), l4.endSketchPoint, q)
    l5 = lines.addByTwoPoints(a4.endSketchPoint, P(0, -b))
    sk.geometricConstraints.addCoincident(l5.endSketchPoint, l1.startSketchPoint)
    return l1


def draw_slot(sk, c1, c2, width):
    """Fente oblongue entre les centres c1 et c2 (tuples mm), largeur `width`."""
    lines = sk.sketchCurves.sketchLines
    arcs = sk.sketchCurves.sketchArcs
    r = width / 2.0
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    nx, ny = -dy, dx                       # normale = direction tournée de +90 deg

    def pt(c, s):
        return P(c[0] + s * r * nx, c[1] + s * r * ny)

    lA = lines.addByTwoPoints(pt(c1, -1), pt(c2, -1))                       # côté -n
    aB = arcs.addByCenterStartSweep(P(*c2), lA.endSketchPoint, math.pi)     # bout côté c2
    lC = lines.addByTwoPoints(aB.endSketchPoint, pt(c1, +1))                # côté +n (retour)
    aD = arcs.addByCenterStartSweep(P(*c1), lC.endSketchPoint, math.pi)     # bout côté c1
    sk.geometricConstraints.addCoincident(aD.endSketchPoint, lA.startSketchPoint)


# --- Matrice de fixation ------------------------------------------------------------
def hole_positions():
    """
    20 positions de perçage (EDGE_OFFSET des bords). Retourne (points, xs, ys) où xs/ys sont
    les rangées de perçages (grands côtés / petits côtés).
    """
    hx = LENGTH_X / 2.0 - EDGE_OFFSET
    hy = WIDTH_Y / 2.0 - EDGE_OFFSET
    xs = [-hx + i * (2 * hx) / (N_HOLES_X - 1) for i in range(N_HOLES_X)]
    ys = [-hy + j * (2 * hy) / (N_HOLES_Y - 1) for j in range(N_HOLES_Y)]
    pts = []
    for x in xs:
        pts += [(x, -hy), (x, hy)]
    for y in ys[1:-1]:
        pts += [(-hx, y), (hx, y)]
    assert len(pts) == 20, "La matrice de fixation doit comporter 20 perçages"
    return pts, xs, ys


def clamp_screw_positions():
    """
    12 vis M3 de serrage du film, sur la MÊME rangée que les vis M4, intercalées entre elles
    (au milieu de deux perçages M4 voisins). On évite les positions des évents et des ports
    (canaux verticaux de la base) : 4 par grand côté, 2 par petit côté.
    """
    hx = LENGTH_X / 2.0 - EDGE_OFFSET
    hy = WIDTH_Y / 2.0 - EDGE_OFFSET
    _, xs, ys = hole_positions()
    mx = [(xs[i] + xs[i + 1]) / 2.0 for i in range(len(xs) - 1)]
    my = [(ys[i] + ys[i + 1]) / 2.0 for i in range(len(ys) - 1)]
    vent_x = (xs[N_HOLES_X // 2 + 1] + xs[N_HOLES_X // 2 + 2]) / 2.0
    port_y = (ys[N_HOLES_Y // 2] + ys[N_HOLES_Y // 2 + 1]) / 2.0
    pts = [(x, sy * hy) for x in mx if abs(abs(x) - vent_x) > 1.0 for sy in (-1, 1)]
    pts += [(sx * hx, y) for y in my if abs(abs(y) - port_y) > 1.0 for sx in (-1, 1)]
    assert len(pts) == 12, "Il doit y avoir 12 vis de serrage"
    return pts


def cut_circles(comp, pts, diameter, depth, name, start=0.0, toward=-1):
    """Esquisse de cercles (centres `pts`, mm) sur le plan XY + coupe (voir extrude())."""
    sk = new_sketch(comp, comp.xYConstructionPlane, name)
    circles = sk.sketchCurves.sketchCircles
    for (x, y) in pts:
        circles.addByCenterRadius(P(x, y), mm(diameter / 2.0))
    return cut(comp, all_profiles(sk), depth, comp.xYConstructionPlane, start, toward)


def cut_hole_pattern(comp, diameter, depth, name):
    """20 cercles de la matrice de fixation M4, coupe depuis la face supérieure."""
    pts, _, _ = hole_positions()
    return cut_circles(comp, pts, diameter, depth, name)


def pneumatic_ports():
    """
    Les 6 voies pneumatiques : 4 évents M5 (grands côtés), 1 injection M5 (flanc court droit),
    1 prise de pression M3 (flanc court gauche). Chaque voie est un dict :
      name, axis ('x' ou 'y' : sens du forage), sign (+1/-1 : flanc), across (cote sur l'autre axe),
      stop (|coord| du fond de forage = position du canal vertical), tap (Ø forage), chan (Ø canal).
    Les évents sont placés au milieu de deux perçages de fixation voisins, les ports courts au
    milieu de deux perçages voisins des petits côtés (jeu maximal avec les vis).
    """
    _, xs, ys = hole_positions()
    vent_x = (xs[N_HOLES_X // 2 + 1] + xs[N_HOLES_X // 2 + 2]) / 2.0
    port_y = (ys[N_HOLES_Y // 2] + ys[N_HOLES_Y // 2 + 1]) / 2.0
    ports = []
    for sy in (-1, 1):
        for vx in (-vent_x, vent_x):
            ports.append(dict(name='Event_M5_x{:+.0f}_y{:+d}'.format(vx, sy), axis='y', sign=sy,
                              across=vx, stop=PORT_STOP_Y, tap=D_M5_TAP, chan=D_M5_TAP))
    ports.append(dict(name='Port_injection_M5', axis='x', sign=+1, across=port_y,
                      stop=PORT_STOP_X, tap=D_M5_TAP, chan=D_M5_TAP))
    ports.append(dict(name='Port_SDP810_M3', axis='x', sign=-1, across=-port_y,
                      stop=PORT_STOP_X, tap=D_M3_TAP, chan=D_M3_TAP))
    return ports


def connector_width(p, thickness):
    """Largeur (mm, arrondie au 0.5 supérieur) de la fente de liaison : section >= forage."""
    area = math.pi * (p['tap'] / 2.0) ** 2 * FLOW_MARGIN
    return math.ceil(area / thickness * 2.0) / 2.0


def port_xy(p):
    """Position (x, y) en mm du canal vertical d'une voie."""
    return (p['across'], p['sign'] * p['stop']) if p['axis'] == 'y' else (p['sign'] * p['stop'], p['across'])


# --- Composants / occurrences ---------------------------------------------------------
def new_part(root, name, z_top_mm, x_mm=0.0, y_mm=0.0):
    """
    Crée un composant vide, placé par une matrice de translation Z de sorte que sa face
    supérieure (Z local = 0) soit à z_top_mm dans l'assemblage.
    """
    mat = adsk.core.Matrix3D.create()
    mat.translation = adsk.core.Vector3D.create(mm(x_mm), mm(y_mm), mm(z_top_mm))
    occ = root.occurrences.addNewComponent(mat)
    occ.component.name = name
    try:
        occ.isGroundToParent = True     # pièces fixes les unes par rapport aux autres
    except Exception:
        pass
    return occ


def make_plate(comp, thickness_param, body_name):
    """Plaque 250 x 170 centrée (NewBody), face supérieure à Z=0, épaisseur vers -Z."""
    sk = new_sketch(comp, comp.xYConstructionPlane, 'Contour_250x170')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(LENGTH_X / 2.0, WIDTH_Y / 2.0))
    feat = extrude(comp, sk.profiles.item(0), thickness_param,
                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = feat.bodies.item(0)
    body.name = body_name
    return body


def make_rounded_plate(comp, hx, hy, r, thickness_param, body_name):
    """Plaque à coins arrondis (demi-dimensions hx, hy, rayon r), centrée, face supérieure à Z=0 (NewBody)."""
    sk = new_sketch(comp, comp.xYConstructionPlane, 'Contour_{:.0f}x{:.0f}'.format(2 * hx, 2 * hy))
    draw_rounded_rect(sk, hx, hy, r)
    feat = extrude(comp, sk.profiles.item(0), thickness_param,
                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = feat.bodies.item(0)
    body.name = body_name
    return body


# =============================================================================
# COMPOSANT 1 - CADRE SUPÉRIEUR DE PRESSION
# =============================================================================
CEILING = '-Frame_H + Clamp_T + Membrane_T'   # cote Z du plafond du décrochement (expression Fusion)


def build_frame(comp):
    make_plate(comp, 'Frame_H', 'Cadre_Superieur')
    top = comp.xYConstructionPlane

    # Cuve centrale traversante 210 x 130, congés R10 dans les 4 angles verticaux
    sk = new_sketch(comp, top, 'Cuve_210x130_R10')
    draw_rounded_rect(sk, VAT_X / 2.0, VAT_Y / 2.0, VAT_R)
    cut(comp, sk.profiles.item(0), 'Frame_H + 1 mm')

    # 20 passages Ø4.5 traversants, puis lamages Ø8.5 x 48 depuis la face supérieure
    cut_hole_pattern(comp, D_THROUGH, 'Frame_H + 1 mm', 'Percages_4_5')
    cut_hole_pattern(comp, D_COUNTERBORE, 'Counterbore_Depth', 'Lamages_8_5')

    # DÉCROCHEMENT de la face inférieure, où le plot entre : contour du plot + jeu de pincement,
    # profondeur = plot + film (le dessous du plot affleure alors la face du cadre).
    sk = new_sketch(comp, top, 'Decrochement_plot')
    draw_rounded_rect(sk, PLUG_HX + PINCH_GAP, PLUG_HY + PINCH_GAP, PLUG_R + PINCH_GAP)
    cut(comp, sk.profiles.item(0), 'Clamp_T + Membrane_T', top, '-Frame_H', +1)

    # 12 taraudages M3 borgnes (avant-trou Ø2.5) depuis le PLAFOND du décrochement
    cut_circles(comp, clamp_screw_positions(), D_M3_TAP, 'Clamp_Screw_Depth', 'Taraudages_M3_serrage',
                start=CEILING, toward=+1)

    # Gorge de joint torique Ø1.5 (2.0 x 1.15) dans le plafond du décrochement : le joint presse le film
    # sur le plot, tout autour de la cuve.
    sk = new_sketch(comp, top, 'Gorge_joint_plafond')
    draw_rounded_rect(sk, GROOVE_HALF_X + GROOVE_W / 2.0, GROOVE_HALF_Y + GROOVE_W / 2.0,
                      GROOVE_CORNER_R + GROOVE_W / 2.0)
    draw_rounded_rect(sk, GROOVE_HALF_X - GROOVE_W / 2.0, GROOVE_HALF_Y - GROOVE_W / 2.0,
                      GROOVE_CORNER_R - GROOVE_W / 2.0)
    cut(comp, ring_profile(sk), 'Groove_D', top, CEILING, +1)


# =============================================================================
# COMPOSANT 2 - MEMBRANE PFA
# =============================================================================
def build_membrane(comp):
    """
    Film PFA, plan au plafond du décrochement, au contour du plot. Dans la réalité il déborde, est
    rabattu le long de la paroi du plot (pincement radial) puis détouré : le rabat n'est pas modélisé.
    """
    make_rounded_plate(comp, PLUG_HX, PLUG_HY, PLUG_R, 'Membrane_T', 'Membrane_PFA')
    cut_hole_pattern(comp, D_THROUGH, 'Membrane_T + 1 mm', 'Percages_4_5')
    # Passages des vis M3 de serrage
    cut_circles(comp, clamp_screw_positions(), D_M3_CLEAR, 'Membrane_T + 1 mm', 'Percages_M3_serrage')


# =============================================================================
# COMPOSANT 3 - CONTRE-BRIDE / SPACER (1.0 mm)
# =============================================================================
def draw_pneumatic_paths(sk, thickness):
    """
    Dessine, dans l'esquisse `sk` (plan XY), les 6 voies pneumatiques de la paroi de la cavité :
      - une fente de liaison rectangulaire, du canal vertical de la base jusqu'à la paroi de la
        chambre, assez large pour ne pas freiner le débit (largeur x `thickness` >= section du forage) ;
      - une fente répartitrice de 1.0 mm, COLLÉE À LA PAROI de la chambre, parallèle au bord et
        ouverte vers l'intérieur de la chambre sur toute sa longueur (DISTRIB_LEN).
    Les formes se chevauchent : couper toutes les régions de l'esquisse coupe leur union.
    """
    cav_hx, cav_hy = CAVITY_X / 2.0, CAVITY_Y / 2.0
    half = (DISTRIB_LEN - SLOT_W) / 2.0           # demi-longueur centre à centre du répartiteur
    off = SLOT_W / 2.0 - SLOT_OVERLAP             # axe du répartiteur : juste derrière la paroi
    rects = sk.sketchCurves.sketchLines
    for p in pneumatic_ports():
        w = connector_width(p, thickness)
        end = p['stop'] + p['chan'] / 2.0 + 0.4   # la liaison recouvre entièrement le canal vertical
        if p['axis'] == 'y':                      # voie sur un grand côté : paroi y = +/- 55
            wall = p['sign'] * (cav_hy + off)
            y1, y2 = sorted((p['sign'] * (cav_hy - SLOT_OVERLAP), p['sign'] * end))
            rects.addTwoPointRectangle(P(p['across'] - w / 2.0, y1), P(p['across'] + w / 2.0, y2))
            draw_slot(sk, (p['across'] - half, wall), (p['across'] + half, wall), SLOT_W)
        else:                                     # voie sur un petit côté : paroi x = +/- 95
            wall = p['sign'] * (cav_hx + off)
            x1, x2 = sorted((p['sign'] * (cav_hx - SLOT_OVERLAP), p['sign'] * end))
            rects.addTwoPointRectangle(P(x1, p['across'] - w / 2.0), P(x2, p['across'] + w / 2.0))
            draw_slot(sk, (wall, p['across'] - half), (wall, p['across'] + half), SLOT_W)


def build_clamp_spacer(comp):
    """
    Plot / contre-bride 1.0 mm, rigide : il entre dans le décrochement du cadre en pinçant le film
    contre sa paroi, et fixe l'écart film-verre. Cavité 190 x 110 traversante (le fond de la chambre
    est le verre), 20 passages M4, 12 passages M3 de serrage, et les 6 voies pneumatiques.
    """
    make_rounded_plate(comp, PLUG_HX, PLUG_HY, PLUG_R, 'Clamp_T', 'Plot_contre_bride')
    top = comp.xYConstructionPlane

    cut_hole_pattern(comp, D_THROUGH, 'Clamp_T + 1 mm', 'Percages_4_5')
    cut_circles(comp, clamp_screw_positions(), D_M3_CLEAR, 'Clamp_T + 1 mm', 'Percages_M3_serrage')

    sk = new_sketch(comp, top, 'Cavite_190x110')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(CAVITY_X / 2.0, CAVITY_Y / 2.0))
    cut(comp, sk.profiles.item(0), 'Clamp_T + 1 mm')

    sk = new_sketch(comp, top, 'Voies_pneumatiques')
    draw_pneumatic_paths(sk, p_mm('Clamp_T'))
    cut(comp, all_profiles(sk), 'Clamp_T + 1 mm')


# =============================================================================
# COMPOSANT 4 - JOINT PLAT (0.2 mm)
# =============================================================================
def build_gasket(comp):
    """
    Joint plat 0.2 mm (feuille silicone / PTFE) entre la contre-bride et la base : étanchéité à l'air.
    Découpes : ouverture 190 x 110, voies pneumatiques (mêmes formes que la contre-bride, pour laisser
    passer l'air jusqu'aux canaux de la base), 20 passages M4, 12 logements de tête M3.
    """
    make_plate(comp, 'Gasket_T', 'Joint_plat')
    top = comp.xYConstructionPlane

    cut_hole_pattern(comp, D_THROUGH, 'Gasket_T + 1 mm', 'Percages_4_5')
    cut_circles(comp, clamp_screw_positions(), D_M3_HEAD_HOLE, 'Gasket_T + 1 mm', 'Logements_tetes_M3')

    sk = new_sketch(comp, top, 'Ouverture_190x110')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(CAVITY_X / 2.0, CAVITY_Y / 2.0))
    cut(comp, sk.profiles.item(0), 'Gasket_T + 1 mm')

    sk = new_sketch(comp, top, 'Voies_pneumatiques')
    draw_pneumatic_paths(sk, p_mm('Clamp_T'))
    cut(comp, all_profiles(sk), 'Gasket_T + 1 mm')


# =============================================================================
# JOINT TORIQUE (1.5 mm) ET VIS M3 DE SERRAGE : pièces de visualisation du montage
# =============================================================================
def build_oring(comp):
    """
    Joint torique Ø1.5 : balayage d'un cercle le long de l'axe médian de la gorge du cadre
    (rectangle 110 x 70, R12), à plat dans le plan XY local. Le profil est esquissé dans le plan YZ
    d'origine, au milieu du côté bas, point de départ du chemin. Le joint est modélisé non comprimé :
    son recouvrement avec le cadre et le film représente l'écrasement.
    """
    sk = new_sketch(comp, comp.xYConstructionPlane, 'Chemin_joint')
    first = draw_rounded_rect_path(sk, GROOVE_HALF_X, GROOVE_HALF_Y, GROOVE_CORNER_R)
    path = comp.features.createPath(first, True)

    yz = comp.yZConstructionPlane
    sp = new_sketch(comp, yz, 'Section_joint')
    c = sp.modelToSketchSpace(adsk.core.Point3D.create(0.0, mm(-GROOVE_HALF_Y), 0.0))
    sp.sketchCurves.sketchCircles.addByCenterRadius(c, mm(ORING_CORD / 2.0))

    sweeps = comp.features.sweepFeatures
    inp = sweeps.createInput(sp.profiles.item(0), path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    feat = sweeps.add(inp)
    feat.bodies.item(0).name = 'Joint_torique_1_5'


def build_screw(comp):
    """Vis M3x8 tête basse : axe en Z, plan de portée de la tête à Z=0, tige vers +Z, tête vers -Z."""
    sk = new_sketch(comp, comp.xYConstructionPlane, 'Tige')
    sk.sketchCurves.sketchCircles.addByCenterRadius(P(0, 0), mm(M3_SHANK_D / 2.0))
    feat = extrude(comp, sk.profiles.item(0), M3_LEN, adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                   comp.xYConstructionPlane, 0.0, +1)
    feat.bodies.item(0).name = 'Vis_M3x8'
    sk = new_sketch(comp, comp.xYConstructionPlane, 'Tete')
    sk.sketchCurves.sketchCircles.addByCenterRadius(P(0, 0), mm(M3_HEAD_D / 2.0))
    extrude(comp, sk.profiles.item(0), M3_HEAD_H, adsk.fusion.FeatureOperations.JoinFeatureOperation,
            comp.xYConstructionPlane, 0.0, -1)


# =============================================================================
# COMPOSANT 5 - BASE OPTIQUE SUPPORT
# =============================================================================
def cut_bore(comp, plane, center_mm, start, toward, depth_mm, diameter, name):
    """
    Forage horizontal (cylindre) par extrusion d'un cercle esquissé sur un plan d'origine
    (XZ pour un forage le long de Y, YZ pour un forage le long de X).
      center_mm : centre du cercle en coordonnées MONDE (x, y, z) en mm, sur le plan d'origine
      start     : coordonnée monde (mm) de la face de départ sur l'axe du forage
      toward    : sens monde de l'extrusion (+1 / -1) ; depth_mm : longueur du forage
    Le centre est converti dans l'espace de l'esquisse par modelToSketchSpace, ce qui évite
    toute hypothèse sur l'orientation des axes du plan.
    """
    sk = new_sketch(comp, plane, name)
    c = sk.modelToSketchSpace(adsk.core.Point3D.create(*[mm(v) for v in center_mm]))
    sk.sketchCurves.sketchCircles.addByCenterRadius(c, mm(diameter / 2.0))
    cut(comp, sk.profiles.item(0), depth_mm, plane, start, toward)


def build_base(comp):
    make_plate(comp, 'Base_T', 'Base_Optique')
    top = comp.xYConstructionPlane
    base_t = p_mm('Base_T')

    # Fenêtre optique traversante 190 x 110
    sk = new_sketch(comp, top, 'Fenetre_190x110')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(WINDOW_X / 2.0, WINDOW_Y / 2.0))
    cut(comp, sk.profiles.item(0), 'Base_T + 1 mm')

    # Logement du verre 224.6 x 140.6 (+ jeu), angles R18.6 (+ jeu), profondeur Shoulder_Depth
    sk = new_sketch(comp, top, 'Logement_verre')
    draw_rounded_rect(sk, SHOULDER_X / 2.0, SHOULDER_Y / 2.0, SHOULDER_R)
    cut(comp, sk.profiles.item(0), 'Shoulder_Depth')

    # 20 avant-trous borgnes Ø3.3 x 10 (taraudage M4 final), coïncidents avec la matrice
    cut_hole_pattern(comp, D_PILOT, 'Pilot_Depth', 'Avant_trous_3_3')

    # 12 poches Ø6.4 pour les têtes basses des vis M3 de serrage (elles dépassent sous la contre-bride)
    cut_circles(comp, clamp_screw_positions(), D_M3_HEAD_HOLE, 'Head_Pocket_Depth', 'Poches_tetes_M3')

    # --- Raccords pneumatiques M5 / M3 : forages horizontaux dans les flancs de la base --------
    # (à mi-épaisseur), arrêtés à PORT_STOP_* ; un canal vertical monte ensuite jusqu'à la face
    # supérieure, sous la fente correspondante du spacer.
    port_z = -base_t / 2.0
    out_x = LENGTH_X / 2.0 + 1.0           # départ au-delà du flanc (coupe franche)
    out_y = WIDTH_Y / 2.0 + 1.0
    xz, yz = comp.xZConstructionPlane, comp.yZConstructionPlane
    ports = pneumatic_ports()
    for p in ports:
        # Le forage va jusqu'au bord intérieur du canal (stop - rayon) : le canal, de même
        # diamètre, tombe entièrement dans le forage -> coude sans rétrécissement.
        end = p['stop'] - p['tap'] / 2.0
        if p['axis'] == 'y':
            cut_bore(comp, xz, (p['across'], 0.0, port_z), p['sign'] * end, p['sign'],
                     out_y - end, p['tap'], p['name'])
        else:
            cut_bore(comp, yz, (0.0, p['across'], port_z), p['sign'] * end, p['sign'],
                     out_x - end, p['tap'], p['name'])

    # Canaux verticaux (même Ø que le forage) de la face supérieure jusqu'au fond du forage
    for tap in sorted({p['tap'] for p in ports}, reverse=True):
        sk = new_sketch(comp, top, 'Canaux_verticaux_D{}'.format(tap))
        for p in (q for q in ports if q['tap'] == tap):
            x, y = port_xy(p)
            sk.sketchCurves.sketchCircles.addByCenterRadius(P(x, y), mm(tap / 2.0))
        cut(comp, all_profiles(sk), 'Base_T / 2 + {} mm'.format(tap / 2.0))


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================
def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = 'Bac_CDLM'
        design = adsk.fusion.Design.cast(app.activeProduct)
        try:
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType   # historique paramétrique
        except Exception:
            pass
        root = design.rootComponent

        setup_parameters(design)

        # Cote Z de la face supérieure de chaque pièce (empilement vers le bas, haut du cadre à 0)
        z_frame = 0.0
        # Le plot affleure la face inférieure du cadre ; le film est entre le plot et le plafond du décrochement.
        z_ceiling = z_frame - p_mm('Frame_H') + p_mm('Clamp_T') + p_mm('Membrane_T')
        z_membrane = z_ceiling
        z_clamp = z_membrane - p_mm('Membrane_T')
        z_gasket = z_clamp - p_mm('Clamp_T')            # = face inférieure du cadre
        z_base = z_gasket - p_mm('Gasket_T')

        parts = (
            ('1_Cadre_Superieur', z_frame, build_frame),
            ('2_Membrane_PFA', z_membrane, build_membrane),
            ('3_Plot_Contre_Bride', z_clamp, build_clamp_spacer),
            ('4_Joint_Plat', z_gasket, build_gasket),
            ('5_Base_Optique', z_base, build_base),
        )
        for name, z_top, builder in parts:
            occ = new_part(root, name, z_top)
            builder(occ.component)

        # Pièces de visualisation (joint torique, vis M3) : une erreur ici n'arrête pas l'assemblage.
        warnings = []
        try:
            # centre de la section du joint : à mi-hauteur entre le fond de gorge et le dessus du film
            z_oring = z_ceiling + p_mm('Groove_D') / 2.0
            occ = new_part(root, '6_Joint_torique_1_5', z_oring)
            build_oring(occ.component)
        except Exception:
            warnings.append("Joint torique non généré :\n" + traceback.format_exc(limit=2))
        try:
            positions = clamp_screw_positions()          # plan de portée des têtes = dessous de la contre-bride
            first = new_part(root, '7_Vis_M3x8', z_gasket, positions[0][0], positions[0][1])
            build_screw(first.component)
            for (x, y) in positions[1:]:
                mat = adsk.core.Matrix3D.create()
                mat.translation = adsk.core.Vector3D.create(mm(x), mm(y), mm(z_gasket))
                root.occurrences.addExistingComponent(first.component, mat)
        except Exception:
            warnings.append("Vis M3 non générées :\n" + traceback.format_exc(limit=2))

        app.activeViewport.fit()
        ui.messageBox(
            'Bac CDLM généré.\n\n'
            'Z haut de chaque pièce (mm) :\n'
            '  Cadre              : {:.3f}\n  Membrane           : {:.3f}\n'
            '  Contre-bride/spacer: {:.3f}\n  Joint plat         : {:.3f}\n  Base               : {:.3f}\n'
            'Fond de la base : {:.3f} mm\n'
            'Ecart film - verre : {:.2f} mm{}'.format(
                z_frame, z_membrane, z_clamp, z_gasket, z_base, z_base - p_mm('Base_T'),
                p_mm('Clamp_T') + p_mm('Gasket_T'),
                ('\n\n' + '\n'.join(warnings)) if warnings else ''))
    except Exception:
        if ui:
            ui.messageBox('Échec du script :\n{}'.format(traceback.format_exc()))
