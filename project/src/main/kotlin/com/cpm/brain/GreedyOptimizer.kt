package com.cpm.brain

import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.pow
import kotlin.random.Random

class GreedyOptimizer(
    private val library: ShapeLibrary,
    private val config: OptimizationConfig
) {
    fun optimize(targetRaster: RasterCanvas, onProgress: (LayerProgress) -> Unit = {}): OptimizationResult {
        require(targetRaster.width == targetRaster.height) { "El prototipo 0.1 usa un lienzo cuadrado" }
        val target = TargetLab(targetRaster)
        val canvas = RasterCanvas(targetRaster.width, targetRaster.height, config.backgroundColor)
        val errors = LayerRenderer.currentErrors(canvas, target)
        val initialMean = LayerRenderer.meanError(errors)
        val random = Random(config.seed)
        val layers = mutableListOf<VinylLayer>()
        val progress = mutableListOf<LayerProgress>()

        optimization@ for (layerIndex in 0 until config.maxLayers) {
            val sampler = ErrorSampler(errors)
            var best: Candidate? = null

            repeat(config.candidatesPerLayer) {
                val anchor = sampler.sample(random)
                val anchorX = (anchor % canvas.width + 0.5) / canvas.width
                val anchorY = (anchor / canvas.width + 0.5) / canvas.height
                val shape = library.masks[random.nextInt(library.masks.size)]
                val longSide = logUniform(random, config.minLongSide, config.maxLongSide)
                val aspect = shape.aspectRatio
                var width = if (aspect >= 1.0) longSide else longSide * aspect
                var height = if (aspect >= 1.0) longSide / aspect else longSide
                width *= logUniform(random, 0.68, 1.48)
                height *= logUniform(random, 0.68, 1.48)
                width = width.coerceIn(0.018, 1.15)
                height = height.coerceIn(0.018, 1.15)

                val jitterX = (random.nextDouble() - 0.5) * width * 0.55
                val jitterY = (random.nextDouble() - 0.5) * height * 0.55
                val opacity = when (shape.definition.kind) {
                    ShapeKind.SOLID -> random.nextDouble(0.76, 1.001).coerceAtMost(1.0)
                    ShapeKind.SOFT, ShapeKind.TEXTURE -> random.nextDouble(0.64, 1.001).coerceAtMost(1.0)
                }
                val raw = Candidate(
                    shape = shape,
                    x = (anchorX + jitterX).coerceIn(-0.08, 1.08),
                    y = (anchorY + jitterY).coerceIn(-0.08, 1.08),
                    width = width,
                    height = height,
                    rotationDeg = random.nextDouble(0.0, 360.0),
                    opacity = opacity
                )
                val color = LayerRenderer.fitColor(raw, target)
                val improvement = LayerRenderer.evaluate(raw, color, canvas, target, errors)
                if (improvement > (best?.improvement ?: 0.0)) {
                    best = raw.copy(color = color, improvement = improvement)
                }
            }

            val chosen = best
            if (chosen == null || chosen.improvement <= 1e-6) break@optimization
            LayerRenderer.apply(chosen, canvas, target, errors)
            val layer = VinylLayer(
                index = layers.size,
                shapeId = chosen.shape.definition.id,
                x = chosen.x,
                y = chosen.y,
                width = chosen.width,
                height = chosen.height,
                rotationDeg = chosen.rotationDeg,
                color = chosen.color.toHex(),
                opacity = chosen.opacity
            )
            layers += layer
            val item = LayerProgress(
                layer = layers.size,
                shapeId = layer.shapeId,
                improvement = chosen.improvement,
                meanDeltaE = LayerRenderer.meanError(errors)
            )
            progress += item
            onProgress(item)
        }

        val estimatedCost = layers.sumOf { layer -> library.byId.getValue(layer.shapeId).definition.cost }
        val finalMean = LayerRenderer.meanError(errors)
        val recipe = Recipe(
            seed = config.seed,
            canvas = CanvasSpec(canvas.width, canvas.height, config.backgroundColor.toHex()),
            layers = layers,
            metrics = RecipeMetrics(
                initialMeanDeltaE = initialMean,
                finalMeanDeltaE = finalMean,
                estimatedCost = estimatedCost,
                requestedLayers = config.maxLayers,
                generatedLayers = layers.size
            )
        )
        return OptimizationResult(recipe, canvas, targetRaster, progress)
    }

    private fun logUniform(random: Random, min: Double, max: Double): Double {
        require(min > 0.0 && max >= min)
        return exp(ln(min) + random.nextDouble() * (ln(max) - ln(min)))
    }

    private class ErrorSampler(errors: DoubleArray) {
        private val cumulative = DoubleArray(errors.size)
        private val total: Double

        init {
            var sum = 0.0
            for (i in errors.indices) {
                // El cuadrado concentra las propuestas en las zonas todavía incorrectas.
                sum += errors[i].pow(2.0) + 1e-5
                cumulative[i] = sum
            }
            total = sum
        }

        fun sample(random: Random): Int {
            val value = random.nextDouble() * total
            var low = 0
            var high = cumulative.lastIndex
            while (low < high) {
                val mid = (low + high) ushr 1
                if (cumulative[mid] < value) low = mid + 1 else high = mid
            }
            return low
        }
    }
}
