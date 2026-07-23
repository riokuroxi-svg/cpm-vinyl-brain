# Investigación: Car Parking Multiplayer original — julio de 2026

## Alcance

Objetivo exclusivo: **Car Parking Multiplayer original**, paquete Android:

```text
com.olzhas.carparking.multyplayer
```

CPM 2 no será objetivo del Ejecutor. El Cerebro visual puede compartir algoritmos, pero perfiles, coordenadas, catálogo y UI serán independientes.

## 1. Información oficial confirmada

Fuentes:

- Google Play: https://play.google.com/store/apps/details?id=com.olzhas.carparking.multyplayer
- App Store: https://apps.apple.com/us/app/car-parking-multiplayer/id1374868881
- EULA: https://olzhass.net/Car_Parking_Multiplayer_EULA.html

Datos:

- Desarrollador/publicador: olzhass / OGAMES.
- Más de 100 millones de descargas en Google Play.
- Editor visual descrito oficialmente como “Dynamic vinyls, car body parts”.
- Ajuste de suspensión, ángulo de ruedas, motor, turbo, caja y escape.
- Intercambio de coches y World Sale.
- Modo offline/single-player y multijugador.
- App Store declara 200+ coches; también indica 130+ con interior real.
- Android oficial actualizado el 16 de julio de 2026.
- Distribuidores firmados reportan versión 4.9.10, publicada alrededor del 17–20 de julio de 2026. La versión exacta debe verificarse en el dispositivo.

## 2. Restricciones legales relevantes

La EULA prohíbe:

- modificar el juego;
- ingeniería inversa, descompilación o acceso al código fuente;
- cheats/hacks y apps que modifiquen el contenido;
- versiones no oficiales no soportadas.

Decisión del proyecto:

- no extraer assets del APK;
- no modificar memoria/archivos;
- no usar GameGuardian ni mods;
- trabajar mediante UI visible, recetas, modo manual asistido y, solo tras revisar riesgo, Accesibilidad/IME;
- usar cuenta secundaria y garaje offline durante pruebas;
- respetar derechos de las imágenes objetivo.

## 3. Editor de vinilos: hechos observados en capturas del usuario

### Carrocería

- Contador visible: `n/450`.
- 450 es el límite operativo de la carrocería en la instalación actual del usuario.
- Lista vertical de capas con miniaturas e índices.
- Figuras geométricas, orgánicas, pinceles, brillos y texto.
- Color HEX visible.
- Rotación y escalas X/Y mostradas numéricamente.
- Duplicar, borrar, confirmar, información/favorito.
- Gestión de capas y selección múltiple.
- Texto con selector de fuente, Bold, Italic y contenido editable.

### Ventanas

Una reseña reciente en Google Play afirma que el “window vinyl” dispone de 100 capas y solicita ampliación. Debe confirmarse jugando. Hipótesis de perfil:

```json
{
  "bodyLayerLimit": 450,
  "windowLayerLimit": 100,
  "independentCounters": true
}
```

## 4. Funciones comunitarias confirmadas o muy probables

### Selección múltiple / grupo temporal

La comunidad describe:

1. abrir el panel de capas;
2. seleccionar múltiples vinilos;
3. mover/copiar el conjunto sin que se disperse.

Esto encaja con las capturas del usuario y es esencial para Brain 0.6: cada bloque podrá aplicarse y calibrarse como grupo.

### Copiar, pegar y espejo

Tutoriales muestran selección de varias capas, copia, traslado, escalado y duplicado invertido al otro lado. El espejo puede necesitar reajuste por diferencias de panel/cámara.

### Orden de capas

Fuentes comunitarias describen mover una capa arriba/abajo y voltearla. Debemos capturar exactamente los botones y comprobar si existe reordenamiento múltiple.

### Duplicación

El icono de páginas duplica una figura. Puede ahorrar navegación y conservar color/fuente.

## 5. Texto y “vinilos raros” mediante Unicode

Hallazgo público:

- Video: https://www.youtube.com/watch?v=TxJhNF6lEEo
- El creador comparte una app “Cool text and Symbols” y un archivo de símbolos.
- Los símbolos se copian y pegan en Car Parking Multiplayer y se usan como stickers/vinilos no presentes en el catálogo básico.

Otro tutorial muestra fuentes gruesas generadas con apps de texto estilizado; advierte que no todos los estilos funcionan en CPM.

Implicación:

```text
El catálogo real = vinilos visibles + glifos de fuentes + símbolos Unicode compatibles
```

Familias potenciales:

- líneas: `I | / \\ _ -`;
- curvas: `( ) C U J S`;
- anillos: `O 0 o ○ ●`;
- ángulos: `V W M < >`;
- estrellas/flechas/formas Unicode;
- secuencias repetidas si una cadena sigue contando como una capa.

Pruebas obligatorias:

- caracteres soportados;
- fuentes compatibles;
- Bold/Italic;
- anclaje y caja visual;
- longitud máxima;
- conteo de capas de una cadena;
- coste;
- comportamiento al estirar X/Y.

## 6. Catálogo de vinilos visibles

No se encontró una fuente pública completa, actual y fiable del catálogo 4.9.10.

Información parcial pública/comunitaria:

- círculos, rectángulos, triángulos, líneas;
- animales/dragones/caballos;
- gatos, panda, ninja y gráficos decorativos;
- estrellas, ondas, pinceles y formas de carreras;
- texto, banderas y plate vinyl.

Las capturas del usuario demuestran más formas que las 13 actuales. Necesitamos construir nuestro propio catálogo por observación legítima de la UI.

