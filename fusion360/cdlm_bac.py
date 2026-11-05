# -*- coding: utf-8 -*-
"""
Bac CDLM (Continuous Dielectric Liquid Masking) - assemblage paramétrique Fusion 360.

Génère un nouveau document avec 4 composants empilés de haut en bas :
    1. Cadre supérieur de pression (réservoir de résine)
    2. Membrane PFA
    3. Châssis intermédiaire / spacer (chambre à oxygène)
    4. Base optique support

Conventions
-----------
* Toutes les cotes ci-dessous sont en mm. L'API Fusion travaille en cm en interne :
  la conversion est centralisée dans mm().
* Repère monde : Z vers le haut, dessus du cadre supérieur à Z = 0, le bac descend vers -Z.
* Chaque pièce est modélisée dans SON repère local : face supérieure à Z = 0, corps vers -Z,
  centré en XY. La position dans l'assemblage est donnée uniquement par la matrice de
  transformation de l'occurrence (Matrix3D), pas par la géométrie des pièces.
* Aucune méthode obsolète : uniquement sketches sur plans de construction décalés en Z,
  ExtrudeFeatures (setOneSideExtent) et RevolveFeatures (perçages horizontaux).
  Les perçages horizontaux sont volontairement faits en révolution : cela évite toute
  ambiguïté d'orientation (repère / normale) des plans XZ et YZ.

Utilisation : Fusion 360 > Utilities > Scripts and Add-Ins > "+" > choisir ce fichier > Run.
"""
import math
import traceback

import adsk.core
import adsk.fusion

# =============================================================================
# PARAMÈTRES (mm) - modifier ici puis relancer le script
# =============================================================================
# --- Hors-tout commun ---------------------------------------------------------
LENGTH_X = 250.0
WIDTH_Y = 170.0

# --- Matrice de fixation : 20 perçages en périphérie --------------------------
EDGE_OFFSET = 10.0   # distance des axes de perçage aux bords extérieurs
N_HOLES_X = 8        # perçages par grand côté (coins inclus) -> 2 x 8 = 16
N_HOLES_Y = 4        # perçages par petit côté (coins inclus) -> 2 x (4 - 2) = 4  => 20 au total
D_THROUGH = 4.5      # passage de vis M4
D_COUNTERBORE = 8.5  # lamage tête CHC M4
COUNTERBORE_DEPTH = 48.0
D_PILOT = 3.3        # avant-trou taraudage M4
PILOT_DEPTH = 10.0

# --- Composant 1 : cadre supérieur ---------------------------------------------
FRAME_H = 60.0
VAT_X, VAT_Y, VAT_R = 210.0, 130.0, 10.0   # cuve centrale traversante + congés verticaux

# --- Composant 2 : membrane PFA --------------------------------------------------
MEMBRANE_T = 0.075

# --- Composant 3 : spacer ---------------------------------------------------------
SPACER_T = 12.0
CAVITY_X, CAVITY_Y, CAVITY_DEPTH = 190.0, 110.0, 1.2
GROOVE_W, GROOVE_D = 1.8, 1.1
# Axe médian de la gorge de joint (demi-dimensions) : placé au-delà du logement quartz
# (198x118) pour que la gorge du dessous porte sur une face plane de la base.
GROOVE_HALF_X, GROOVE_HALF_Y, GROOVE_CORNER_R = 102.0, 62.0, 5.0
D_M5_TAP = 4.2       # avant-trou M5 (le filetage n'est pas modélisé)
D_M3_TAP = 2.5       # avant-trou M3 (idem)
SLOT_W = 1.0         # fente oblongue de liaison vers la chambre
PORT_BORE_MARGIN = 6.0  # le forage s'arrête à 6 mm du bord de la cavité (sous la cavité)

# --- Composant 4 : base optique -----------------------------------------------------
BASE_T = 14.0
WINDOW_X, WINDOW_Y = 190.0, 110.0
SHOULDER_X, SHOULDER_Y, SHOULDER_DEPTH = 198.0, 118.0, 4.8


# =============================================================================
# OUTILS GÉNÉRIQUES
# =============================================================================
def mm(v):
    """mm -> cm (unité interne de l'API Fusion)."""
    return v / 10.0


def P(x, y):
    """Point3D (mm) dans le plan d'une esquisse parallèle à XY."""
    return adsk.core.Point3D.create(mm(x), mm(y), 0.0)


