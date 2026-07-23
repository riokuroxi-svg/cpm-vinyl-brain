# CPM Vinyl Brain 0.3 — versión integrada de pruebas

## Alcance finalizado

Esta entrega completa el Cerebro aislado necesario para comenzar pruebas con imágenes. No incluye todavía Android, OCR, overlay ni ejecución en el juego.

Pipeline:

```text
Imagen
  → Analizador progresivo 0.2A
  → 30 subpartes + grafo 0.2B
  → Solucionador semántico multietapa 0.3
  → Receta JSON + vista previa + métricas
```

## Funciones incluidas

- Lienzo vertical sin recorte cuadrado.
- Separación de fondo, cabello, piel, ropa, blancos, acentos y detalles.
- Niveles progresivos: base, estructura, rasgos y cuantizado.
- Cabello posterior, flequillo y mechones laterales.
- Rostro, cuello y piel visible.
- Cofia, mangas, delantal, puños, volantes y moño.
- Ojos izquierdo/derecho subdivididos en blanco, oscuro, celeste y reflejo.
- Cejas, boca, nariz y accesorios.
- Grafo detrás→delante.
- Solucionador limitado a las 9 figuras sólidas.
- Opacidad obligatoria de 100%.
- Políticas de formas según la región.
- Cobertura, overflow, borde y refinamiento por región.
- Varias inicializaciones en perfil de calidad.
- Refinamiento conjunto de las capas de cada región.
- Fases registradas por capa: estructura, rasgos y accesorios.
- Orquestador de un solo comando.
- Perfiles quick, balanced y quality.
- Pruebas unitarias y GitHub Actions.
- Cuaderno Google Colab para ejecutar desde teléfono.

## Demostración de calidad

Perfil: `quality`  
Semilla: `20260720`

- Capas disponibles según regiones: 144.
- Capas finalmente útiles: 127.
- Cobertura regional media: 84.40%.
- Boundary F1 regional: 78.41%.
- SSIM contra objetivo semántico: 0.8608.
- Edge-F1 global: 0.3899.
- MAE semántico: 12.62.
- Todas las capas son sólidas y opacas.
- Tiempo observado en el entorno de desarrollo: aproximadamente 47 segundos para el solucionador de calidad.

## Mejoras respecto a 0.1

- La imagen ya no se genera como pintura translúcida.
- Cada vinilo tiene región y propósito.
- El rostro y los ojos se construyen explícitamente.
- La profundidad controla qué tapa a qué.
- Cabello, piel y ropa no compiten en una sola métrica global.
- Las formas existentes se refinan antes de aceptar la receta.

## Comando completo

```bash
python3 research/analyzer_v02/run_brain.py \
  --input imagen.png \
  --out resultado \
  --shapes src/main/resources/shapes \
  --profile quality \
  --seed 20260720
```

## Salidas

```text
resultado/
├── 01_analysis/
│   ├── VISTA_PREVIA_ANALIZADOR.png
│   ├── regions.json
│   └── masks/
├── 02_subparts/
│   ├── VISTA_PREVIA_0_2B.png
│   ├── layer_graph.json
│   └── masks_0_2B/
├── 03_final/
│   ├── FINAL_COMPARISON.png
│   ├── final_preview.png
│   ├── final_recipe.json
│   └── region_report.json
└── run_manifest.json
```

## Limitaciones que deben medirse durante las pruebas

- El parser clásico usa color y geometría; funciona mejor con ilustraciones anime de colores planos.
- La detección de cabello actual favorece tonos rosas/rojizos. Otros colores pueden necesitar corrección o el backend neuronal planeado.
- La máscara convexa del rostro es una aproximación.
- La forma de cofia, cabello y ropa está limitada por el catálogo disponible.
- Edge-F1 sigue siendo la métrica más débil; los contornos finos necesitan más trabajo.
- Las áreas ocultas no se reconstruyen porque no son necesarias para la composición visible.
- Esta versión no convierte todavía coordenadas normalizadas en valores calibrados del juego.

## Estado de la Puerta B

La infraestructura y el nuevo enfoque estructural quedan listos para evaluación con un conjunto de imágenes. La Puerta B solo debe aprobarse después de probar, como mínimo, cinco objetivos variados y calificarlos visualmente sin enseñar el original al evaluador.
