# Rediseño del Cerebro 0.2 — De manchas de color a construcción por regiones

**Fecha:** 20 de julio de 2026  
**Motivo:** la demostración de 100/280 capas valida la infraestructura, pero visualmente se parece a una pintura al óleo y no a un diseño de vinilos bien construido.

## 1. Diagnóstico honesto de la versión 0.1

El optimizador 0.1 solamente pregunta: “¿esta nueva figura reduce el ΔE promedio de los píxeles?”. No sabe qué es un ojo, un mechón de cabello, una cara o un borde importante.

Esto provoca que:

- use figuras grandes y semitransparentes para promediar colores;
- coloque pinceles en zonas que deberían tener bordes sólidos;
- acepte formas que mejoran el promedio aunque destruyan detalles reconocibles;
- nunca corrija una capa antigua que quedó mal;
- no planifique el orden de oclusión;
- trate un píxel del fondo como igual de importante que el contorno de un ojo.

La versión 0.1 se conservará como prueba de infraestructura y, quizá, como refinador final. Deja de ser el algoritmo principal.

## 2. Cómo debe “pensar” el Cerebro

El Cerebro no necesita conciencia ni una IA generativa. Necesita una representación correcta del problema y una función de calidad que premie la estructura visual.

Cada capa tiene estos parámetros:

```text
figura, X, Y, escalaX, escalaY, rotación, color, opacidad, ordenZ
```

El nuevo Cerebro debe poder ejecutar estas operaciones sobre la receta completa:

- agregar una figura;
- moverla en X/Y;
- cambiar escala X/Y;
- rotarla;
- recolorearla;
- sustituirla por otra figura;
- moverla adelante o atrás en el orden de capas;
- eliminarla si estorba;
- dividir una región entre varias figuras.

Después de cada grupo de capas debe revisar y reajustar las ya colocadas, no limitarse a poner una mancha nueva encima.

## 3. Regla real de superposición

La imagen se construye de atrás hacia adelante. Una capa nueva se dibuja sobre las anteriores.

Para un punto con opacidad alfa:

```text
resultado = colorNuevo × alfa + colorAnterior × (1 − alfa)
```

- Si `alfa = 1`, la nueva figura tapa completamente la parte inferior.
- Si `alfa = 0.5`, mezcla ambos colores.
- La transparencia interna de los pinceles se conserva mediante su máscara.

Decisión para 0.2:

- Figuras sólidas: opacidad obligatoria de 100%.
- Brillos y pinceles: reservados para una etapa final y solamente donde la imagen objetivo realmente tenga degradado o textura.
- No usar transparencia como atajo para corregir masas de color.

## 4. Nueva tubería de procesamiento

### Etapa A — Preparar la imagen

1. Conservar su relación de aspecto; no forzar recorte cuadrado.
2. Separar fondo y zona útil.
3. Suavizar ruido sin borrar contornos.
4. Reducir la paleta en CIELAB a aproximadamente 12–24 colores.

Las ilustraciones anime son especialmente adecuadas porque tienen colores planos y bordes definidos.

### Etapa B — Segmentar por regiones

Transformar la imagen en componentes conectados coherentes:

- cabello rosa claro;
- sombras del cabello;
- piel;
- blanco de los ojos;
- iris y pupilas;
- pestañas;
- cofia blanca;
- uniforme negro;
- delantal blanco;
- moño;
- fondo.

La segmentación inicial será automática por color y continuidad. Después se podrá admitir una máscara opcional para marcar zonas prioritarias.

### Etapa C — Crear un mapa de importancia

No todos los píxeles valen lo mismo:

- ojos, boca y contorno de la cara: peso ×4;
- silueta y bordes fuertes: peso ×3;
- detalles del uniforme: peso ×2;
- zonas grandes de color: peso ×1;
- fondo uniforme: peso reducido.

Esto evita que el algoritmo sacrifique los ojos para mejorar una mancha grande de cabello.

### Etapa D — Construcción de atrás hacia adelante

Orden sugerido para el objetivo de prueba:

1. fondo;
2. cofia y cabello posterior;
3. cuello y cuerpo;
4. rostro;
5. blancos de los ojos;
6. iris, pupilas y reflejos;
7. pestañas y cejas;
8. mechones frontales sobre la cara y ojos;
9. uniforme, delantal y moño;
10. sombras y brillos pequeños.

Los mechones del flequillo deben ir después de los ojos porque en la imagen real los tapan parcialmente.

### Etapa E — Ajuste geométrico de cada región

Para cada componente, el Cerebro probará varias figuras y optimizará de forma deliberada:

```text
X, Y, escalaX, escalaY, ángulo
```

La calidad de encaje se medirá con:

- intersección sobre unión de la región (IoU);
- distancia entre contornos;
- error de color ΔE;
- penalización por invadir regiones ajenas;
- costo y cantidad de capas.

Una propuesta que tenga el color correcto pero destruya el borde de un ojo será rechazada.

### Etapa F — Refinamiento global

Cada cierto número de capas:

1. seleccionar una capa existente;
2. mover, escalar o rotar ligeramente;
3. probar otra figura;
4. modificar su orden;
5. eliminarla si mejora el resultado;
6. aceptar únicamente cambios que mejoren la puntuación estructural.

También se ejecutarán varias semillas y se conservará la mejor receta.

## 5. Nueva función de calidad

Propuesta inicial:

```text
calidad =
  35% similitud de color CIELAB
+ 30% similitud de contornos
+ 25% cobertura de regiones (IoU)
+ 10% simplicidad/costo
```

Estos porcentajes deberán medirse con el conjunto de evaluación. El mapa de importancia multiplica la contribución de ojos, boca y silueta.

## 6. Descomposición esperada de la imagen de prueba

En lugar de 280 manchas mezcladas, una receta lógica debería parecerse a:

- 8–15 figuras grandes para cabello posterior;
- 3–6 para rostro y cuello;
- 5–10 por ojo, contando blanco, iris, pupila, reflejos y pestañas;
- 8–15 para el flequillo;
- 10–20 para la cofia;
- 15–30 para uniforme, delantal y moño;
- el resto para sombras, curvas y correcciones de silueta.

La cantidad exacta surgirá del optimizador, pero cada grupo tendrá un propósito visible.

## 7. Cambios técnicos para 0.2

- Lienzo rectangular y preservación de proporción.
- Cuantización de paleta en CIELAB.
- Extracción de bordes.
- Segmentación en regiones conectadas.
- Máscaras de importancia.
- Figuras sólidas sin opacidad variable.
- Pases separados: base, estructura, detalles y textura.
- Ajuste local y global de capas.
- Reordenamiento y eliminación.
- Registro de qué región intenta representar cada capa.
- Comparación visual por etapas.

## 8. Criterio de aceptación revisado

La reducción de ΔE ya no basta. Una prueba se aprueba si:

1. el personaje se reconoce a primera vista;
2. ambos ojos están correctamente ubicados;
3. la silueta de cabello y rostro es estable;
4. las grandes áreas son opacas y limpias;
5. no parece una pintura de manchas translúcidas;
6. aumentar de 100 a 280 capas mejora detalles, no solo el promedio de color;
7. cada capa tiene una región o propósito identificable.

## 9. Decisión

No continuar con lector, Android ni ejecutor hasta que este rediseño supere la prueba visual. La infraestructura 0.1 se conserva; el algoritmo de generación se reemplaza por el enfoque estructural 0.2.
