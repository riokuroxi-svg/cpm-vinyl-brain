# Guía de pruebas — CPM Vinyl Brain 0.3

## Objetivo

Medir si el Cerebro produce recetas reconocibles y limpias antes de comenzar la app Android.

## Conjunto mínimo

Probar al menos:

1. personaje anime con cabello claro;
2. personaje con cabello oscuro o azul;
3. logotipo de pocos colores;
4. animal o mascota estilizada;
5. imagen con fondo no transparente.

## Perfiles

### quick

Prueba de instalación. Menos propuestas y una inicialización. No usar para juzgar calidad final.

### balanced

Iteración de desarrollo.

### quality

Perfil recomendado para evaluación. Usa dos inicializaciones y mayor resolución interna.

## Qué revisar

Calificar de 1 a 5:

- reconocimiento general;
- silueta;
- rostro;
- ojos;
- cabello;
- ropa;
- limpieza de bordes;
- ausencia de manchas translúcidas;
- aprovechamiento de capas;
- semejanza sin mostrar el original.

## Archivos que deben conservarse

- imagen original;
- `run_manifest.json`;
- `FINAL_COMPARISON.png`;
- `final_recipe.json`;
- `region_report.json`;
- calificación humana;
- tiempo de ejecución y dispositivo.

## Criterios iniciales

Una ejecución candidata a aprobar debe cumplir:

- ninguna capa con opacidad menor de 1;
- ninguna figura fuera del catálogo;
- menos de 280 capas para el perfil actual;
- cobertura regional media ≥ 0.80;
- SSIM semántico ≥ 0.80;
- rostro y ojos reconocibles;
- no parecer pintura al óleo.

Las métricas no sustituyen la inspección visual.

## Prueba desde teléfono

1. Abrir `CPM_Brain_0_3_Colab.ipynb` en Google Colab.
2. Ejecutar la instalación.
3. Subir `CPM_Vinyl_Brain_0.3_TestBuild.zip`.
4. Subir la imagen.
5. Ejecutar el perfil `quality`.
6. Descargar el ZIP de resultados.

## Reporte de errores

Si falla la segmentación, indicar:

- qué región confundió;
- color del cabello;
- presencia o ausencia de transparencia;
- si el rostro está de frente o perfil;
- captura de `VISTA_PREVIA_0_2B.png`;
- archivo `layer_graph.json`.

Si falla el ajuste de vinilos, adjuntar `FINAL_COMPARISON.png` y `region_report.json`.
