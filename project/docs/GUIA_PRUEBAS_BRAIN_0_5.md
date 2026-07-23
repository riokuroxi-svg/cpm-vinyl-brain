# Guía de pruebas — CPM Vinyl Brain 0.5

## Objetivo

Medir generalización, calidad por presupuesto y utilidad de ADD/CUT antes de implementar Android.

## Imágenes mínimas

1. anime con cabello rosa/claro;
2. anime con cabello azul, negro o rubio;
3. personaje de perfil;
4. logotipo plano;
5. imagen con fondo opaco/no transparente.

## Ejecución oficial

```bash
python3 research/analyzer_v02/run_brain.py \
  --input imagen.png \
  --out resultado \
  --shapes src/main/resources/shapes \
  --profile quality \
  --seed 20260720
```

No evaluar calidad con `quick`.

## Revisar las cuatro recetas

- 64: silueta y colores principales.
- 128: comparación justa con el baseline 0.3.
- 256: detalles principales.
- 430: máxima fidelidad y 20 capas reservadas.

## Calificación humana 1–5

- reconocimiento sin mostrar original;
- proporción;
- silueta;
- rostro;
- ojos;
- cabello;
- ropa;
- ausencia de huecos;
- limpieza de CUT/mascarado;
- semejanza general.

## Archivos a conservar

- imagen;
- `run_manifest.json`;
- `04_optimize_reduce_v05/FINAL_COMPARISON_03_VS_05.png`;
- las cuatro recetas;
- `comparison_metrics.json`;
- tiempo y dispositivo;
- calificación humana.

## Criterios provisionales de aprobación

Para 128 capas:

- superar la puntuación del baseline 0.3;
- SSIM semántico ≥ 0.78;
- Edge-F1 ≥ 0.75;
- opacidad 100%;
- ojos y rostro reconocibles.

Para 430 capas:

- SSIM ≥ 0.88;
- Edge-F1 ≥ 0.85;
- MAE ≤ 5;
- ningún hueco grande visible;
- máximo 430 capas.

Las métricas no sustituyen la inspección visual.

## Fallos a reportar

### Percepción

Adjuntar `01_analysis` y `02_subparts` si confunde cabello, piel, fondo o ropa.

### Compilación

Adjuntar recetas y comparación si la segmentación es correcta pero el ensamblaje falla.

### Reducción

Si 430 es bueno pero 128 destruye una parte importante, reportar la región y revisar la función de importancia.

### CUT

Si una capa correctora tapa un detalle correcto, indicar el índice y la región de esa capa.
