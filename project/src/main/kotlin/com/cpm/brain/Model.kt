package com.cpm.brain

import kotlinx.serialization.Serializable

@Serializable
data class Catalog(
    val version: Int,
    val shapes: List<ShapeDefinition>
)

@Serializable
data class ShapeDefinition(
    val id: String,
    val name: String,
    val asset: String,
    val kind: ShapeKind,
    val cost: Int
)

@Serializable
enum class ShapeKind { SOLID, SOFT, TEXTURE }

@Serializable
data class CanvasSpec(
    val width: Int,
    val height: Int,
    val backgroundColor: String
)

@Serializable
data class VinylLayer(
    val index: Int,
    val shapeId: String,
    /** Centro horizontal normalizado, 0..1. */
    val x: Double,
    /** Centro vertical normalizado, 0..1. */
    val y: Double,
    /** Ancho normalizado respecto al lienzo. */
    val width: Double,
    /** Alto normalizado respecto al lienzo. */
    val height: Double,
    val rotationDeg: Double,
    val color: String,
    val opacity: Double = 1.0
)

@Serializable
data class RecipeMetrics(
    val initialMeanDeltaE: Double,
    val finalMeanDeltaE: Double,
    val estimatedCost: Int,
    val requestedLayers: Int,
    val generatedLayers: Int
)

@Serializable
data class Recipe(
    val format: String = "cpm-vinyl-recipe",
    val version: Int = 1,
    val generator: String = "cpm-vinyl-brain/0.1.0",
    val seed: Long,
    val canvas: CanvasSpec,
    val layers: List<VinylLayer>,
    val metrics: RecipeMetrics
)

data class OptimizationConfig(
    val maxLayers: Int = 30,
    val candidatesPerLayer: Int = 140,
    val minLongSide: Double = 0.055,
    val maxLongSide: Double = 0.72,
    val canvasSize: Int = 128,
    val backgroundColor: Rgb = Rgb.WHITE,
    val seed: Long = 20260720L
)

data class Candidate(
    val shape: ShapeMask,
    val x: Double,
    val y: Double,
    val width: Double,
    val height: Double,
    val rotationDeg: Double,
    val opacity: Double,
    val color: Rgb = Rgb.WHITE,
    val improvement: Double = Double.NEGATIVE_INFINITY
)

data class OptimizationResult(
    val recipe: Recipe,
    val preview: RasterCanvas,
    val target: RasterCanvas,
    val progress: List<LayerProgress>
)

data class LayerProgress(
    val layer: Int,
    val shapeId: String,
    val improvement: Double,
    val meanDeltaE: Double
)
