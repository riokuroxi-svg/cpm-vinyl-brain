# Investigación y arquitectura elegida para el Cerebro 0.2

**Fecha:** 20 de julio de 2026

## Hallazgo principal

La idea del usuario —simplificar primero una ilustración, construir grandes masas y añadir detalles progresivamente— coincide con una línea de investigación llamada vectorización progresiva o semántica por capas.

No se encontró, entre los proyectos revisados, un sistema público que convierta directamente una imagen en una receta restringida al catálogo de vinilos de Car Parking Multiplayer. Esa adaptación sigue siendo la parte distintiva del proyecto.

## Proyectos relevantes

### 1. Layered Image Vectorization via Semantic Simplification

- Proyecto: https://github.com/SZUVIZ/layered_vectorization
- Artículo: https://arxiv.org/abs/2406.05404

Genera versiones progresivamente simplificadas de una imagen y reconstruye vectores en dos etapas: estructura general y refinamiento visual. Es la referencia más cercana a la idea propuesta por el usuario.

No se incorporará como dependencia móvil directa: usa PyTorch, CUDA, Stable Diffusion, SAM y DiffVG. Se estudiará su arquitectura coarse-to-fine.

### 2. LIVE — Layer-wise Image Vectorization

- Proyecto: https://github.com/Picsart-AI-Research/LIVE-Layerwise-Image-Vectorization
- Artículo: https://arxiv.org/abs/2206.04655

Añade caminos vectoriales cerrados de manera progresiva y optimiza todos los caminos existentes. La idea que debemos adoptar es que una capa anterior puede seguir ajustándose; no se limita a agregar capas nuevas.

### 3. See-through — Single-image Layer Decomposition for Anime Characters

- Proyecto: https://github.com/shitagaki-lab/see-through
- Artículo: https://arxiv.org/abs/2602.03749

Descompone ilustraciones anime en capas semánticas, completa regiones ocultas e infiere su orden. Maneja cabello, cara, ojos, ropa, accesorios y otras partes. Es una referencia directa para saber qué es cada región y qué va delante o detrás.

Es demasiado pesado para ser el motor final en Android: su propósito incluye generar las partes ocultas para animación 2.5D y utiliza modelos de difusión y profundidad. Para CPM no necesitamos reconstruir zonas invisibles; solo necesitamos máscaras visibles y orden de dibujo.

### 4. AnimeSeg

- Proyecto: https://github.com/suzukimain/AnimeSeg

Ofrece clases como fondo, piel, cara, cabello principal, ojo izquierdo/derecho, cejas, nariz, boca, ropa y accesorios. Puede servir como modelo maestro para probar segmentación o generar datos con los que entrenar/destilar un modelo móvil más pequeño.

### 5. Primitive y Geometrize

- Primitive: https://github.com/fogleman/primitive
- Geometrize: https://github.com/Tw1ddle/geometrize

Aproximan una imagen agregando primitivas que reducen el error. Producen deliberadamente resultados artísticos/abstractos. El Cerebro 0.1 pertenece a esta familia, lo que explica el aspecto de pintura.

### 6. VTracer

- Proyecto: https://github.com/jniox/vtracer_raster-to-svg

Convierte imágenes de color a contornos SVG compactos. Puede ayudar a obtener regiones y curvas de referencia, pero no resuelve la traducción a las 13 formas permitidas ni el orden semántico.

## Decisión: arquitectura híbrida

La mejor solución no es confiar completamente en un modelo pesado ni hacerlo todo manualmente. Se adopta un sistema híbrido de cuatro módulos.

```text
Imagen
  ↓
Parser semántico + segmentación por color
  ↓
Editor rápido de máscaras (corrección humana opcional)
  ↓
Planificador coarse-to-fine y grafo de profundidad
  ↓
Solucionador de vinilos restringido a las formas de CPM
  ↓
Receta JSON
```

## Módulo A — Parser semántico

Salida esperada por píxel:

- fondo;
- cabello;
- piel/rostro;
- ojos;
- boca/cejas;
- ropa;
- accesorios;
- desconocido.

