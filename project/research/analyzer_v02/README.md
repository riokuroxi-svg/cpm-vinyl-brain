# Analizador semántico 0.2A

Primer prototipo del nuevo Cerebro estructural. Todavía no coloca vinilos.

## Función

- Respeta la relación de aspecto.
- Utiliza la transparencia del PNG para separar el fondo cuando está disponible.
- Detecta provisionalmente cabello, piel, blancos, ropa oscura, grises y acentos mediante color y conectividad.
- Cuantiza la paleta en CIELAB.
- Genera cuatro objetivos progresivos.
- Exporta máscaras transparentes y `regions.json`.

## Ejecución

```bash
python3 research/analyzer_v02/analyzer.py \
  --input imagen.png \
  --out examples/analisis \
  --max-side 768 \
  --colors 20
```

## Estado

Este backend de heurísticas sirve para validar el contrato de máscaras y la simplificación progresiva. No pretende sustituir el parser anime definitivo. La siguiente iteración conectará un backend semántico intercambiable y añadirá corrección manual de máscaras.
