import math
import traceback

import adsk.core
import adsk.fusion

# Fusion 360 API works in centimeters internally.
BALL_DIAMETER_MM = 50.0
HOLE_DIAMETER_MM = 2.0


def mm(value):
    return value / 10.0


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)

        root = design.rootComponent
        radius = mm(BALL_DIAMETER_MM) / 2.0
        hole_radius = mm(HOLE_DIAMETER_MM) / 2.0

        # --- 1. Ball: revolve a half-circle around the Y axis -----------------
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.name = "Ball profile"
        p = adsk.core.Point3D.create

        axis_line = sketch.sketchCurves.sketchLines.addByTwoPoints(
            p(0, -radius, 0), p(0, radius, 0)
        )
        sketch.sketchCurves.sketchArcs.addByThreePoints(
            p(0, -radius, 0), p(radius, 0, 0), p(0, radius, 0)
        )

        profile = sketch.profiles.item(0)
        revolves = root.features.revolveFeatures
        rev_input = revolves.createInput(
            profile, axis_line, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        rev_input.setAngleExtent(False, adsk.core.ValueInput.createByReal(2 * math.pi))
        ball_feature = revolves.add(rev_input)
        ball_feature.name = "Ball"
        ball_feature.bodies.item(0).name = "Ball"

        # --- 2. Hole: 2 mm circle on the XZ plane, cut through along Y --------
        hole_sketch = root.sketches.add(root.xZConstructionPlane)
        hole_sketch.name = "Hole profile"
        hole_sketch.sketchCurves.sketchCircles.addByCenterRadius(p(0, 0, 0), hole_radius)

        hole_profile = hole_sketch.profiles.item(0)
        extrudes = root.features.extrudeFeatures
        cut_input = extrudes.createInput(
            hole_profile, adsk.fusion.FeatureOperations.CutFeatureOperation
        )
        # Symmetric about the sketch plane, total length 60 mm (> 50 mm ball),
        # so the hole goes completely through both sides.
        cut_input.setSymmetricExtent(adsk.core.ValueInput.createByReal(mm(60.0)), True)
        cut_feature = extrudes.add(cut_input)
        cut_feature.name = "Through hole"

        app.activeViewport.fit()

    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