Estrategia:

1. Prototipo de investigación con AnimeSeg u otro parser disponible.
2. Combinarlo con agrupación de colores CIELAB y componentes conectados.
3. Para Android, evaluar un modelo pequeño MobileNet/U-Net en TFLite/ONNX, posiblemente destilado desde un modelo grande.
4. Si la confianza es baja, pedir al usuario uno o dos toques o trazos para corregir la máscara.

El usuario no tendrá que dibujar cada capa; solo corregirá errores grandes de clasificación.

## Módulo B — Simplificación progresiva

Generar objetivos escalonados:

### Nivel 0 — Base

- fondo;
- silueta general del cabello;
- rostro/cuello;
- masa principal de ropa;
- cofia o accesorio grande.

Sin ojos, sombras, boca ni líneas.

### Nivel 1 — Estructura

- cabello frontal y posterior;
- delantal y moño;
- sombras principales;
- accesorios laterales.

### Nivel 2 — Rasgos

- blanco de ojos;
- iris y pupilas;
- boca y cejas;
- mechones principales.

### Nivel 3 — Detalles

- pestañas;
- reflejos;
- sombras pequeñas;
- líneas finas;
- pinceles o brillos, solamente si son necesarios.

La primera imagen enviada por el usuario representa aproximadamente el Nivel 0/1; la original corresponde al Nivel 3.

## Módulo C — Grafo de profundidad

Cada región tendrá relaciones de orden:

```text
cofia → detrás de cabello
cabello posterior → detrás de rostro
rostro → detrás de ojos
ojos → detrás de flequillo
cuerpo → detrás de moño/delantal
```

Cuando una misma clase aparece delante y detrás —por ejemplo, cabello posterior y flequillo— se divide en subcapas.

El orden automático se basará en:

- etiquetas semánticas;
- contención y contacto entre contornos;
- intersecciones tipo T;
- posición relativa;
- una regla de plantilla para personajes frontales;
- corrección humana opcional cuando exista ambigüedad.

## Módulo D — Solucionador de vinilos

Para cada máscara regional:

1. Elegir una forma candidata.
2. Ajustar X, Y, escala X/Y y rotación.
3. Maximizar cobertura dentro de la región.
4. Penalizar toda invasión fuera de la región.
5. Aplicar la figura con opacidad sólida.
6. Restar el área cubierta y repetir.
7. Refinar todas las figuras de la región.
8. Intentar reemplazar dos figuras por una si conserva calidad.

Puntuación regional propuesta:

```text
+ cobertura interna
- desbordamiento
- distancia de contorno
- error de color
- cantidad de capas
- costo
```

Después se ejecuta un refinamiento global que puede mover, rotar, sustituir, eliminar y reordenar cualquier capa.

## Por qué será mejor que 0.1

- Cada figura tendrá un propósito y una región asociada.
- Las capas sólidas producirán bordes de vinilo, no mezclas de pintura.
- Los ojos no competirán contra todo el cabello en una sola métrica.
- El orden será planeado antes de renderizar.
- La receta crecerá desde una versión simplificada hacia la original.
- Una mala capa podrá corregirse o eliminarse.

## Restricciones y expectativas

- Las 13 formas permiten comenzar, pero la fidelidad máxima puede requerir extraer más figuras útiles del catálogo real, especialmente curvas delgadas, óvalos y formas cóncavas.
- Ningún parser semántico es perfecto; el modo de corrección rápida es parte del diseño, no un fracaso.
- See-through y la vectorización semántica son referencias de investigación, no dependencias que deban ejecutarse completas en el teléfono.
- Antes de reutilizar código o modelos se revisarán sus licencias de software, pesos y datasets.

## Próximo prototipo

No generar todavía 280 capas. Primero demostrar:

1. máscaras de fondo, cabello, piel y ropa;
2. imagen simplificada automática comparable al ejemplo del usuario;
3. orden posterior/frontal correcto;
4. receta base de 20–40 capas sólidas con bordes limpios;
5. después añadir ojos y detalles como una segunda receta incremental.
