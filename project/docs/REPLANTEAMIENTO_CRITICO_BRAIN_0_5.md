# Replanteamiento crítico — CPM Vinyl Brain 0.5

## Diagnóstico

El límite final no es el cuello de botella actual:

- el editor mostrado permite 450 capas;
- la receta 0.3 utilizó 127;
- varias regiones dejaron presupuesto sin usar;
- el solucionador se detuvo porque ninguna propuesta local superaba su penalización de overflow.

Por tanto, aumentar el límite sin cambiar el algoritmo no resuelve la calidad. Hay que eliminar el presupuesto durante la búsqueda, optimizar un conjunto sobrecompleto y solo después compilarlo al presupuesto real.

## Lo aprendido de diseñadores humanos

### 1. Referencia, cuadrícula y overlay

Los artistas no colocan formas a ciegas. Conservan proporciones con una cuadrícula o trazan sobre una referencia superpuesta.

Traducción al Brain: todas las regiones deben trabajar en coordenadas compartidas y verificarse contra una superposición del objetivo, no solo contra métricas agregadas.

### 2. Eficiencia de lados

Una forma es buena si varios de sus bordes coinciden simultáneamente con el objetivo. No basta medir cuántos píxeles cubre.

Traducción: añadir una puntuación por segmentos de borde coincidentes y esquinas útiles.

### 3. Máscara/borrador

Los creadores colocan una forma grande y después la recortan con otra del color del fondo, piel o región frontal.

Traducción: permitir operaciones positivas y negativas:

```text
ADD  color cabello
CUT  color rostro
CUT  color fondo
```

No es transparencia ni sustracción real; son capas opacas ordinarias colocadas en el orden correcto.

### 4. Línea detrás, relleno delante

Cuando faltan formas finas, se crea primero una silueta/contorno oscuro ligeramente mayor y luego se coloca el color encima. La parte oscura visible se convierte en line art.

Traducción: cada bloque puede tener `outlineMask = dilate(mask) - mask`, construido antes del relleno.

### 5. Verificación al tamaño real

Una curva que se ve perfecta grande puede perder punta o engordar al aplicarse pequeña sobre el coche.

Traducción: evaluar siempre en tres escalas y, finalmente, con una tabla de rasterización/calibración del juego.

## Repositorios y métodos útiles

### Optimize & Reduce — adaptación principal

- https://github.com/ajevnisek/optimize-and-reduce
- Licencia MIT.

Principio:

1. empezar con muchas formas;
2. optimizarlas juntas;
3. medir la importancia de cada una;
4. eliminar las menos útiles;
5. volver a optimizar;
6. repetir hasta alcanzar el presupuesto.

No se copiará su representación Bézier/DiffVG. Se adaptarán el scheduler, la importancia y la reducción a las máscaras fijas de CPM.

### Segmentation-Based Parametric Painting

- https://github.com/manuelladron/semantic_based_painting
- Licencia MIT.

Principios a reutilizar:

- bloques semánticos;
- coarse-to-fine;
- mapa dinámico de atención;
- optimización por parches/regiones;
- volver repetidamente a las zonas con mayor error.

No se usarán sus pinceles como salida final.

### CMA-ES / pycma

- https://github.com/CMA-ES/pycma
- Licencia BSD-3-Clause.

Uso propuesto: optimizar parámetros continuos de pequeños grupos de capas:

```text
X, Y, escalaX, escalaY, rotación
```

La selección discreta de figura seguirá a cargo de búsqueda de haz/mutaciones.

### Primitive / ImagesPrimitives

- https://github.com/fogleman/primitive
- https://github.com/mtrebi/ImagesPrimitives

Aportan mutación, multi-start e hill climbing, pero su esquema de añadir una forma y congelarla produce resultados artísticos/abstractos. Se conservarán únicamente sus ideas de generación de candidatos, no su arquitectura central.

### Layered Image Vectorization via Semantic Simplification

- https://github.com/SZUVIZ/layered_vectorization

