# Resultado del Analizador 0.2B

**Estado:** subdivisión semántica y grafo de profundidad implementados.

## Salida de la prueba

- 30 subpartes visibles.
- 30 relaciones `detrás → delante`.
- Ninguna relación contradice el orden Z propuesto.
- 30 máscaras PNG transparentes.
- `layer_graph.json` con nodos, colores, áreas, cajas, grupos, padres y Z.
- Plantilla opcional de correcciones por puntos.
- Dos pruebas automatizadas aprobadas.

## Partes principales detectadas

### Cabello

- `hair_back`: cabello posterior.
- `hair_front`: flequillo que debe cubrir parte del rostro/ojos.
- `hair_side`: mechones laterales que pueden cubrir las mangas.
- `accessory_pink_ribbon`: cinta rosa separada.

### Piel

- `face`: rostro base sólido.
- `neck`: cuello.
- `arm_right_image`: piel visible del brazo derecho de la imagen.

### Ropa y blancos

- `headpiece`: cofia.
- `apron`: delantal/blanco central.
- `shoulder_frills`: volantes de hombro.
- `cuff_left_image` y `cuff_right_image`: puños.
- `sleeve_left_image` y `sleeve_right_image`: mangas oscuras.
- `bow_dark`: moño/ropa central oscura.

### Rostro

- Blanco de cada ojo.
- Zona oscura/pestaña de cada ojo.
- Iris celeste de cada ojo.
- Reflejos.
- Cejas.
- Boca.
- Detalle de nariz.

### Accesorios

- Accesorio azul.
- Accesorio amarillo.
- Cinta rosa.

## Regla de izquierda/derecha

Los nombres `left_image` y `right_image` se refieren a la posición en la imagen, no al lado anatómico del personaje. Esto elimina ambigüedad al ejecutar coordenadas X.

## Grafo de profundidad

Ejemplos ya codificados:

```text
fondo → cofia → cabello posterior
cabello posterior → rostro
rostro → blanco de ojos → iris oscuro → iris celeste → reflejos
rostro/ojos → flequillo frontal
mangas → delantal → moño
mangas → mechones laterales
```

Las aristas están guardadas como `edgesBehindToFront`.

## Correcciones

`corrections_template.json` permite añadir o quitar áreas de una máscara con puntos normalizados y radio. Es una interfaz de datos inicial para el futuro editor visual; todavía no es una UI táctil.

## Limitaciones

- El parser sigue siendo heurístico por color; la clasificación neuronal se conectará como backend alternativo.
- La división de flequillo usa la intersección entre cabello y rostro reconstruido.
- Algunas piezas blancas conectadas requieren heurísticas espaciales.
- Los rasgos finos necesitan revisión antes de traducirlos a vinilos.
- No se reconstruyen zonas ocultas porque CPM solo necesita la composición visible.

## Puerta siguiente: Solucionador 0.2C

El próximo módulo no intentará copiar toda la imagen. Ajustará las 13 figuras únicamente al **Nivel 0** y por regiones:

1. fondo;
2. cofia;
3. cabello posterior;
4. mangas/ropa;
5. delantal;
6. rostro y cuello;
7. flequillo y mechones laterales.

Usará capas sólidas, cobertura/overflow de máscara, distancia de contorno y refinamiento X/Y/escala/rotación. La meta es una base limpia de 20–40 capas antes de agregar ojos.
