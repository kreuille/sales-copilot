# -*- coding: utf-8 -*-
"""
Bac CDLM (Continuous Dielectric Liquid Masking) - assemblage paramétrique Fusion 360.

Génère un nouveau document avec 4 composants empilés de haut en bas :
    1. Cadre supérieur de pression (réservoir de résine)
    2. Membrane PFA
    3. Châssis intermédiaire / spacer (chambre à oxygène)
    4. Base optique support

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
GROOVE_HALF_X, GROOVE_HALF_Y, GROOVE_CORNER_R = 102.0, 62.0, 5.0   # axe médian des gorges
WINDOW_X, WINDOW_Y = 190.0, 110.0                 # fenêtre optique
GLASS_X, GLASS_Y, GLASS_T = 224.6, 140.6, 4.6      # plaque de verre / quartz
GLASS_CORNER_R = 18.6                             # rayon des angles du verre
GLASS_CLEARANCE = 0.3                             # jeu par côté dans le logement
SHOULDER_X = GLASS_X + 2 * GLASS_CLEARANCE        # logement du verre (225.2 x 141.2)
SHOULDER_Y = GLASS_Y + 2 * GLASS_CLEARANCE
SHOULDER_R = GLASS_CORNER_R + GLASS_CLEARANCE     # rayon des angles du logement (18.9)

D_M5_TAP = 4.2        # avant-trou M5 (filetage non modélisé)
D_M3_TAP = 2.5        # avant-trou M3 (filetage non modélisé)
PORT_BREAKTHROUGH = 1.0  # les forages dépassent de 1 mm dans la cavité (vide) pour déboucher franchement

# =============================================================================
# USER PARAMETERS Fusion (nom, valeur en mm, commentaire)
# =============================================================================
USER_PARAMS = [
    ('Frame_H', 60.0, "Hauteur du cadre superieur (50 resine + 10 garde)"),
    ('Counterbore_Depth', 48.0, "Profondeur des lamages Ø8.5 (tetes CHC M4)"),
    ('Membrane_T', 0.075, "Epaisseur membrane PFA (75 um)"),
    ('Spacer_T', 12.0, "Epaisseur du spacer pneumatique"),
    ('Groove_D', 1.1, "Profondeur des gorges de joint torique"),
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


def cut_hole_pattern(comp, diameter, depth, name):
    """Esquisse de 20 cercles sur le plan XY + coupe depuis la face supérieure."""
    pts, _, _ = hole_positions()
    sk = new_sketch(comp, comp.xYConstructionPlane, name)
    circles = sk.sketchCurves.sketchCircles
    for (x, y) in pts:
        circles.addByCenterRadius(P(x, y), mm(diameter / 2.0))
    return cut(comp, all_profiles(sk), depth)


# --- Composants / occurrences ---------------------------------------------------------
def new_part(root, name, z_top_mm):
    """
    Crée un composant vide, placé par une matrice de translation Z de sorte que sa face
    supérieure (Z local = 0) soit à z_top_mm dans l'assemblage.
    """
    mat = adsk.core.Matrix3D.create()
    mat.translation = adsk.core.Vector3D.create(0.0, 0.0, mm(z_top_mm))
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


# =============================================================================
# COMPOSANT 1 - CADRE SUPÉRIEUR DE PRESSION
# =============================================================================
def build_frame(comp):
    make_plate(comp, 'Frame_H', 'Cadre_Superieur')

    # Cuve centrale traversante 210 x 130, congés R10 dans les 4 angles verticaux
    sk = new_sketch(comp, comp.xYConstructionPlane, 'Cuve_210x130_R10')
    draw_rounded_rect(sk, VAT_X / 2.0, VAT_Y / 2.0, VAT_R)
    cut(comp, sk.profiles.item(0), 'Frame_H + 1 mm')

    # 20 passages Ø4.5 traversants, puis lamages Ø8.5 x 48 depuis la face supérieure
    cut_hole_pattern(comp, D_THROUGH, 'Frame_H + 1 mm', 'Percages_4_5')
    cut_hole_pattern(comp, D_COUNTERBORE, 'Counterbore_Depth', 'Lamages_8_5')


# =============================================================================
# COMPOSANT 2 - MEMBRANE PFA
# =============================================================================
def build_membrane(comp):
    make_plate(comp, 'Membrane_T', 'Membrane_PFA')
    cut_hole_pattern(comp, D_THROUGH, 'Membrane_T + 1 mm', 'Percages_4_5')


# =============================================================================
# COMPOSANT 3 - SPACER / CŒUR PNEUMATIQUE
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


def build_spacer(comp):
    make_plate(comp, 'Spacer_T', 'Spacer_Pneumatique')
    top = comp.xYConstructionPlane
    spacer_t = p_mm('Spacer_T')

    # 20 passages de vis Ø4.5 (même matrice que les autres pièces)
    cut_hole_pattern(comp, D_THROUGH, 'Spacer_T + 1 mm', 'Percages_4_5')

    # Cavité de la chambre à oxygène 190 x 110 TRAVERSANTE : le spacer est un cadre, sans fond.
    # Le fond de la chambre est la plaque de verre / quartz posée dans la base.
    sk = new_sketch(comp, top, 'Cavite_190x110')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(CAVITY_X / 2.0, CAVITY_Y / 2.0))
    cut(comp, sk.profiles.item(0), 'Spacer_T + 1 mm')

    # Gorges de joint torique 1.8 x 1.1 : face supérieure (départ Z=0, vers le bas) et face
    # inférieure (départ Z=-Spacer_T, vers le haut). Même esquisse XY, décalage de départ.
    gw = 1.8
    for label, start, toward in (('sup', 0.0, -1), ('inf', '-Spacer_T', +1)):
        sk = new_sketch(comp, top, 'Gorge_joint_' + label)
        draw_rounded_rect(sk, GROOVE_HALF_X + gw / 2.0, GROOVE_HALF_Y + gw / 2.0,
                          GROOVE_CORNER_R + gw / 2.0)
        draw_rounded_rect(sk, GROOVE_HALF_X - gw / 2.0, GROOVE_HALF_Y - gw / 2.0,
                          GROOVE_CORNER_R - gw / 2.0)
        cut(comp, ring_profile(sk), 'Groove_D', top, start, toward)

    # --- Évents et ports : forages HORIZONTAUX depuis les flancs, à mi-épaisseur -------------
    # Ils traversent la paroi du spacer et débouchent directement dans la paroi de la cavité
    # (traversante). Rien n'est usiné sur la face supérieure ni sur le fond de la chambre.
    port_z = -spacer_t / 2.0
    cav_hx, cav_hy = CAVITY_X / 2.0, CAVITY_Y / 2.0
    end_x = cav_hx - PORT_BREAKTHROUGH         # fond de forage : juste dans la cavité (vide)
    end_y = cav_hy - PORT_BREAKTHROUGH
    out_x = LENGTH_X / 2.0 + 1.0               # départ au-delà du flanc (coupe franche)
    out_y = WIDTH_Y / 2.0 + 1.0

    _, xs, ys = hole_positions()
    # Évents au milieu de deux perçages de fixation voisins (jeu maximal avec les vis)
    vent_x = (xs[N_HOLES_X // 2 + 1] + xs[N_HOLES_X // 2 + 2]) / 2.0
    # Ports courts au milieu de deux perçages voisins des petits côtés
    port_y = (ys[N_HOLES_Y // 2] + ys[N_HOLES_Y // 2 + 1]) / 2.0

    xz, yz = comp.xZConstructionPlane, comp.yZConstructionPlane

    # 4 évents M5 sur les grands côtés (flancs Y = +/- 85) : 2 par côté
    for sy in (-1, 1):
        for vx in (-vent_x, vent_x):
            cut_bore(comp, xz, (vx, 0.0, port_z), sy * end_y, sy, out_y - end_y, D_M5_TAP,
                     'Event_M5_x{:+.0f}_y{:+d}'.format(vx, sy))

    # Port d'injection M5 (flanc court droit, X=+125) et port capteur SDP810 M3 (gauche, X=-125)
    cut_bore(comp, yz, (0.0, port_y, port_z), +end_x, +1, out_x - end_x, D_M5_TAP, 'Port_injection_M5')
    cut_bore(comp, yz, (0.0, -port_y, port_z), -end_x, -1, out_x - end_x, D_M3_TAP, 'Port_SDP810_M3')


# =============================================================================
# COMPOSANT 4 - BASE OPTIQUE SUPPORT
# =============================================================================
def build_base(comp):
    make_plate(comp, 'Base_T', 'Base_Optique')
    top = comp.xYConstructionPlane

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
        z_membrane = z_frame - p_mm('Frame_H')
        z_spacer = z_membrane - p_mm('Membrane_T')
        z_base = z_spacer - p_mm('Spacer_T')

        parts = (
            ('1_Cadre_Superieur', z_frame, build_frame),
            ('2_Membrane_PFA', z_membrane, build_membrane),
            ('3_Spacer_Pneumatique', z_spacer, build_spacer),
            ('4_Base_Optique', z_base, build_base),
        )
        for name, z_top, builder in parts:
            occ = new_part(root, name, z_top)
            builder(occ.component)

        app.activeViewport.fit()
        ui.messageBox(
            'Bac CDLM généré.\n\n'
            'Z haut de chaque pièce (mm) :\n'
            '  Cadre     : {:.3f}\n  Membrane  : {:.3f}\n  Spacer    : {:.3f}\n  Base      : {:.3f}\n'
            'Fond de la base : {:.3f} mm'.format(
                z_frame, z_membrane, z_spacer, z_base, z_base - p_mm('Base_T')))
    except Exception:
        if ui:
            ui.messageBox('Échec du script :\n{}'.format(traceback.format_exc()))