Aporta objetivos progresivos, bloques semánticos y optimización conjunta de primitivas anteriores y nuevas.

### Packing 2D

Los algoritmos de bin packing no son el núcleo correcto: intentan evitar solapamientos y ocupar un contenedor, mientras una livery necesita superposición, máscaras y orden Z. Solo pueden aportar geometría de colisión/overflow.

## Nueva arquitectura: Optimizar sin límite, compilar con límite

```text
Imagen
  ↓
Bloques semánticos
  ↓
Blueprint: contorno + relleno + detalles
  ↓
Pool sobrecompleto de 600–1000 capas virtuales
  ↓
Optimización conjunta por bloques
  ↓
Máscaras/borradores y corrección residual
  ↓
Optimize & Reduce
  ↓
Recetas 64 / 128 / 256 / 430 capas
  ↓
Calibración sobre coche real
```

Las “capas virtuales” solo existen durante el cálculo. La receta final reserva aproximadamente 20 capas del límite 450 para correcciones específicas del coche.

## Puzzle solver por bloques

Cada bloque se trata como un rompecabezas con piezas que pueden solaparse.

### Bloques

1. fondo/contorno general;
2. cofia y cabello posterior;
3. ropa base;
4. rostro y piel;
5. ojos y boca;
6. flequillo y mechones frontales;
7. sombras/accesorios;
8. corrección global.

### Candidato

```text
figura o glifo
X / Y
escalaX / escalaY
rotación
color
operación ADD o CUT
orden Z
bloque semántico
```

### Función de pérdida

```text
L =
  30% huecos visibles
+ 20% overflow visible
+ 20% distancia de contorno
+ 10% color ΔE
+ 10% rasgos prioritarios
+  5% redundancia
+  5% costo/capas
```

Los pesos cambian por etapa: al principio importan las masas; al final los bordes y rasgos.

## Optimización alternada

1. **Asignación discreta:** cambiar figura, glifo, operación o Z.
2. **Ajuste continuo:** CMA-ES/coordenadas para X/Y/escala/ángulo.
3. **Reordenamiento:** swaps locales de profundidad.
4. **Atención:** escoger el bloque con mayor error residual.
5. **Máscara:** añadir CUT cuando una forma grande es eficiente pero sobresale.
6. **Reducción:** eliminar capas redundantes y reoptimizar.

## Importancia de una capa

```text
importance(layer) =
  pérdida_sin_capa - pérdida_con_capa
+ cobertura_única
+ bono_semántico
- redundancia
```

Se elimina por lotes pequeños, no todas de golpe. Después de cada eliminación se recalibran las capas vecinas.

## Recetas progresivas

Una sola ejecución producirá:

- `recipe_064.json`: silueta y colores base;
- `recipe_128.json`: estructura completa;
- `recipe_256.json`: rostro y detalles principales;
- `recipe_430.json`: máxima fidelidad y correcciones.

Esto permite comprobar cuándo deja de mejorar perceptiblemente y escoger el mejor equilibrio.

## Texto como primitivas

Los glifos `| / \\ ( ) C O V W` se integrarán como familias geométricas tras capturar las fuentes reales. Serán especialmente útiles en el pase de huecos y line art.

## Calibración con el coche

La optimización 2D no es suficiente. La receta debe evaluarse después en:

- vista lateral fija;
- tamaño final;
- carrocería y curvatura reales;
- luz fija del garaje;
- captura real del resultado.

El Lector devolverá un mapa de error para una última calibración de X/Y/escala/color.

## Decisión

El solver 0.3 queda como baseline. No se seguirá parcheando. El núcleo 0.5 será una reescritura basada en:

- pool sobrecompleto;
- ADD/CUT;
- bloques semánticos;
- optimización alternada;
- atención residual;
- Optimize & Reduce;
- salidas progresivas 64–430.

La fase de percepción 0.2A/0.2B se conserva. El cambio principal está en el compilador de vinilos.
