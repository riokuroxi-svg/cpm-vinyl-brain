package com.cpm.brain

import java.awt.Color
import java.awt.RenderingHints
import java.awt.image.BufferedImage
import java.nio.file.Files
import java.nio.file.Path
import javax.imageio.ImageIO
import kotlin.math.roundToInt

class RasterCanvas(
    val width: Int,
    val height: Int,
    val red: IntArray,
    val green: IntArray,
    val blue: IntArray
) {
    init {
        require(width > 0 && height > 0)
        require(red.size == width * height && green.size == red.size && blue.size == red.size)
    }

    constructor(width: Int, height: Int, fill: Rgb) : this(
        width,
        height,
        IntArray(width * height) { fill.r },
        IntArray(width * height) { fill.g },
        IntArray(width * height) { fill.b }
    )

    fun copy(): RasterCanvas = RasterCanvas(width, height, red.copyOf(), green.copyOf(), blue.copyOf())

    fun colorAt(index: Int): Rgb = Rgb(red[index], green[index], blue[index])

    fun set(index: Int, color: Rgb) {
        red[index] = color.r
        green[index] = color.g
        blue[index] = color.b
    }

    fun blend(index: Int, color: Rgb, alpha: Double) {
        val a = alpha.coerceIn(0.0, 1.0)
        val inverse = 1.0 - a
        red[index] = (color.r * a + red[index] * inverse).roundToInt().coerceIn(0, 255)
        green[index] = (color.g * a + green[index] * inverse).roundToInt().coerceIn(0, 255)
        blue[index] = (color.b * a + blue[index] * inverse).roundToInt().coerceIn(0, 255)
    }

    fun toBufferedImage(): BufferedImage {
        val image = BufferedImage(width, height, BufferedImage.TYPE_INT_RGB)
        for (i in red.indices) {
            val rgb = (red[i] shl 16) or (green[i] shl 8) or blue[i]
            image.setRGB(i % width, i / width, rgb)
        }
        return image
    }
}

class TargetLab(val raster: RasterCanvas) {
    val l = DoubleArray(raster.width * raster.height)
    val a = DoubleArray(l.size)
    val b = DoubleArray(l.size)

    init {
        for (i in l.indices) {
            val lab = ColorScience.rgbToLab(raster.red[i], raster.green[i], raster.blue[i])
            l[i] = lab.l
            a[i] = lab.a
            b[i] = lab.b
        }
    }
}

object RasterIO {
    fun loadNormalized(path: Path, size: Int, background: Rgb, cover: Boolean = true): RasterCanvas {
        require(Files.exists(path)) { "No existe la imagen: $path" }
        val source = ImageIO.read(path.toFile()) ?: error("Formato de imagen no compatible: $path")
        val output = BufferedImage(size, size, BufferedImage.TYPE_INT_RGB)
        val graphics = output.createGraphics()
        graphics.color = Color(background.r, background.g, background.b)
        graphics.fillRect(0, 0, size, size)
        graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC)
        graphics.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY)

        val scale = if (cover) {
            maxOf(size.toDouble() / source.width, size.toDouble() / source.height)
        } else {
            minOf(size.toDouble() / source.width, size.toDouble() / source.height)
        }
        val w = (source.width * scale).roundToInt()
        val h = (source.height * scale).roundToInt()
        val x = (size - w) / 2
        val y = (size - h) / 2
        graphics.drawImage(source, x, y, w, h, null)
        graphics.dispose()
        return fromBufferedImage(output)
    }

    fun fromBufferedImage(image: BufferedImage): RasterCanvas {
        val n = image.width * image.height
        val r = IntArray(n)
        val g = IntArray(n)
        val b = IntArray(n)
        for (i in 0 until n) {
            val rgb = image.getRGB(i % image.width, i / image.width)
            r[i] = rgb ushr 16 and 0xFF
            g[i] = rgb ushr 8 and 0xFF
            b[i] = rgb and 0xFF
        }
        return RasterCanvas(image.width, image.height, r, g, b)
    }

    fun savePng(raster: RasterCanvas, path: Path) {
        path.parent?.let { Files.createDirectories(it) }
        ImageIO.write(raster.toBufferedImage(), "png", path.toFile())
    }

    fun saveComparison(target: RasterCanvas, preview: RasterCanvas, path: Path) {
        require(target.width == preview.width && target.height == preview.height)
        val gap = 8
        val output = BufferedImage(target.width * 2 + gap, target.height, BufferedImage.TYPE_INT_RGB)
        val g = output.createGraphics()
        g.color = Color(32, 35, 40)
        g.fillRect(0, 0, output.width, output.height)
        g.drawImage(target.toBufferedImage(), 0, 0, null)
        g.drawImage(preview.toBufferedImage(), target.width + gap, 0, null)
        g.dispose()
        path.parent?.let { Files.createDirectories(it) }
        ImageIO.write(output, "png", path.toFile())
    }
}
