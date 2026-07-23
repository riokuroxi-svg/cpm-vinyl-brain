package com.cpm.brain

import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

object LayerRenderer {
    private data class Geometry(
        val centerX: Double,
        val centerY: Double,
        val widthPx: Double,
        val heightPx: Double,
        val cos: Double,
        val sin: Double,
        val minX: Int,
        val maxX: Int,
        val minY: Int,
        val maxY: Int
    )

    fun currentErrors(canvas: RasterCanvas, target: TargetLab): DoubleArray {
        val result = DoubleArray(canvas.width * canvas.height)
        for (i in result.indices) {
            result[i] = ColorScience.deltaE76(
                canvas.red[i], canvas.green[i], canvas.blue[i],
                target.l[i], target.a[i], target.b[i]
            )
        }
        return result
    }

    fun meanError(errors: DoubleArray): Double = errors.sum() / errors.size

    fun fitColor(candidate: Candidate, target: TargetLab): Rgb {
        val geometry = geometry(candidate, target.raster.width, target.raster.height) ?: return Rgb.WHITE
        var weight = 0.0
        var l = 0.0
        var a = 0.0
        var b = 0.0
        visit(candidate, target.raster.width, geometry) { index, alpha ->
            val w = alpha * alpha
            weight += w
            l += target.l[index] * w
            a += target.a[index] * w
            b += target.b[index] * w
        }
        return if (weight > 1e-8) ColorScience.labToRgb(Lab(l / weight, a / weight, b / weight)) else Rgb.WHITE
    }

    fun evaluate(
        candidate: Candidate,
        color: Rgb,
        canvas: RasterCanvas,
        target: TargetLab,
        currentErrors: DoubleArray
    ): Double {
        val geometry = geometry(candidate, canvas.width, canvas.height) ?: return Double.NEGATIVE_INFINITY
        var improvement = 0.0
        visit(candidate, canvas.width, geometry) { index, maskAlpha ->
            val alpha = (maskAlpha * candidate.opacity).coerceIn(0.0, 1.0)
            if (alpha > 0.002) {
                val inverse = 1.0 - alpha
                val r = (color.r * alpha + canvas.red[index] * inverse).toInt().coerceIn(0, 255)
                val g = (color.g * alpha + canvas.green[index] * inverse).toInt().coerceIn(0, 255)
                val b = (color.b * alpha + canvas.blue[index] * inverse).toInt().coerceIn(0, 255)
                val next = ColorScience.deltaE76(r, g, b, target.l[index], target.a[index], target.b[index])
                improvement += currentErrors[index] - next
            }
        }
        return improvement
    }

    fun applyVisual(candidate: Candidate, canvas: RasterCanvas) {
        val geometry = geometry(candidate, canvas.width, canvas.height) ?: return
        visit(candidate, canvas.width, geometry) { index, maskAlpha ->
            val alpha = (maskAlpha * candidate.opacity).coerceIn(0.0, 1.0)
            if (alpha > 0.002) canvas.blend(index, candidate.color, alpha)
        }
    }

    fun apply(
        candidate: Candidate,
        canvas: RasterCanvas,
        target: TargetLab,
        currentErrors: DoubleArray
    ) {
        val geometry = geometry(candidate, canvas.width, canvas.height) ?: return
        visit(candidate, canvas.width, geometry) { index, maskAlpha ->
            val alpha = (maskAlpha * candidate.opacity).coerceIn(0.0, 1.0)
            if (alpha > 0.002) {
                canvas.blend(index, candidate.color, alpha)
                currentErrors[index] = ColorScience.deltaE76(
                    canvas.red[index], canvas.green[index], canvas.blue[index],
                    target.l[index], target.a[index], target.b[index]
                )
            }
        }
    }

    private inline fun visit(
        candidate: Candidate,
        canvasWidth: Int,
        geometry: Geometry,
        action: (index: Int, alpha: Double) -> Unit
    ) {
        for (y in geometry.minY..geometry.maxY) {
            val py = y + 0.5 - geometry.centerY
            for (x in geometry.minX..geometry.maxX) {
                val px = x + 0.5 - geometry.centerX
                val localX = geometry.cos * px + geometry.sin * py
                val localY = -geometry.sin * px + geometry.cos * py
                val u = localX / geometry.widthPx + 0.5
                val v = localY / geometry.heightPx + 0.5
                if (u in 0.0..1.0 && v in 0.0..1.0) {
                    val alpha = candidate.shape.sample(u, v)
                    if (alpha > 0.002) action(y * canvasWidth + x, alpha)
                }
            }
        }
    }

    private fun geometry(candidate: Candidate, canvasWidth: Int, canvasHeight: Int): Geometry? {
        val widthPx = candidate.width * canvasWidth
        val heightPx = candidate.height * canvasHeight
        if (widthPx < 0.5 || heightPx < 0.5) return null
        val radians = Math.toRadians(candidate.rotationDeg)
        val c = cos(radians)
        val s = sin(radians)
        val halfX = abs(c) * widthPx / 2.0 + abs(s) * heightPx / 2.0
        val halfY = abs(s) * widthPx / 2.0 + abs(c) * heightPx / 2.0
        val cx = candidate.x * canvasWidth
        val cy = candidate.y * canvasHeight
        val minX = max(0, floor(cx - halfX).toInt())
        val maxX = min(canvasWidth - 1, ceil(cx + halfX).toInt())
        val minY = max(0, floor(cy - halfY).toInt())
        val maxY = min(canvasHeight - 1, ceil(cy + halfY).toInt())
        if (minX > maxX || minY > maxY) return null
        return Geometry(cx, cy, widthPx, heightPx, c, s, minX, maxX, minY, maxY)
    }
}
