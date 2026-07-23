package com.cpm.brain

import kotlin.math.abs
import kotlin.math.cbrt
import kotlin.math.pow
import kotlin.math.roundToInt
import kotlin.math.sqrt

data class Rgb(val r: Int, val g: Int, val b: Int) {
    init {
        require(r in 0..255 && g in 0..255 && b in 0..255)
    }

    fun toHex(): String = "#%02X%02X%02X".format(r, g, b)

    companion object {
        val WHITE = Rgb(255, 255, 255)
        val BLACK = Rgb(0, 0, 0)

        fun parse(text: String): Rgb {
            val clean = text.trim().removePrefix("#")
            require(clean.matches(Regex("[0-9a-fA-F]{6}"))) { "Color HEX inválido: $text" }
            return Rgb(clean.substring(0, 2).toInt(16), clean.substring(2, 4).toInt(16), clean.substring(4, 6).toInt(16))
        }
    }
}

data class Lab(val l: Double, val a: Double, val b: Double)

/** Conversión sRGB ↔ CIELAB D65 y distancia ΔE76. */
object ColorScience {
    private const val XN = 0.95047
    private const val YN = 1.00000
    private const val ZN = 1.08883
    private const val EPSILON = 216.0 / 24389.0
    private const val KAPPA = 24389.0 / 27.0

    fun rgbToLab(rgb: Rgb): Lab = rgbToLab(rgb.r, rgb.g, rgb.b)

    fun rgbToLab(r: Int, g: Int, b: Int): Lab {
        val rl = srgbToLinear(r / 255.0)
        val gl = srgbToLinear(g / 255.0)
        val bl = srgbToLinear(b / 255.0)

        val x = (0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl) / XN
        val y = (0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl) / YN
        val z = (0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl) / ZN

        val fx = labF(x)
        val fy = labF(y)
        val fz = labF(z)
        return Lab(116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))
    }

    fun labToRgb(lab: Lab): Rgb {
        val fy = (lab.l + 16.0) / 116.0
        val fx = fy + lab.a / 500.0
        val fz = fy - lab.b / 200.0
        val x = XN * labInverseF(fx)
        val y = YN * labInverseF(fy)
        val z = ZN * labInverseF(fz)

        val rl =  3.2404542 * x - 1.5371385 * y - 0.4985314 * z
        val gl = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
        val bl =  0.0556434 * x - 0.2040259 * y + 1.0572252 * z
        return Rgb(
            (255.0 * linearToSrgb(rl)).roundToInt().coerceIn(0, 255),
            (255.0 * linearToSrgb(gl)).roundToInt().coerceIn(0, 255),
            (255.0 * linearToSrgb(bl)).roundToInt().coerceIn(0, 255)
        )
    }

    fun deltaE76(a: Lab, b: Lab): Double {
        val dl = a.l - b.l
        val da = a.a - b.a
        val db = a.b - b.b
        return sqrt(dl * dl + da * da + db * db)
    }

    fun deltaE76(r: Int, g: Int, b: Int, targetL: Double, targetA: Double, targetB: Double): Double {
        val lab = rgbToLab(r, g, b)
        val dl = lab.l - targetL
        val da = lab.a - targetA
        val db = lab.b - targetB
        return sqrt(dl * dl + da * da + db * db)
    }

    fun almostEqual(a: Double, b: Double, tolerance: Double = 1e-6): Boolean = abs(a - b) <= tolerance

    private fun srgbToLinear(c: Double): Double =
        if (c <= 0.04045) c / 12.92 else ((c + 0.055) / 1.055).pow(2.4)

    private fun linearToSrgb(c: Double): Double {
        val v = c.coerceIn(0.0, 1.0)
        return if (v <= 0.0031308) 12.92 * v else 1.055 * v.pow(1.0 / 2.4) - 0.055
    }

    private fun labF(t: Double): Double = if (t > EPSILON) cbrt(t) else (KAPPA * t + 16.0) / 116.0

    private fun labInverseF(t: Double): Double {
        val cube = t * t * t
        return if (cube > EPSILON) cube else (116.0 * t - 16.0) / KAPPA
    }
}