def offset_plane(comp, z_mm, name):
    """Plan de construction parallèle à XY, décalé de z_mm (signé) dans le repère du composant."""
    planes = comp.constructionPlanes
    inp = planes.createInput()
    inp.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(z_mm)))
    plane = planes.add(inp)
    plane.name = name
    return plane


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


def extrude(comp, profiles, depth_mm, operation, upward=False):
    """
    Extrusion d'un profil (ou d'une ObjectCollection de profils) sur depth_mm.
    upward=False : vers -Z (depuis la face supérieure vers le bas) ; True : vers +Z.
    Toutes les esquisses sont sur des plans parallèles à XY (normale +Z).
    """
    feats = comp.features.extrudeFeatures
    inp = feats.createInput(profiles, operation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByReal(mm(depth_mm)))
    direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if upward
                 else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    inp.setOneSideExtent(extent, direction)
    return feats.add(inp)


def cut(comp, profiles, depth_mm, upward=False):
    return extrude(comp, profiles, depth_mm, adsk.fusion.FeatureOperations.CutFeatureOperation, upward)


# --- Esquisses paramétriques -----------------------------------------------------
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
    # Fermeture du contour : l'extrémité de a4 coïncide avec le départ de l1.
    sk.geometricConstraints.addCoincident(a4.endSketchPoint, l1.startSketchPoint)


def draw_slot(sk, c1, c2, width):
    """Fente oblongue (rainure) entre les centres c1 et c2 (tuples mm), largeur `width`."""
    lines = sk.sketchCurves.sketchLines
    arcs = sk.sketchCurves.sketchArcs
    r = width / 2.0
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    nx, ny = -dy, dx                       # normale = d tourné de +90 deg

    def pt(c, s):                          # c +/- r * normale
        return P(c[0] + s * r * nx, c[1] + s * r * ny)

    lA = lines.addByTwoPoints(pt(c1, -1), pt(c2, -1))                       # côté -n
    aB = arcs.addByCenterStartSweep(P(*c2), lA.endSketchPoint, math.pi)     # bout côté c2 (par +d)
    lC = lines.addByTwoPoints(aB.endSketchPoint, pt(c1, +1))                # côté +n (retour)
    aD = arcs.addByCenterStartSweep(P(*c1), lC.endSketchPoint, math.pi)     # bout côté c1 (par -d)
    sk.geometricConstraints.addCoincident(aD.endSketchPoint, lA.startSketchPoint)


# --- Matrice de fixation -----------------------------------------------------------
def hole_positions():
    """
    20 positions de perçage sur le rectangle de perçage (entraxe EDGE_OFFSET aux bords).
    Grands côtés : N_HOLES_X (coins inclus) ; petits côtés : N_HOLES_Y - 2 (hors coins).
    Retourne (liste de (x, y), liste des abscisses des perçages des grands côtés).
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
    return pts, xs


def cut_hole_pattern(comp, plane, diameter, depth_mm, name, upward=False):
    """Esquisse de 20 cercles sur `plane` + coupe de depth_mm."""
    pts, _ = hole_positions()
    sk = new_sketch(comp, plane, name)
    circles = sk.sketchCurves.sketchCircles
    for (x, y) in pts:
        circles.addByCenterRadius(P(x, y), mm(diameter / 2.0))
    return cut(comp, all_profiles(sk), depth_mm, upward)


# --- Composants / occurrences --------------------------------------------------------
def new_part(root, name, z_top_mm):
    """
    Crée un composant vide, placé par une matrice de transformation (translation Z)
    de sorte que sa face supérieure (Z local = 0) soit à z_top_mm dans l'assemblage.
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


