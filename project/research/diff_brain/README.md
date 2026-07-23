# Diff Brain — prototipo de renderizado diferenciable

Reescritura experimental del optimizador de bloques. Usa PyTorch `grid_sample` para optimizar simultáneamente posición, escala, rotación, color, opacidad y selección suave de figura.

## Por qué

El solver 0.3/0.5 depende de búsquedas aleatorias y decisiones discretas locales. Este prototipo permite que todas las piezas de un bloque se reajusten juntas mediante gradientes.

## Uso en Colab/GPU

```bash
pip install torch torchvision
python optimize_block.py \
  --shapes ../../src/main/resources/shapes \
  --target eye_left_target.png \
  --allowed-mask eye_left_allowed.png \
  --out result_eye_left \
  --layers 25 \
  --steps 1200
```

## Estado

- Esqueleto implementado.
- No probado localmente porque el entorno actual no contiene PyTorch.
- Primero se validará con un ojo y después con cabello/ropa.
- La salida `recipe_soft.json` debe discretizarse, forzar opacidad 1 y reducirse al presupuesto antes de entrar a CPM.

## Ingeniería inversa

Este módulo no accede al APK. Optimiza máscaras obtenidas mediante capturas autorizadas de la UI visible.
