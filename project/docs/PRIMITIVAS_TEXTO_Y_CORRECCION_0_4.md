# Brain 0.4 — Primitivas de texto y pase de corrección

## Hallazgo

El editor de CPM permite una capa de texto con selección de fuente, negrita, cursiva, color y transformaciones. Un glifo puede tratarse como máscara geométrica, no necesariamente como lenguaje.

Ejemplos:

| Familia | Glifos candidatos | Uso geométrico |
|---|---|---|
| Líneas | `I | / \\ _ -` | pestañas, cejas, mechones, costuras |
| Curvas | `( ) C U J S` | boca, mandíbula, cofia, arcos |
| Anillos | `O 0 o` | ojos, iris, huecos |
| Ángulos | `V W M < > A` | puntas de cabello, pliegues |
| Repeticiones | `///`, `)))`, `||||`, `VVV` | patrones compuestos con una sola capa, pendiente de verificar |

## Verificaciones obligatorias en el juego

1. Confirmar si una cadena completa consume una sola capa.
2. Confirmar símbolos aceptados.
3. Confirmar longitud máxima.
4. Confirmar repetición de caracteres.
5. Confirmar si espacios iniciales/finales se conservan.
6. Confirmar escalado X/Y y rotación.
7. Confirmar si Bold/Italic alteran el glifo como se espera.
8. Registrar precio de una capa de texto.
9. Confirmar si todos los vehículos/editor usan las mismas fuentes.
10. Capturar el anclaje real respecto al punto X/Y.

## Catálogo propuesto

No se incorporarán todas las letras de todas las fuentes. Se comenzará con:

- 3 fuentes: geométrica, curva/script y delgada;
- 12–18 glifos por fuente;
- variantes normal, bold e italic solamente cuando cambien de forma de manera útil;
- plantillas repetidas de 2–5 símbolos si siguen contando como una capa.

Cada entrada tendrá:

```json
{
  "id": "text_mantega_paren_left_italic",
  "type": "text",
  "text": "(",
  "font": "Mantega",
  "bold": false,
  "italic": true,
  "family": "curve_left",
  "visualBounds": [0.12, 0.04, 0.84, 0.96],
  "baseline": 0.82,
  "cost": 1000
}
```

El costo es provisional hasta verificarlo.

## Solucionador creativo por familias

El Cerebro no probará todos los glifos en todas las regiones. Primero clasificará la geometría del hueco residual:

- componente alargado + ángulo vertical → `I` o `|`;
- componente alargado diagonal → `/` o `\\`;
- curva abierta hacia la derecha → `(` o `C`;
- curva abierta hacia la izquierda → `)`;
- componente anular → `O` o `0`;
- puntas repetidas → `V`, `W` o `M`;
- región compacta → figuras geométricas existentes.

Se usarán PCA, relación de aspecto, esqueleto, número de huecos y curvatura del contorno para elegir una familia antes de optimizar X/Y/escala/rotación.

## Por qué quedan espacios actualmente

- penalización fuerte al sobresalir;
- formas limitadas para huecos delgados o cóncavos;
- el solucionador puede detener una región antes de gastar todo su presupuesto;
- las oclusiones posteriores pueden descubrir pequeñas zonas no previstas;
- optimizar cobertura promedio no garantiza eliminar cada componente residual.

## Pase final de corrección

Después de renderizar la receta completa:

1. comparar objetivo semántico y resultado;
2. crear mapa de huecos por región/color;
3. extraer componentes conectados residuales;
4. ordenar por área e importancia;
5. clasificar su geometría;
6. escoger figura o glifo;
7. optimizar transformación;
8. añadir capa de relleno del color objetivo;
9. si sobresale, añadir una capa correctora del color frontal/vecino;
10. repetir hasta llegar al límite o al umbral de calidad.

Criterios iniciales:

- cobertura visible por región ≥ 95% cuando la geometría lo permita;
- ningún hueco conectado mayor al 0.10% del lienzo;
- opacidad 100%;
- máximo 280 capas en el perfil de carrocería;
- glifos y figuras registrados explícitamente en la receta.

## Receta ampliada

```json
{
  "type": "text",
  "phase": "gap_correction",
  "regionId": "brow_left_image",
  "text": "(",
  "font": "Mantega",
  "bold": false,
  "italic": true,
  "x": 0.36,
  "y": 0.29,
  "width": 0.09,
  "height": 0.025,
  "rotationDeg": 12.0,
  "color": "#20242F",
  "opacity": 1.0,
  "z": 54
}
```

## Compatibilidad descubierta

La wiki japonesa de CPM advierte que símbolos dependientes del entorno, fuentes estilizadas, guiones y algunos números pueden cambiar entre Android e iOS. El carácter ASCII de medio ancho `(` es usado habitualmente para line art y presenta menos diferencias que símbolos complejos.

El catálogo de texto tendrá perfiles:

- `portable`: formas oficiales + ASCII verificado;
- `android-local`: símbolos comprobados en el dispositivo, sin garantía para iOS.

No se utilizará Unicode raro por defecto en diseños destinados a World Sale o multiplataforma.

## Decisión

La versión 0.3 queda como línea base histórica. El siguiente Brain incorporará line art con paréntesis ASCII, catálogo visible real y un pase de corrección. No se simularán fuentes genéricas: primero se capturarán las formas reales del juego para que la Receta coincida con el Ejecutor.
