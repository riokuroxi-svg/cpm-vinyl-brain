# Reescritura diferenciable del Cerebro

## Evaluación crítica

“Quedar igual al original” no es una garantía realista con 280 capas y un catálogo limitado. El objetivo de ingeniería será máxima semejanza perceptual, contornos limpios y rasgos reconocibles. Las liveries profesionales mostradas también son reinterpretaciones simplificadas.

## Fallos actuales

- Parser dependiente de color.
- Objetivo semántico puede estar equivocado.
- Hill climbing/local search se atasca.
- Las capas no se reajustan todas simultáneamente.
- Corrección global destruye bloques.
- SSIM del objetivo simplificado puede ocultar fallos visibles.

## Nuevo núcleo

### Secuencia de construcción experta

```text
canvas de seguridad
→ guías temporales
→ line art completo con `(`
→ relleno con círculos/gotas/rectángulos
→ sombras y detalles
→ CUT/correcciones
```

La optimización diferenciable se aplicará por separado a line art y relleno. No se mezclarán ambas fases desde el inicio.

### Parser guiado

- segmentación automática;
- validación obligatoria;
- corrección humana por puntos cuando la confianza sea baja;
- no generar si faltan rostro/dos ojos/cabello.

### Renderizador diferenciable

Para cada bloque, cada capa tendrá parámetros continuos:

```text
x, y, scaleX, scaleY, angle, color, opacity
```

La figura se seleccionará con logits/Gumbel-Softmax sobre el catálogo. PyTorch `affine_grid` y `grid_sample` hacen diferenciable la transformación. Adam ajustará todas las capas del bloque a la vez.

### Pérdidas

- L1/CIELAB de color;
- Sobel/Chamfer de bordes;
- overflow de máscara;
- landmarks especializados en ojos;
- sparsity/importe por capa;
- penalización de solapamiento inútil.

### Discretización

Después de optimizar:

1. elegir figura argmax;
2. opacidad final 1;
3. eliminar capas de baja importancia;
4. ajuste local discreto;
5. exportar receta CPM.

## Orden de validación

1. ojo izquierdo Bocchi;
2. ojo derecho Bocchi;
3. ojos personaje azul;
4. cabello de ambos colores;
5. rostro;
6. ropa;
7. ensamblaje 280.

Una mejora debe funcionar en las dos imágenes.

## Ingeniería inversa permitida

Se empleará identificación de sistemas por caja negra:

- valores X/Y conocidos;
- capturas de salida;
- ajuste de función entrada→píxel;
- cuadrículas y colores;
- catálogo visible;
- comportamiento de grupos.

No se extraerán assets ni código del APK porque la EULA lo prohíbe.

## Estado

Se creó `research/diff_brain/renderer.py` y `optimize_block.py`. Requieren PyTorch/Colab y todavía deben validarse con el primer bloque de ojo.
