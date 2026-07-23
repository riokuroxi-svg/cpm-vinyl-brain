package com.cpm.brain

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class BrainCoreTest {
    @Test
    fun catalogLoadsAllThirteenShapes() {
        val library = ShapeLibrary.load(96)
        assertEquals(42, library.masks.size)
        assertNotNull(library.byId["09_gota"])
        assertTrue(library.masks.all { it.alpha.any { alpha -> alpha > 0.5f } })
    }

    @Test
    fun rgbLabRoundTripIsStable() {
        val colors = listOf(Rgb(0, 0, 0), Rgb(255, 255, 255), Rgb(57, 255, 20), Rgb(210, 32, 86))
        colors.forEach { original ->
            val restored = ColorScience.labToRgb(ColorScience.rgbToLab(original))
            assertTrue(kotlin.math.abs(original.r - restored.r) <= 1)
            assertTrue(kotlin.math.abs(original.g - restored.g) <= 1)
            assertTrue(kotlin.math.abs(original.b - restored.b) <= 1)
        }
    }

    @Test
    fun oneLayerCanReduceDeltaE() {
        val library = ShapeLibrary.load(96)
        val targetRaster = RasterCanvas(32, 32, Rgb(220, 30, 40))
        val target = TargetLab(targetRaster)
        val canvas = RasterCanvas(32, 32, Rgb.WHITE)
        val errors = LayerRenderer.currentErrors(canvas, target)
        val before = LayerRenderer.meanError(errors)
        val raw = Candidate(
            shape = library.byId.getValue("13_rectangulo"),
            x = 0.5,
            y = 0.5,
            width = 1.2,
            height = 1.2,
            rotationDeg = 0.0,
            opacity = 1.0
        )
        val color = LayerRenderer.fitColor(raw, target)
        val improvement = LayerRenderer.evaluate(raw, color, canvas, target, errors)
        assertTrue(improvement > 0.0)
        LayerRenderer.apply(raw.copy(color = color), canvas, target, errors)
        assertTrue(LayerRenderer.meanError(errors) < before)
    }

    @Test
    fun recipeJsonRoundTripPreservesLayer() {
        val recipe = Recipe(
            seed = 7,
            canvas = CanvasSpec(128, 128, "#FFFFFF"),
            layers = listOf(VinylLayer(0, "09_gota", .5, .5, .3, .2, 15.0, "#FF0000", .9)),
            metrics = RecipeMetrics(50.0, 20.0, 1000, 1, 1)
        )
        val decoded = RecipeIO.decode(RecipeIO.encode(recipe))
        assertEquals(recipe, decoded)
    }
}
