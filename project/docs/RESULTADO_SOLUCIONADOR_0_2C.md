# Resultado del Solucionador 0.2C

**Estado:** primera receta estructural por regiones completada.

## Restricciones cumplidas

- 40 capas generadas de 40 solicitadas.
- Solo las 9 figuras sólidas del catálogo.
- Opacidad 100% en todas las capas.
- Cada capa tiene `regionId` y propósito explícito.
- Orden Z heredado del grafo 0.2B.
- Sin ojos, pestañas, pinceles ni brillos.
- Receta JSON reproducible con semilla `20260720`.

## Resultado cuantitativo

Cobertura regional media: **81.4%**.

| Región | Capas | Cobertura |
|---|---:|---:|
| Cofia | 3 | 89.3% |
| Cabello posterior | 3 | 89.1% |
| Manga izquierda | 1 | 100.0% |
| Manga derecha | 1 | 99.9% |
| Delantal | 3 | 90.5% |
| Volantes de hombro | 1 | 50.8% |
| Puño izquierdo | 1 | 60.1% |
| Puño derecho | 1 | 64.4% |
| Piel/brazo visible | 1 | 73.6% |
| Cuello | 1 | 82.6% |
| Rostro | 3 | 97.0% |
| Moño oscuro | 2 | 73.6% |
| Flequillo frontal | 6 | 81.9% |
| Mechones laterales | 13 | 86.5% |

## Figuras elegidas

- 10 rectángulos.
- 9 pentágonos.
- 7 gotas.
- 6 círculos.
- 3 triángulos.
- 2 flechas.
- 2 banderas onduladas.
- 1 arco grueso.

El arco delgado no fue seleccionado en esta ejecución.

## Diferencia respecto a 0.1

El resultado ya no utiliza transparencias para promediar colores. Las superficies son planas, los bordes son de vinilo y cada figura intenta cubrir una máscara específica. La apariencia deja de ser pintura al óleo, aunque la silueta todavía es geométricamente aproximada.

## Funcionamiento del ajuste

Para cada región:

1. calcula el área residual sin cubrir;
2. localiza su componente principal y orientación;
3. genera candidatos con figura, X, Y, escala X/Y y rotación;
4. premia cobertura nueva y bordes importantes;
5. penaliza desbordamiento visible;
6. permite invadir zonas que una capa posterior cubrirá;
7. refina localmente el mejor candidato;
8. registra la capa en la receta.

## Limitaciones detectadas

- La cofia y los volantes necesitan más formas curvas o capas de corrección.
- Los mechones laterales consumen gran parte del presupuesto.
- Algunas figuras rectangulares dejan cortes demasiado evidentes en el cabello.
- La cobertura media no mide por sí sola la suavidad de la silueta.
- Todavía no existe refinamiento global de todas las capas juntas.
- La asignación de presupuesto es manual.

## Próxima puerta: 0.2D

Antes de añadir ojos:

1. optimizar conjuntamente las 40 capas existentes;
2. reasignar automáticamente capas desde regiones ya resueltas hacia regiones débiles;
3. introducir puntuación de contorno global;
4. probar varias semillas y conservar la mejor;
5. permitir capas correctoras del color de la región frontal;
6. reducir rectángulos visibles en cabello y cofia;
7. exigir que la silueta base sea limpia a simple vista.

Solo después se iniciará el pase de rasgos faciales.
