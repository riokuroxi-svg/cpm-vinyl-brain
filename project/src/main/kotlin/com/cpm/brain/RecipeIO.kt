package com.cpm.brain

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.nio.file.Files
import java.nio.file.Path

object RecipeIO {
    private val json = Json {
        prettyPrint = true
        encodeDefaults = true
        ignoreUnknownKeys = true
    }

    fun encode(recipe: Recipe): String = json.encodeToString(recipe)

    fun decode(text: String): Recipe = json.decodeFromString(text)

    fun write(recipe: Recipe, path: Path) {
        path.parent?.let { Files.createDirectories(it) }
        Files.writeString(path, encode(recipe), Charsets.UTF_8)
    }

    fun read(path: Path): Recipe = decode(Files.readString(path, Charsets.UTF_8))
}

class RecipeRenderer(private val library: ShapeLibrary) {
    fun render(recipe: Recipe, outputSize: Int = recipe.canvas.width): RasterCanvas {
        val canvas = RasterCanvas(outputSize, outputSize, Rgb.parse(recipe.canvas.backgroundColor))
        recipe.layers.sortedBy { it.index }.forEach { layer ->
            val shape = library.byId[layer.shapeId]
                ?: error("La receta usa una figura desconocida: ${layer.shapeId}")
            LayerRenderer.applyVisual(
                Candidate(
                    shape = shape,
                    x = layer.x,
                    y = layer.y,
                    width = layer.width,
                    height = layer.height,
                    rotationDeg = layer.rotationDeg,
                    opacity = layer.opacity,
                    color = Rgb.parse(layer.color)
                ),
                canvas
            )
        }
        return canvas
    }
}