def make_plate(comp, thickness_mm, body_name):
    """Plaque 250 x 170 centrée, face supérieure à Z = 0, épaisseur vers -Z."""
    sk = new_sketch(comp, comp.xYConstructionPlane, 'Contour_250x170')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(LENGTH_X / 2.0, WIDTH_Y / 2.0))
    feat = extrude(comp, sk.profiles.item(0), thickness_mm,
                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = feat.bodies.item(0)
    body.name = body_name
    return body


# =============================================================================
# COMPOSANT 1 - CADRE SUPÉRIEUR DE PRESSION
# =============================================================================
def build_frame(comp):
    make_plate(comp, FRAME_H, 'Cadre_Superieur')
    top = comp.xYConstructionPlane

    # Cuve centrale traversante 210 x 130, congés R10 dans les 4 angles verticaux
    sk = new_sketch(comp, top, 'Cuve_210x130_R10')
    draw_rounded_rect(sk, VAT_X / 2.0, VAT_Y / 2.0, VAT_R)
    cut(comp, sk.profiles.item(0), FRAME_H + 1.0)

    # 20 passages de vis Ø4.5 traversants, puis lamages Ø8.5 x 48 depuis la face supérieure
    cut_hole_pattern(comp, top, D_THROUGH, FRAME_H + 1.0, 'Percages_4_5')
    cut_hole_pattern(comp, top, D_COUNTERBORE, COUNTERBORE_DEPTH, 'Lamages_8_5')


# =============================================================================
# COMPOSANT 2 - MEMBRANE PFA
# =============================================================================
def build_membrane(comp):
    make_plate(comp, MEMBRANE_T, 'Membrane_PFA')
    cut_hole_pattern(comp, comp.xYConstructionPlane, D_THROUGH, MEMBRANE_T + 1.0, 'Percages_4_5')


# =============================================================================
# COMPOSANT 3 - SPACER / CŒUR PNEUMATIQUE
# =============================================================================
def cut_horizontal_bore(comp, plane_z_mm, along, across_mm, start_abs, end_abs, sign, diameter, name):
    """
    Forage horizontal de rayon diameter/2 le long de X ('x') ou de Y ('y'), à la cote
    `across_mm` sur l'autre axe et à l'altitude plane_z_mm. Il part de l'extérieur
    (|coord| = start_abs, au-delà du flanc) jusqu'à |coord| = end_abs, du côté `sign` (+1/-1).
    Réalisé par COUPE EN RÉVOLUTION d'un rectangle dont un côté est l'axe du forage.
    """
    r = diameter / 2.0
    a0, a1 = sign * start_abs, sign * end_abs

    def pt(along_v, across_v):
        return P(along_v, across_v) if along == 'x' else P(across_v, along_v)

    plane = offset_plane(comp, plane_z_mm, name + '_plan')
    sk = new_sketch(comp, plane, name)
    rect = sk.sketchCurves.sketchLines.addTwoPointRectangle(
        pt(a0, across_mm), pt(a1, across_mm + r))

    # Axe de révolution = le côté du rectangle situé à la cote `across_mm`
    axis = None
    for i in range(rect.count):
        ln = rect.item(i)
        s, e = ln.startSketchPoint.geometry, ln.endSketchPoint.geometry
        coord = (lambda p: p.y) if along == 'x' else (lambda p: p.x)
        if abs(coord(s) - mm(across_mm)) < 1e-6 and abs(coord(e) - mm(across_mm)) < 1e-6:
            axis = ln
            break
    if axis is None:
        raise RuntimeError("Axe du forage '{}' introuvable".format(name))

    rev_in = comp.features.revolveFeatures.createInput(
        sk.profiles.item(0), axis, adsk.fusion.FeatureOperations.CutFeatureOperation)
    rev_in.setAngleExtent(False, adsk.core.ValueInput.createByReal(2.0 * math.pi))
    comp.features.revolveFeatures.add(rev_in)


def build_spacer(comp):
    make_plate(comp, SPACER_T, 'Spacer_Pneumatique')
    top = comp.xYConstructionPlane
    bottom = offset_plane(comp, -SPACER_T, 'Face_inferieure')

    # 20 passages de vis Ø4.5 (même matrice que les autres pièces)
    cut_hole_pattern(comp, top, D_THROUGH, SPACER_T + 1.0, 'Percages_4_5')

    # Cavité de la chambre à oxygène 190 x 110, profondeur 1.2 (face supérieure)
    sk = new_sketch(comp, top, 'Cavite_190x110')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(CAVITY_X / 2.0, CAVITY_Y / 2.0))
    cut(comp, sk.profiles.item(0), CAVITY_DEPTH)

    # Gorges de joint torique (1.8 x 1.1) : face supérieure et face inférieure
    for plane, upward, label in ((top, False, 'sup'), (bottom, True, 'inf')):
        sk = new_sketch(comp, plane, 'Gorge_joint_' + label)
        draw_rounded_rect(sk, GROOVE_HALF_X + GROOVE_W / 2.0, GROOVE_HALF_Y + GROOVE_W / 2.0,
                          GROOVE_CORNER_R + GROOVE_W / 2.0)
        draw_rounded_rect(sk, GROOVE_HALF_X - GROOVE_W / 2.0, GROOVE_HALF_Y - GROOVE_W / 2.0,
                          GROOVE_CORNER_R - GROOVE_W / 2.0)
        cut(comp, ring_profile(sk), GROOVE_D, upward)

    # --- Forages pneumatiques horizontaux, à mi-épaisseur -------------------------------
    port_z = -SPACER_T / 2.0
    cav_hx, cav_hy = CAVITY_X / 2.0, CAVITY_Y / 2.0
    end_x = cav_hx - PORT_BORE_MARGIN     # fond de forage (sous la cavité)
    end_y = cav_hy - PORT_BORE_MARGIN
    start_x = LENGTH_X / 2.0 + 1.0        # départ au-delà du flanc (coupe franche)
    start_y = WIDTH_Y / 2.0 + 1.0

    # Abscisse des évents : au milieu de deux perçages de fixation voisins (jeu maximal)
    _, xs = hole_positions()
    mid = N_HOLES_X // 2
    vent_x = (xs[mid] + xs[mid + 1]) / 2.0          # entre l'avant-dernier et le 3e perçage
    vent_xs = (-vent_x, vent_x)

    slots = []   # (centre1, centre2) des fentes oblongues Ø1.0

    # 4 évents M5 sur les grands côtés (flancs Y = +/- 85) : 2 par côté
    for sy in (-1, 1):
        for vx in vent_xs:
            cut_horizontal_bore(comp, port_z, 'y', vx, start_y, end_y, sy, D_M5_TAP,
                                'Event_M5_x{:+.0f}_y{:+d}'.format(vx, sy))
            slots.append(((vx, sy * (end_y + 1.0)), (vx, sy * (cav_hy - 1.5))))

    # 1 port d'injection M5 (flanc court droit, X = +125) et 1 port capteur M3 (gauche, X = -125)
    cut_horizontal_bore(comp, port_z, 'x', 0.0, start_x, end_x, +1, D_M5_TAP, 'Port_injection_M5')
    slots.append(((end_x + 1.0, 0.0), (cav_hx - 1.5, 0.0)))
    cut_horizontal_bore(comp, port_z, 'x', 0.0, start_x, end_x, -1, D_M3_TAP, 'Port_SDP810_M3')
    slots.append(((-(end_x + 1.0), 0.0), (-(cav_hx - 1.5), 0.0)))

    # Fentes oblongues Ø1.0 : du fond de cavité (Z = -1.2) jusqu'à l'axe des forages (Z = -6)
    floor = offset_plane(comp, -CAVITY_DEPTH, 'Fond_cavite')
    sk = new_sketch(comp, floor, 'Fentes_oblongues_1_0')
    for c1, c2 in slots:
        draw_slot(sk, c1, c2, SLOT_W)
    cut(comp, all_profiles(sk), SPACER_T / 2.0 - CAVITY_DEPTH)


