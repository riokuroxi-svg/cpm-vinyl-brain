# CPM Vinyl Brain

Cerebro aislado para convertir una ilustración en recetas de vinilos restringidas al catálogo de Car Parking Multiplayer.

**Versión de pruebas:** 0.5.0 — Optimize & Reduce  
**Estado:** lista para evaluación con imágenes; todavía no integrada con Android ni con el juego.

```text
Imagen
  → simplificación progresiva
  → 30 subpartes y profundidad
  → baseline semántico
  → 500 capas virtuales ADD/CUT
  → Optimize & Reduce
  → recetas 64 / 128 / 256 / 430
```

## Inicio rápido

```bash
pip install -r requirements-brain.txt

python3 research/analyzer_v02/run_brain.py \
  --input imagen.png \
  --out resultado \
  --shapes src/main/resources/shapes \
  --profile quality \
  --seed 20260720
```

Perfiles:

- `quick`: instalación y depuración;
- `balanced`: iteración;
- `quality`: evaluación oficial, pool virtual de 500 capas.

## Salidas

```text
resultado/
├── 01_analysis/
├── 02_subparts/
├── 03_baseline_v03/
├── 04_optimize_reduce_v05/
│   ├── recipe_064.json
│   ├── recipe_128.json
│   ├── recipe_256.json
│   ├── recipe_430.json
│   ├── preview_064.png
│   ├── preview_128.png
│   ├── preview_256.png
│   ├── preview_430.png
│   ├── comparison_metrics.json
│   └── FINAL_COMPARISON_03_VS_05.png
└── run_manifest.json
```

## Capacidades

- Relación de aspecto vertical.
- Segmentación de cabello, piel, ropa, blancos y accesorios.
- Cabello posterior, flequillo y mechones laterales.
- Rostro, cuello, ropa, cofia, delantal, puños y moño.
- Ojos divididos en blanco, oscuro, iris y reflejo.
- Grafo `detrás → delante`.
- Catálogo ejecutable de 42 máscaras: 13 capturadas y 29 geometrías genéricas recreadas proceduralmente.
- Solo figuras sólidas y opacidad 100% en las recetas finales.
- Operaciones `ADD` y `CUT` mediante capas normales.
- Pool virtual sin presupuesto final.
- Mapa dinámico de error residual.
- Optimización de figura, X/Y, escala X/Y y rotación.
- Importancia por capa y reducción progresiva.
- Reserva de 20 capas del límite 450 para calibración.
- Comparación automática con la versión 0.3.
- Pruebas unitarias, GitHub Actions y Colab.

## Resultado de referencia

A igual presupuesto:

| Motor | Capas | SSIM | Edge-F1 | MAE | Puntuación |
|---|---:|---:|---:|---:|---:|
| Brain 0.3 | 127 | 0.7537 | 0.7704 | 12.51 | 0.8125 |
| Brain 0.5 | 128 | **0.8178** | **0.8343** | **5.87** | **0.8653** |

Brain 0.5 gana al mismo presupuesto.

La receta 430 alcanza SSIM 0.9144, Edge-F1 0.9106 y 96.23% de píxeles semánticos exactos. Incluye 382 capas ADD y 48 CUT.

## Pruebas

```bash
cd research/analyzer_v02
python3 -m unittest -v \
  test_analyzer.py \
  test_subparts.py \
  test_solver_v02c.py \
  test_solver_final.py \
  test_solver_v05.py
```

## Formato de capa 0.5

```json
{
  "index": 210,
  "phase": "gap_correction",
  "operation": "CUT",
  "source": "virtual_overcomplete",
  "regionId": "face",
  "shapeId": "08_circulo",
  "x": 0.51,
  "y": 0.32,
  "width": 0.06,
  "height": 0.04,
  "rotationDeg": 12.0,
  "color": "#F2E9DF",
  "opacity": 1.0,
  "z": 210
}
```

## Limitaciones

- El parser clásico favorece anime plano y cabello rosa/rojo.
- Todavía no se integran glifos de texto reales.
- El objetivo semántico no conserva todos los degradados.
- La receta necesita calibración sobre la carrocería 3D.
- No se ha implementado el Ejecutor Android.
- El pool de 500 capas es virtual; la salida máxima se reduce a 430.

## Documentación

- `docs/FINAL_BRAIN_0_5.md`
- `docs/REPLANTEAMIENTO_CRITICO_BRAIN_0_5.md`
- `docs/GUIA_PRUEBAS_BRAIN_0_3.md`
- `docs/PRIMITIVAS_TEXTO_Y_CORRECCION_0_4.md`

## Siguiente decisión

Probar Brain 0.5 sin modificarlo sobre varias imágenes. Si generaliza, se capturarán fuentes/glifos reales y se iniciará la calibración del editor del juego.
