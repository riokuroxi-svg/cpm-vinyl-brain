# Manual de uso y continuación

## A. Ejecutar el Brain funcional actual

```bash
cd project
pip install -r requirements-brain.txt
./run_brain.sh test_inputs/imagen.png resultado quality
```

Salida principal:

```text
resultado/04_optimize_reduce_v05/
```

Usar solo como baseline, no como calidad final.

## B. Ejecutar el experimento diferenciable

Recomendado en Google Colab/GPU:

```bash
pip install -r requirements-diff.txt
python3 research/diff_brain/optimize_block.py \
 --shapes src/main/resources/shapes \
 --target bloque_target.png \
 --allowed-mask bloque_mask.png \
 --out resultado_bloque \
 --layers 25 \
 --steps 1200
```

Interpretación:

- `preview.png`: render suave;
- `recipe_soft.json`: parámetros todavía no discretos;
- no ejecutar directamente en CPM;
- elegir figura argmax, forzar opacidad 1 y refinar.

## C. Agregar máscaras propias

1. Colocar figura blanca sobre base negra en CPM.
2. Captura completa sin editar.
3. Usar:

```bash
python3 research/cpm_capture/mask_extractor.py \
 --image captura.png --roi x,y,w,h \
 --mode white-on-dark --out nueva_forma.png
```

4. Añadir PNG a `src/main/resources/shapes/`.
5. Añadir entrada a `catalog.json`.
6. Añadir ID a `SOLID_SHAPES` si es sólida.
7. Ejecutar tests.

## D. Regenerar catálogo geométrico

```bash
python3 research/generate_public_geometric_shapes.py
```

No reemplazar las 13 originales sin comparación visual.

## E. Capturar catálogo del juego

```bash
python3 research/cpm_capture/catalog_extractor.py catalogo.mp4 \
 --out catalog_output
```

Revisar hoja de contacto; no asumir deduplicación perfecta.

## F. Qué mejorar

1. Parser con fondo opaco y cabello de cualquier color.
2. Glifo `(` real.
3. Line art diferenciable.
4. Ojos con landmarks.
5. Fill solver dentro de contornos.
6. Ensamblaje de bloques.
7. Perfil del coche/cámara/color.

## G. Prohibiciones del proyecto

- no extraer APK;
- no decompilar;
- no modificar memoria;
- no redistribuir imágenes de la wiki;
- no incluir modelos 3D con proveniencia dudosa;
- no optimizar para evadir detección;
- no afirmar compatibilidad iOS de Unicode sin probar.