# =============================================================================
# COMPOSANT 4 - BASE OPTIQUE SUPPORT
# =============================================================================
def build_base(comp):
    make_plate(comp, BASE_T, 'Base_Optique')
    top = comp.xYConstructionPlane

    # Fenêtre optique traversante 190 x 110
    sk = new_sketch(comp, top, 'Fenetre_190x110')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(WINDOW_X / 2.0, WINDOW_Y / 2.0))
    cut(comp, sk.profiles.item(0), BASE_T + 1.0)

    # Épaulement carreau quartz 198 x 118, profondeur 4.8
    sk = new_sketch(comp, top, 'Epaulement_quartz_198x118')
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(SHOULDER_X / 2.0, SHOULDER_Y / 2.0))
    cut(comp, sk.profiles.item(0), SHOULDER_DEPTH)

    # 20 avant-trous borgnes Ø3.3 x 10 (taraudage M4 final), coïncidents avec la matrice
    cut_hole_pattern(comp, top, D_PILOT, PILOT_DEPTH, 'Avant_trous_3_3')


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

        # Cotes Z de la face supérieure de chaque pièce (empilement vers le bas, haut du cadre à 0)
        z_frame = 0.0
        z_membrane = z_frame - FRAME_H
        z_spacer = z_membrane - MEMBRANE_T
        z_base = z_spacer - SPACER_T

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
            'Fond de la base : {:.3f} mm'.format(z_frame, z_membrane, z_spacer, z_base, z_base - BASE_T))
    except Exception:
        if ui:
            ui.messageBox('Échec du script :\n{}'.format(traceback.format_exc()))
