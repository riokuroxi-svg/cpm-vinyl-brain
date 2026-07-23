# Resultado del Analizador 0.2A

**Estado:** primer hito funcional completado.

## Qué se implementó

- Prototipo Python reproducible en `research/analyzer_v02/`.
- Conservación de la relación de aspecto vertical.
- Composición correcta del PNG transparente sobre fondo oscuro.
- Separación inicial de fondo mediante alfa.
- Detección heurística de cabello, piel/rostro, blancos, ropa oscura, grises, acentos y detalles.
- Reconstrucción de una máscara sólida del rostro para retirar ojos y boca del Nivel 0.
- Cuantización de 20 colores en CIELAB.
- Cuatro objetivos progresivos: base, estructura, rasgos y cuantizado.
- Máscaras PNG transparentes individuales.
- Contrato `regions.json` con color, área, caja, confianza, máscara y Z sugerida.
- Prueba unitaria sobre una ilustración anime sintética.

## Primera salida

La Base automática ya elimina los ojos, boca y líneas principales, pero conserva:

- cofia;
- masa del cabello y flequillo;
- rostro y cuello;
- ropa oscura;
- delantal y puños;
- fondo.

Esto se acerca conceptualmente a la referencia simplificada enviada por el usuario. Las composiciones no coinciden exactamente porque la referencia tiene geometría y encuadre modificados, y se utiliza como guía de abstracción, no como verdad píxel a píxel.

## Regiones detectadas en la prueba

| Región | Área aproximada |
|---|---:|
| Fondo | 25.03% |
| Blancos estructurales | 20.68% |
| Cabello | 29.82% |
| Ropa oscura | 14.52% |
| Piel/rostro reconstruido | 12.32% |
| Acentos de color | 0.99% |
| Detalles no clasificados | 0.78% |

Las máscaras pueden solaparse intencionalmente para representar oclusión; por eso las áreas no forman una partición estricta.

## Limitaciones conocidas

- El backend actual utiliza color y conectividad; todavía no incorpora AnimeSeg.
- No separa automáticamente cabello posterior y flequillo frontal.
- Blancos como cofia, delantal y puños comparten una sola categoría.
- La máscara de rostro se reconstruye con una aproximación convexa.
- Los niveles 1/2 todavía se crean por tamaño de componente, no por un plan semántico completo.
- No se han ajustado vinilos; esta etapa solamente prepara objetivos y máscaras.

## Puerta siguiente: 0.2B

Antes del solucionador de vinilos:

1. dividir cabello posterior/frontal;
2. separar cara, cuello y brazos;
3. separar cofia, delantal y puños;
4. identificar ojos izquierdo/derecho, boca y accesorios;
5. permitir corregir una máscara con puntos positivos/negativos;
6. crear el grafo de profundidad final.

Después se podrá construir una receta base limpia de 20–40 capas opacas.
