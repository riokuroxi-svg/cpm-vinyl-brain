# Plan de adquisición de datos sin extraer el APK

## Principio

El proyecto no extraerá ni redistribuirá assets, meshes, texturas, atlases, código o metadatos internos de Car Parking Multiplayer sin autorización escrita del titular.

Se utilizarán:

- UI pública;
- capturas del propio usuario;
- experimentos reproducibles dentro del editor;
- documentación pública;
- contenido generado por el usuario;
- permisos o datos entregados directamente por olzhass.

## Datos deseados y alternativa legal

| Dato deseado | Por qué sirve | Método sin APK | Salida |
|---|---|---|---|
| Máscaras de vinilos | Catálogo limpio | blanco sobre fondo negro, captura perpendicular | PNG alfa |
| Índice/precio/categoría | Ejecutor y presupuesto | video completo del catálogo + OCR | `catalog.json` |
| Fuentes y glifos | Primitivas adicionales | hojas de prueba renderizadas en el juego | atlas de glifos propio |
| Unicode compatible | Vinilos raros | pegar lista de símbolos y capturar | `unicode_catalog.json` |
| X/Y/escala/ángulo | Transformaciones exactas | barrido controlado de valores + capturas | modelo de calibración |
| Anclaje de texto | Colocación | cadena con marcadores y escalas conocidas | bbox/baseline |
| Orden de capas | Receta | experimentos de superposición de dos colores | reglas Z |
| Límites body/window | Presupuesto | contador antes/después | perfil del juego |
| Copy/mirror/grupo | Compilación por bloques | experimento con 3–10 capas | reglas de grupo |
| Panel del coche | Warping | cuadrícula aplicada al lateral | homografía/malla |
| Zonas prohibidas | Evitar ruedas/ventanas | segmentación de captura lateral | máscara por vehículo |
| Color aplicado/observado | Fidelidad | carta de 12–32 colores | LUT HEX→Lab |
| Comportamiento a escala | Puntas/líneas | misma figura en varios tamaños | modelo de rasterizado |
| Material body vs vinyl | CUT invisible | mismo HEX en pintura y vinilo | error ΔE |

## Identificación del sistema X/Y/ángulo

### Barrido mínimo

Para una figura rectangular:

```text
X: -20, -10, 0, 10, 20
Y: -20, -10, 0, 10, 20
Ángulo: 0, 30, 45, 90, 180
Escala X/Y: varios valores conocidos
```

Capturar cada estado con cámara fija. Detectar automáticamente el centro y las esquinas de la figura. Ajustar:

- transformación afín;
- posibles no linealidades;
- límites y redondeo;
- relación valor→píxel;
- sentido del ángulo;
- anclaje.

No necesitamos conocer el código interno si la función entrada→resultado puede medirse.

## Perfil geométrico de un coche

1. Seleccionar un coche de desarrollo.
2. Fijar cámara lateral.
3. Aplicar cuadrícula 5×5.
4. Detectar puntos en captura.
5. Ajustar homografía inicial.
6. Añadir corrección de malla para curvatura.
7. Crear máscara de ventanas, ruedas, luces y costuras.
8. Guardar por versión/resolución.

```json
{
  "vehicle": "nissan_350z",
  "panel": "body_left",
  "homography": [[0,0,0],[0,0,0],[0,0,1]],
  "meshCorrection": "mesh.json",
  "forbiddenMask": "mask.png"
}
```

## Atlas de vinilos propio

No es una copia de archivos internos. Es un dataset de mediciones visuales creadas por el usuario dentro del editor.

Por figura:

- captura original;
- fondo estimado;
- máscara alfa derivada;
- bbox;
- centro visual;
- tags geométricos;
- precio e índice;
- versión del juego;
- calidad/confianza.

## Modelos 3D

No son necesarios para el MVP. Un perfil screen-space por coche es más pequeño, legalmente más limpio y suficiente para aplicar una livery lateral.

Si en el futuro olzhass concede autorización o proporciona UV/meshes oficiales, se podría añadir un renderer 3D. Sin permiso no se redistribuirán modelos del juego.

## Solicitud al desarrollador

Datos que podemos pedir sin solicitar código fuente:

- lista/atlas oficial de decals;
- nombres e índices;
- límites por sección;
- convención de X/Y/escala/ángulo;
- fuentes y glifos permitidos;
- documentación del formato de diseños;
- permiso para una herramienta manual asistida;
- posible SDK/exportación de recetas.

## Ventajas de la caja negra

- funciona incluso si cambia Unity o el empaquetado;
- no depende de assets propietarios;
- se puede publicar;
- detecta el comportamiento real, incluyendo shaders y deformación 3D;
- permite perfiles por versión;
- reduce riesgo legal y de cuenta.

## Desventajas

- requiere capturas sistemáticas;
- es más lento al principio;
- algunos parámetros deben inferirse;
- hay que repetir calibración tras actualizaciones.

## Decisión

La ruta oficial del proyecto será:

```text
Capturar → medir → modelar → validar
```

Solo se utilizarán datos internos si olzhass entrega autorización escrita y condiciones claras de uso/distribución.
