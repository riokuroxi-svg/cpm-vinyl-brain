# Fase 0 — Captura del editor CPM original

## Preparación

- Usar versión oficial de Google Play/App Store.
- Anotar versión exacta desde Ajustes → Apps.
- Cuenta secundaria.
- Garaje/offline.
- Elegir un coche de prueba con lateral amplio y relativamente plano.
- No cambiar resolución, DPI ni orientación durante la captura.

## Sesión A — Catálogo visible

Grabar pantalla mientras se desplaza lentamente por todo el catálogo.

Debe verse:

- miniatura;
- índice/orden;
- precio;
- categoría;
- contador de capas;
- versión del juego anotada aparte.

Repetir si existen categorías/filtros.

## Sesión B — Máscaras útiles

Aplicar en blanco sobre una zona negra:

- líneas/arcos;
- curvas;
- cóncavas;
- gotas/mechones;
- círculos/anillos;
- rectángulos/triángulos;
- estrellas;
- pinceles;
- brillos;
- formas con transparencia interna.

Condiciones:

- rotación 0;
- X/Y iguales;
- escala anotada;
- cámara perpendicular;
- UI sin cubrir la forma.

## Sesión C — Texto y Unicode

Fuentes iniciales:

- Norwester;
- Mantega;
- Eufemia;
- otras dos geométricamente distintas.

Cadena ASCII:

```text
I|/-\()[]{}<>_-=+CVOSJUMW018
```

Repeticiones:

```text
||| /// \\\ ((( ))) VVV OOO
```

Unicode opcional:

```text
• ● ○ ◯ ▲ ▼ ◢ ◣ ★ ☆ ◆ ◇ ◀ ▶
```

Por fuente:

- normal;
- Bold;
- Italic;
- contador antes/después;
- máximo de caracteres;
- coste.

## Sesión D — Campos numéricos

Para forma y texto:

- tocar ángulo;
- tocar X;
- tocar Y;
- intentar teclado;
- probar `-10`, `0`, `5.5`, `189.15`, `999`;
- anotar límites y redondeo;
- probar pegado.

## Sesión E — Capas

- límite de carrocería;
- límite de ventanas;
- independencia de contadores;
- duplicar;
- selección múltiple;
- mover grupo;
- escalar grupo;
- rotar grupo;
- copiar;
- espejo;
- reordenar arriba/abajo;
- efecto en contador;
- deshacer/rehacer, si existe.

## Sesión F — Cuadrícula del coche

Crear temporalmente:

- 5 líneas verticales;
- 5 horizontales;
- cuatro marcadores de esquina;
- un círculo de referencia.

Capturas:

- lateral izquierdo fijo;
- lateral derecho fijo;
- cerca/lejos;
- cámara restablecida.

Anotar costuras y zonas prohibidas.

## Sesión G — Color

Aplicar 12 muestras:

```text
#000000 #FFFFFF #FF0000 #00FF00 #0000FF #FFFF00
#00FFFF #FF00FF #808080 #F2E9DF #EEA4B7 #202300
```

Usar iluminación fija y guardar captura limpia.

## Entregables

```text
capture_session/
├── device_profile.json
├── game_profile.json
├── catalog_video.mp4
├── shapes/
├── text_fonts/
├── unicode/
├── numeric_fields/
├── layers/
├── vehicle_grid/
└── colors/
```

## Puerta de salida

No continuar con el Ejecutor hasta tener:

- catálogo inicial ≥ 40 primitivas útiles o confirmación de que hay menos;
- respuesta sobre IME;
- perfiles de capa body/window;
- un vehículo calibrado;
- al menos tres fuentes y símbolos probados.
