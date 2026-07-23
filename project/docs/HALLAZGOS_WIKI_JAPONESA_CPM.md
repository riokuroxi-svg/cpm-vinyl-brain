# Hallazgos de la wiki japonesa de CPM

Fuentes:

- Guía del editor: https://gamerch.com/cpm/321964
- Base de datos de vinilos: https://gamerch.com/cpm/294126

## Flujo de una itasha de alta calidad

La guía describe que los diseños anime no son imágenes importadas: cada línea se construye mediante vinilos.

### Orden recomendado

1. colocar un rectángulo base como canvas y referencia de capas;
2. colocar líneas guía centrales y de proporción;
3. completar todo el line art;
4. rellenar colores después;
5. añadir sombras, detalles y correcciones;
6. borrar guías temporales;
7. verificar online/tamaño real.

Esto evita mezclar el orden Z de contorno y relleno.

## Herramienta principal de line art

La guía indica que muchos artistas utilizan el texto ASCII de medio ancho:

```text
(
```

Se aplana y alarga para producir una curva fina. Rotando, estirando y encadenando paréntesis se trazan:

- cabello;
- rostro;
- ojos;
- pestañas;
- ropa;
- contornos generales.

Los caracteres de ancho completo pueden fallar. El guion `-` y algunos números cambian más entre Android/iOS.

## Relleno

Vinilos más usados:

- círculo sólido;
- gota;
- rectángulo;
- otras formas según la región.

La eficiencia se consigue seleccionando forma/tamaño que cubra mucho sin invadir demasiado.

## Canvas de seguridad

La wiki advierte que bajar capas demasiado puede llevar su valor interno por debajo del cuerpo y hacerlas desaparecer online. Recomienda colocar primero un rectángulo base y trabajar siempre encima.

Implicación para la receta:

```json
{
  "layer0": "safety_canvas",
  "required": true,
  "deletable": false
}
```

## Capas y duplicación

- Nuevas capas y duplicados aparecen al frente.
- Las capas pueden moverse adelante/atrás.
- Texto duplicado y desplazado crea contornos/sombras.
- Formas del color del cuerpo/base se utilizan para recortar.

## Guías

Los artistas usan:

- línea central;
- líneas de ojos/nariz/boca;
- cuadrícula proporcional;
- caracteres como `ー`, `三` o `III` para guías equidistantes.

El Brain debe generar una vista de guía aunque esas capas no aparezcan en la receta final.

## Color

La wiki recomienda extraer HEX de la imagen, pero indica que el resultado visible no coincide exactamente por las características del juego. Se necesita microajuste/calibración visual.

## Unicode y compatibilidad

Símbolos dependientes del entorno pueden verse diferente entre:

- Android;
- iOS;
- dispositivos con/sin ciertos teclados.

Por tanto habrá dos perfiles:

### Portable

- formas oficiales;
- ASCII seguro;
- sin Unicode dependiente.

### Android local

- glifos/símbolos verificados en el dispositivo objetivo;
- no garantiza apariencia en iOS.

## Problemas de proyección

La guía documenta que vinilos en parachoques/espejos pueden aparecer sobresaliendo en paneles laterales. Deben mantenerse pequeños y dentro de límites.

Esto confirma la necesidad de máscaras por panel y penalización de spill 3D.

## Técnicas compuestas documentadas

- rectángulo redondeado con dos rectángulos cruzados;
- texto con sombra mediante duplicado desplazado;
- texto con borde usando cuatro copias alrededor;
- círculo recortado con una forma del color base;
- texturas metálicas combinando rectángulo y cuatro gradientes;
- marcos mediante capas grandes detrás y pequeñas delante;
- contorno oscuro primero y relleno de color encima.

## Catálogo conocido

La base de datos japonesa registra, entre otros:

- rectángulo, texto, paralelogramo, pentágono, rombo;
- ondas, gota, sol, anillos, flechas, zigzag, estrella;
- gradientes, patrones, telaraña, tribales, llamas, checker;
- cuadrado sólido/contorno, círculo sólido/contorno;
- hexágono sólido/contorno;
- triángulo sólido/contorno;
- flecha sólida/contorno;
- espiral, curvas, U, corazón;
- pinceladas, arcos y gradientes;
- numerosos stamps/animales.

Además lista aproximadamente 19 fuentes y varios glifos ocultos dependientes de combinación carácter+fuente.

## Cambio necesario al Brain

Brain 0.6 debe tener dos subsolvers:

### LineArtSolver

- target: mapa de bordes;
- primitiva principal: `(`;
- optimiza cadenas de curvas;
- presupuesto propio;
- completa todo el line art antes del relleno.

### FillSolver

- target: regiones de color;
- círculos/gotas/rectángulos;
- trabaja debajo/dentro del contorno;
- usa CUT de color base.

Luego sombras/detalles y ensamblaje.

## Conclusión

La forma de pensar de los expertos no es “aproximar una imagen completa con manchas”. Es:

```text
canvas → guías → line art → relleno → sombras → corrección
```

Esta secuencia debe reemplazar al pipeline global anterior.
