package com.cpm.brain

import kotlinx.serialization.json.Json
import java.awt.RenderingHints
import java.awt.image.BufferedImage
import javax.imageio.ImageIO
import kotlin.math.floor
import kotlin.math.roundToInt

data class ShapeMask(
    val definition: ShapeDefinition,
    val width: Int,
    val height: Int,
    val alpha: FloatArray
) {
    val aspectRatio: Double get() = width.toDouble() / height

    fun sample(u: Double, v: Double): Double {
        if (u < 0.0 || v < 0.0 || u > 1.0 || v > 1.0) return 0.0
        val x = u * (width - 1)
        val y = v * (height - 1)
        val x0 = floor(x).toInt().coerceIn(0, width - 1)
        val y0 = floor(y).toInt().coerceIn(0, height - 1)
        val x1 = (x0 + 1).coerceAtMost(width - 1)
        val y1 = (y0 + 1).coerceAtMost(height - 1)
        val tx = x - x0
        val ty = y - y0
        val a00 = alpha[y0 * width + x0]
        val a10 = alpha[y0 * width + x1]
        val a01 = alpha[y1 * width + x0]
        val a11 = alpha[y1 * width + x1]
        val top = a00 * (1.0 - tx) + a10 * tx
        val bottom = a01 * (1.0 - tx) + a11 * tx
        return top * (1.0 - ty) + bottom * ty
    }
}

class ShapeLibrary private constructor(
    val catalog: Catalog,
    val masks: List<ShapeMask>
) {
    val byId: Map<String, ShapeMask> = masks.associateBy { it.definition.id }

    companion object {
        private val json = Json { ignoreUnknownKeys = true }

        fun load(maxMaskSide: Int = 192): ShapeLibrary {
            val loader = ShapeLibrary::class.java.classLoader
            val catalogText = loader.getResourceAsStream("catalog.json")
                ?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }
                ?: error("No se encontró catalog.json")
            val catalog = json.decodeFromString<Catalog>(catalogText)
            val masks = catalog.shapes.map { definition ->
                val stream = loader.getResourceAsStream(definition.asset)
                    ?: error("No se encontró el recurso ${definition.asset}")
                val image = stream.use { ImageIO.read(it) }
                    ?: error("No se pudo leer ${definition.asset}")
                createMask(definition, image, maxMaskSide)
            }
            return ShapeLibrary(catalog, masks)
        }

        private fun createMask(definition: ShapeDefinition, source: BufferedImage, maxSide: Int): ShapeMask {
            var minX = source.width
            var minY = source.height
            var maxX = -1
            var maxY = -1
            for (y in 0 until source.height) {
                for (x in 0 until source.width) {
                    val alpha = source.getRGB(x, y) ushr 24 and 0xFF
                    if (alpha > 1) {
                        if (x < minX) minX = x
                        if (y < minY) minY = y
                        if (x > maxX) maxX = x
                        if (y > maxY) maxY = y
                    }
                }
            }
            require(maxX >= minX && maxY >= minY) { "Máscara vacía: ${definition.asset}" }
            val cropped = source.getSubimage(minX, minY, maxX - minX + 1, maxY - minY + 1)
            val scale = minOf(1.0, maxSide.toDouble() / maxOf(cropped.width, cropped.height))
            val width = maxOf(2, (cropped.width * scale).roundToInt())
            val height = maxOf(2, (cropped.height * scale).roundToInt())
            val resized = BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB)
            val graphics = resized.createGraphics()
            graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR)
            graphics.drawImage(cropped, 0, 0, width, height, null)
            graphics.dispose()
            val alpha = FloatArray(width * height)
            for (i in alpha.indices) {
                alpha[i] = ((resized.getRGB(i % width, i / width) ushr 24) and 0xFF) / 255f
            }
            return ShapeMask(definition, width, height, alpha)
        }
    }
}
