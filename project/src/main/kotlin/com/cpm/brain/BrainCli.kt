package com.cpm.brain

import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.Path
import kotlin.io.path.absolutePathString

fun main(args: Array<String>) {
    if (args.isEmpty() || args[0] in setOf("help", "--help", "-h")) {
        printHelp()
        return
    }
    when (args[0]) {
        "generate" -> generate(parseOptions(args.drop(1)))
        "render" -> render(parseOptions(args.drop(1)))
        "catalog" -> printCatalog()
        else -> error("Comando desconocido: ${args[0]}. Usa --help.")
    }
}

private fun generate(options: Map<String, String>) {
    val input = Path(required(options, "input"))
    val out = Path(options["out"] ?: "resultado-cpm")
    val layers = options["layers"]?.toInt() ?: 30
    val size = options["size"]?.toInt() ?: 128
    val candidates = options["candidates"]?.toInt() ?: 140
    val seed = options["seed"]?.toLong() ?: 20260720L
    val background = Rgb.parse(options["background"] ?: "#FFFFFF")
    require(layers in 1..450) { "--layers debe estar entre 1 y 450" }
    require(size in 32..512) { "--size debe estar entre 32 y 512" }
    require(candidates in 10..5000) { "--candidates debe estar entre 10 y 5000" }

    println("Cargando catálogo y 13 máscaras…")
    val library = ShapeLibrary.load()
    val target = RasterIO.loadNormalized(input, size, background, cover = true)
    val config = OptimizationConfig(
        maxLayers = layers,
        candidatesPerLayer = candidates,
        canvasSize = size,
        backgroundColor = background,
        seed = seed
    )
    println("Optimizando ${layers} capas con ${candidates} candidatos por capa…")
    val result = GreedyOptimizer(library, config).optimize(target) { progress ->
        println(
            "Capa %3d | %-22s | ΔE medio %.3f | mejora %.2f".format(
                progress.layer, progress.shapeId, progress.meanDeltaE, progress.improvement
            )
        )
    }

    Files.createDirectories(out)
    RecipeIO.write(result.recipe, out.resolve("receta.json"))
    val previewSize = options["preview-size"]?.toInt() ?: 1024
    val preview = RecipeRenderer(library).render(result.recipe, previewSize)
    val targetLarge = RasterIO.loadNormalized(input, previewSize, background, cover = true)
    RasterIO.savePng(preview, out.resolve("vista_previa.png"))
    RasterIO.savePng(targetLarge, out.resolve("objetivo_normalizado.png"))
    RasterIO.saveComparison(targetLarge, preview, out.resolve("comparacion.png"))
    Files.writeString(
        out.resolve("progreso.csv"),
        buildString {
            appendLine("layer,shapeId,improvement,meanDeltaE")
            result.progress.forEach { appendLine("${it.layer},${it.shapeId},${it.improvement},${it.meanDeltaE}") }
        },
        Charsets.UTF_8
    )
    Files.writeString(out.resolve("resumen.txt"), summary(result.recipe), Charsets.UTF_8)

    println()
    println(summary(result.recipe))
    println("Resultado: ${out.absolutePathString()}")
}

private fun render(options: Map<String, String>) {
    val recipePath = Path(required(options, "recipe"))
    val output = Path(options["output"] ?: "vista_previa_receta.png")
    val recipe = RecipeIO.read(recipePath)
    val size = options["size"]?.toInt() ?: 1024
    val preview = RecipeRenderer(ShapeLibrary.load()).render(recipe, size)
    RasterIO.savePng(preview, output)
    println("Vista previa creada: ${output.absolutePathString()}")
}

private fun printCatalog() {
    val library = ShapeLibrary.load()
    println("Catálogo v${library.catalog.version}: ${library.masks.size} figuras")
    library.masks.forEachIndexed { index, mask ->
        println("%2d. %-24s %-8s %4dx%-4d costo=%d".format(
            index + 1,
            mask.definition.id,
            mask.definition.kind,
            mask.width,
            mask.height,
            mask.definition.cost
        ))
    }
}

private fun summary(recipe: Recipe): String = buildString {
    appendLine("CPM Vinyl Brain — resultado")
    appendLine("Capas generadas: ${recipe.metrics.generatedLayers}/${recipe.metrics.requestedLayers}")
    appendLine("ΔE medio inicial: %.4f".format(recipe.metrics.initialMeanDeltaE))
    appendLine("ΔE medio final:   %.4f".format(recipe.metrics.finalMeanDeltaE))
    appendLine("Costo estimado:   ${recipe.metrics.estimatedCost}")
    append("Semilla:          ${recipe.seed}")
}

private fun parseOptions(args: List<String>): Map<String, String> {
    val result = linkedMapOf<String, String>()
    var i = 0
    while (i < args.size) {
        val arg = args[i]
        require(arg.startsWith("--")) { "Se esperaba una opción --nombre, llegó: $arg" }
        val key = arg.removePrefix("--")
        require(i + 1 < args.size) { "Falta el valor de $arg" }
        result[key] = args[i + 1]
        i += 2
    }
    return result
}

private fun required(options: Map<String, String>, key: String): String =
    options[key] ?: error("Falta la opción obligatoria --$key")

private fun printHelp() {
    println(
        """
        CPM Vinyl Brain 0.1.0

        Generar una receta:
          generate --input imagen.png --out resultado --layers 30 [opciones]

        Opciones:
          --size 128             Resolución interna de optimización (32..512)
          --candidates 140       Propuestas evaluadas por cada capa
          --seed 20260720        Semilla para resultado reproducible
          --background #FFFFFF   Color base del lienzo
          --preview-size 1024    Resolución de las vistas previas

        Renderizar una receta existente:
          render --recipe resultado/receta.json --output preview.png --size 1024

        Ver las figuras disponibles:
          catalog
        """.trimIndent()
    )
}
