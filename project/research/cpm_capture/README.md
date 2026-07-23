# CPM Capture Toolkit

Herramientas de caja negra para CPM original. Solo procesan capturas o videos de la UI visible.

## 1. Extraer catálogo desde video/capturas

```bash
python3 catalog_extractor.py catalog.mp4 \
  --out session_template/output/catalog \
  --layout layout_2400x1080.json
```

Revisar `CATALOG_CONTACT_SHEET.png` y renombrar/etiquetar manualmente candidatos.

## 2. Extraer máscara

```bash
python3 mask_extractor.py \
  --image screenshot.png \
  --roi 500,100,1000,800 \
  --mode white-on-dark \
  --out mask.png
```

Modos: `white-on-dark`, `dark-on-light`, `green-excess`.

## 3. Calibrar coordenadas

Editar `session_template/numeric_fields/coordinate_manifest.csv` y ejecutar:

```bash
python3 coordinate_calibrator.py \
  --manifest session_template/numeric_fields/coordinate_manifest.csv \
  --roi 100,100,1800,800 \
  --marker-color '#39FF14' \
  --out session_template/output/coordinates.json
```

## 4. Calibrar color

Editar los ROI del manifiesto:

```bash
python3 color_calibrator.py \
  --manifest session_template/colors/color_manifest.csv \
  --out session_template/output/colors.json
```

## Limitaciones

- El layout inicial está ajustado a capturas 2400×1080 observadas.
- El extractor de catálogo produce candidatos, no una lista final garantizada.
- OCR de precios/índices se añadirá cuando tengamos video real.
- La calibración requiere cámara y resolución fijas.