## 7. Catálogo que debe capturarse

Por cada vinilo:

```json
{
  "uiIndex": 0,
  "category": "shape",
  "name": "unknown_000",
  "price": 100,
  "thumbnail": "...",
  "mask": "...",
  "solid": true,
  "hasInternalAlpha": false,
  "concave": false,
  "tags": ["rectangle", "eraser", "fill"],
  "testedVersion": "4.9.10"
}
```

Captura mínima:

1. grabación desplazando todo el catálogo lentamente;
2. contador/índice y precio visibles;
3. aplicar candidatos útiles en blanco sobre superficie negra;
4. rotación 0 y escala idéntica;
5. captura perpendicular;
6. repetir para texto y símbolos.

## 8. Costes

Las capturas actuales muestran precios variados:

- 100, 300, 400… 1400 para formas básicas;
- 6000 para formas avanzadas observadas anteriormente;
- texto alrededor de 1000 en capturas.

Todos los costes deben almacenarse por versión y verificarse. El Brain debe optimizar capa, coste o ambos según el modo.

## 9. Flujo real de diseño aprendido de tutoriales

- base/silueta primero;
- detalles y sombras después;
- logos/texto al final;
- figuras pequeñas para ojos y rasgos;
- seguir líneas y curvatura del coche;
- utilizar formas del color base como borrador/máscara;
- copiar y espejar para consistencia;
- revisar fuera del garaje, en luz y distancia reales;
- usar referencias/guías rectas para alinear ambos lados.

Esto valida Brain 0.6 por bloques y operaciones ADD/CUT.

## 10. Diferencias con CPM 2

Fuentes oficiales confirman que CPM 2 es una app separada:

```text
com.olzhas.carparking.multyplayer2
```

CPM 2 enfatiza:

- gráficos/mapa/entornos más modernos;
- transmisión mecánica con embrague;
- combustible, Dyno Run, taxi, drag y livery mode explícito;
- aproximadamente 160 coches con interior.

Para el proyecto, aunque la idea de receta sea compartible:

- la UI no se presupone idéntica;
- el catálogo puede cambiar;
- límites, coordenadas y renderizado pueden diferir;
- perfiles de calibración no son intercambiables.

Decisión: objetivo único inicial = CPM original.

## 11. Dependencia del vehículo

Fuentes comunitarias advierten que diseños copiados pueden desalinearse o distorsionarse entre modelos. La receta debe incluir:

```json
{
  "game": "CPM1",
  "gameVersion": "4.9.10",
  "vehicleProfile": "nissan_350z_xxx",
  "panel": "body_left",
  "cameraProfile": "garage_left_fixed",
  "layerLimit": 450
}
```

No existe una coordenada universal para todos los coches.

## 12. Perfil geométrico del coche

Debe capturarse una cuadrícula de calibración:

- líneas horizontales y verticales;
- cuatro esquinas del área artística;
- costuras de puerta;
- ruedas/ventanas/luces/alerones como zonas prohibidas;
- cámara lateral fija.

El Brain generará primero en un rectángulo local y aplicará homografía/malla al panel real.

## 13. Color y material

- Usar condición fija de iluminación.
- Aplicar cartas de color conocidas.
- Medir HEX aplicado → Lab observado.
- Probar si vinilo y pintura de carrocería con el mismo HEX coinciden.
- Si no coinciden, crear un “canvas” con una gran capa de vinilo y usar ese mismo color para CUT.

## 14. Campos numéricos y estrategia de entrada

Pendiente de verificar:

- si ángulo, X, Y o escala abren teclado;
- negativos y decimales;
- precisión máxima;
- límites;
- incrementos de flechas;
- comportamiento al pegar;
- anclaje centro/baseline para texto.

Esto decide IME frente a gestos+OCR.

## 15. Riesgo y modo operativo

La EULA deja claro que no se debe modificar el juego. El producto debe priorizar:

1. generador de Receta;
2. vista previa;
3. manual asistido;
4. ejecución por UI visible solo después de revisar términos/riesgo;
5. sin técnicas anti-detección.

## 16. Lo que ya tenemos

- 13 máscaras limpias;
- formato de receta;
- renderizador;
- análisis semántico experimental;
- ADD/CUT;
- investigación Optimize & Reduce;
- arquitectura Brain 0.6 por bloques;
- evidencia de límite 450 en carrocería.

## 17. Lo que falta, priorizado

### Bloqueante

1. versión exacta instalada;
2. catálogo completo por grabación;
3. límite y contador de ventanas;
4. prueba de campos numéricos/IME;
5. test de texto/Unicode;
6. perfil de un vehículo y cámara fija;
7. cuadrícula/homografía del panel;
8. máscaras corregidas para cabello/ojos/ropa.

### Importante

9. costes;
10. orden y reordenamiento de capas;
11. selección múltiple y transformación de grupo;
12. copy/mirror y su efecto en el contador;
13. comportamiento 3D de puntas/figuras pequeñas;
14. tabla de color.

### Posterior

15. ventanas;
16. varios coches;
17. CPM 2;
18. compartir recetas.

## Conclusión

La mayor oportunidad descubierta no es otro algoritmo genérico: es ampliar el catálogo legítimamente mediante:

- todas las formas visibles;
- texto y fuentes;
- símbolos Unicode;
- secuencias repetidas;
- grupos/copias;
- perfiles específicos por coche.

Brain 0.6 debe compilar bloques contra este catálogo real, no contra solo 13 formas.
