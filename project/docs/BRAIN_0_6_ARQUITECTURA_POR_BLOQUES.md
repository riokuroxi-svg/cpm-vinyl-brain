# Brain 0.6 — Arquitectura por bloques con presupuesto 280

## Decisión crítica

Brain 0.5 mejora métricas, pero su corrección global puede convertir la imagen en mosaico y destruir estructura semántica. Las capturas del usuario muestran diseños coherentes con 279–280 capas, demostrando que la eficiencia de construcción es más importante que aproximar píxeles con 430 capas.

Brain 0.5 queda como experimento de Optimize & Reduce y herramienta de corrección, no como generador visual final.

## Nuevo principio

```text
No optimizar toda la imagen como una sola pintura.
Construir piezas completas, aprobarlas y ensamblarlas.
```

Cada bloque es un grupo editable con su propio lienzo local, presupuesto, objetivo y función de pérdida.

## Secuencia experta confirmada

La documentación japonesa de CPM indica el flujo usado en itashas:

```text
canvas de seguridad
→ líneas guía temporales
→ line art completo
→ relleno de colores
→ sombras y detalles
→ correcciones
```

La primitiva principal de line art será el carácter ASCII medio ancho `(`, estirado, aplanado y rotado. Círculos, gotas y rectángulos se reservarán principalmente para relleno. Las guías se eliminarán antes de exportar la receta.

## Bloques y presupuesto

| Bloque | Capas |
|---|---:|
| Underpainting/contorno general | 20 |
| Cabello posterior, frontal y sombras | 60 |
| Rostro, piel y cuello | 25 |
| Ojo izquierdo | 25 |
| Ojo derecho | 25 |
| Cejas, boca y nariz | 15 |
| Ropa, moño y delantal | 55 |
| Accesorios | 30 |
| Correcciones de ensamblaje | 25 |
| **Total** | **280** |

El límite 280 está fijado desde el planificador. Un bloque puede crear candidatos virtuales internamente, pero debe reducirse a su presupuesto antes de pasar al ensamblaje.

## Jerarquía de dibujo

```text
1. underpainting oscuro / line art
2. accesorios posteriores
3. cabello posterior
4. ropa posterior
5. cuello y rostro
6. ojos y rasgos
7. flequillo frontal
8. ropa/accesorios frontales
9. CUT y correcciones finales
```

## Archivos por bloque

```text
blocks/
├── 00_underpainting/
├── 10_hair/
├── 20_skin_face/
├── 30_eye_left/
├── 31_eye_right/
├── 40_face_details/
├── 50_clothes/
├── 60_accessories/
└── 90_assembly_corrections/
```

Cada bloque produce:

- `target.png`;
- `mask.png`;
- `preview.png`;
- `recipe.json`;
- `metrics.json`;
- `approved: true/false`.

No se ensambla un bloque que no pase su puerta de calidad.

## Puerta de percepción

Antes de optimizar:

- fondo separado;
- cabello identificado independientemente del color;
- rostro válido;
- dos ojos localizados;
- ropa y accesorios separados;
- orden frontal/posterior plausible.

Si falla, el pipeline devuelve `NEEDS_MASK_CORRECTION`. No genera una receta engañosa.

## Solucionadores especializados

### Cabello

Objetivo:

- silueta exterior;
- dirección de mechones;
- puntas;
- separación posterior/frontal;
- sombras principales.

Familias preferidas:

- gotas;
- triángulos;
- flechas;
- banderas;
- líneas/glifos diagonales.

### Ojos

No usar solver genérico. Plantilla anatómica parametrizada:

```text
blanco
iris
pupila
pestaña superior
pestaña lateral
reflejo
CUT color piel
```

Parámetros y relaciones:

- centro;
- ancho/alto;
- inclinación;
- posición de iris;
- contacto pestaña–iris;
- apertura;
- dirección de mirada.

### Rostro

- forma principal sólida;
- mandíbula;
- orejas;
- cuello;
- sombras;
- CUT para cabello y ojos.

### Ropa

- grandes masas primero;
- contorno oscuro debajo;
- relleno delante;
- pliegues y bordes al final.

### Accesorios

Se resuelven independientemente y pueden reutilizar plantillas.

## Solver interno de cada bloque

1. crear candidatos de figuras válidas;
2. ajustar X/Y/escala/rotación;
3. permitir ADD y CUT solo dentro del bloque y vecinos autorizados;
4. optimizar contorno y cobertura;
5. reducir al presupuesto asignado;
6. comprobar al tamaño final;
7. exportar grupo local.

## Ensamblador global

No modifica cada vinilo individual. Ajusta cada bloque como una unidad:

```text
blockX
blockY
blockScaleX
blockScaleY
blockRotation
blockZ
```

Esto mantiene ojos y cabello coherentes. Después solo utiliza las 25 capas reservadas para corregir juntas entre bloques.

## Funciones de pérdida por bloque

### Ojos

```text
35% landmarks y proporción
30% contorno
20% iris/pupila
10% color
5% capas
```

### Cabello

```text
35% silueta
25% puntas/mechones
20% cobertura
15% sombras
5% capas
```

### Ropa

```text
40% masas
25% contorno
20% pliegues
10% color
5% capas
```

No se utiliza una única función global para todos.

## Métricas obligatorias

- puntuación por bloque;
- calidad por capa;
- huecos conectados;
- overflow visible;
- landmarks de ojos;
- similitud de silueta;
- evaluación al tamaño final;
- aprobación humana.

SSIM global es secundaria.

## Calibración en el coche

El diseño 2D se monta en una caja de referencia sobre la puerta/lateral. El ensamblador global aplicará una transformación de cuatro puntos o malla para compensar perspectiva y curvatura. Después el Lector comparará una captura real y ajustará bloques, no cientos de capas individuales.

## Estado de versiones

- Brain 0.3: baseline estructural.
- Brain 0.5: mejor métrica, pero corrección global demasiado libre.
- Brain 0.6: arquitectura oficial por bloques y presupuesto 280.

## Primera implementación

1. agregar validador de percepción;
2. exportar bloques independientes;
3. crear template solver para ojos;
4. compilar cabello/rostro/ropa por separado;
5. ensamblar bloques;
6. permitir máximo 25 correcciones globales;
7. comparar contra 0.3 y 0.5 visualmente, no solo por SSIM.
