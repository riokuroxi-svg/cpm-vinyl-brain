# CPM Vinyl Brain 0.5 — Optimize & Reduce

## Estado

Versión finalizada para pruebas comparativas. Reemplaza el compilador de capas 0.3; conserva el análisis semántico y el grafo de profundidad.

## Pipeline

```text
Imagen
  → regiones y niveles progresivos
  → 30 subpartes + profundidad
  → baseline estructural 0.3
  → pool virtual sobrecompleto
  → correcciones ADD/CUT
  → mapa dinámico de error
  → importancia por capa
  → Optimize & Reduce
  → recetas 64 / 128 / 256 / 430
```

## Cambios implementados

- Eliminación del límite durante la búsqueda interna.
- Pool virtual de 500 capas en el perfil quality.
- Capas opacas `ADD` y `CUT`.
- Corrección global guiada por el error residual.
- Priorización semántica de ojos, boca, rostro y cabello frontal.
- Selección de componentes de mayor error.
- Mutación de figura, X, Y, escala X/Y y rotación.
- Importancia calculada por el empeoramiento producido al retirar una capa.
- Eliminación iterativa por lotes pequeños.
- Preservación mínima de regiones semánticas durante la reducción.
- Cuatro recetas progresivas.
- Reserva de 20 capas sobre el límite 450 para calibración real en el coche.
- Comparación automática contra el Brain 0.3 con igual presupuesto.

## Resultado de demostración

### Brain 0.3 — 127 capas

- SSIM: 0.7537
- Edge-F1: 0.7704
- MAE: 12.51
- píxeles exactos: 90.57%
- puntuación combinada: 0.8125

### Brain 0.5 — 128 capas

- SSIM: 0.8178
- Edge-F1: 0.8343
- MAE: 5.87
- píxeles exactos: 93.34%
- puntuación combinada: 0.8653

Ganador al mismo presupuesto: **Brain 0.5**.

### Brain 0.5 — 256 capas

- SSIM: 0.8737
- Edge-F1: 0.8943
- MAE: 3.40
- píxeles exactos: 95.51%
- puntuación: 0.9096

### Brain 0.5 — 430 capas

- SSIM: 0.9144
- Edge-F1: 0.9106
- MAE: 2.15
- píxeles exactos: 96.23%
- puntuación: 0.9337
- ADD: 382
- CUT: 48

Las métricas comparan contra el objetivo semántico plano, no contra todos los degradados de la imagen original.

## Interpretación

La mejora no procede solamente de añadir capas. A 128 capas, la versión 0.5 supera a 0.3 porque conserva las piezas más útiles después de construir y reducir un pool mayor. Las capas CUT permiten limpiar invasiones con colores de piel, blanco o fondo.

## Archivos

```text
04_optimize_reduce_v05/
├── recipe_064.json
├── recipe_128.json
├── recipe_256.json
├── recipe_430.json
├── preview_064.png
├── preview_128.png
├── preview_256.png
├── preview_430.png
├── comparison_metrics.json
└── FINAL_COMPARISON_03_VS_05.png
```

## Uso

```bash
python3 research/analyzer_v02/run_brain.py \
  --input imagen.png \
  --out resultado \
  --shapes src/main/resources/shapes \
  --profile quality \
  --seed 20260720
```

El perfil quality ejecuta baseline y Optimize & Reduce. Los perfiles rápidos pueden producir pools menores al objetivo 430 y no deben usarse para juzgar máxima calidad.

## Limitaciones

- Todavía no se han añadido glifos reales del juego.
- La percepción clásica favorece cabello rosa/rojo.
- El objetivo semántico simplifica degradados y sombras.
- Las capas CUT son capas normales del color objetivo, no sustracción real.
- El orden final debe probarse en la rasterización 3D del coche.
- La reducción actual recalcula importancia, pero no ejecuta CMA-ES completo tras cada lote eliminado.

## Decisión

Brain 0.5 es el nuevo baseline oficial. Brain 0.3 se conserva como referencia y fallback. La siguiente fase es probar 0.5 sin cambios sobre imágenes variadas y capturar los glifos reales para una futura versión 0.6.
