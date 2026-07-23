# Fase 1 — Cerebro aislado

## Objetivo

Demostrar que las 13 figuras disponibles pueden aproximar imágenes objetivo de manera reconocible dentro de un presupuesto realista de capas.

## Entregable actual: 0.1.0

- Motor JVM sin dependencia de Android.
- Catálogo y máscaras.
- Receta JSON v1.
- Renderizador.
- Optimizador greedy inicial.
- CLI, pruebas y CI.

## Protocolo de evaluación

Para cada imagen de prueba, generar versiones de:

- 30 capas: prueba rápida y diseños simples.
- 100 capas: calidad media.
- 280 capas: presupuesto de carrocería mencionado en el plan maestro.
- 450 capas: límite superior observado en las capturas, pendiente de confirmar.

Guardar para cada ejecución:

- Imagen original.
- Objetivo normalizado.
- Vista previa.
- Receta.
- Semilla.
- ΔE inicial/final.
- Tiempo total.
- Evaluación visual: no reconocible / parcialmente / reconocible / muy fiel.

## Criterios de aceptación

La Puerta B se considera aprobada si:

1. Al menos 4 de 5 imágenes sencillas son reconocibles sin ver el original.
2. El error disminuye de forma consistente al aumentar las capas.
3. Una receta produce la misma vista previa al volver a renderizarse.
4. Ninguna capa referencia una figura inexistente.
5. El tiempo de cálculo es razonable para trasladarlo después a Android.

## Pruebas sugeridas

1. Logotipo de dos colores.
2. Cara estilo caricatura con contornos grandes.
3. Personaje anime simplificado.
4. Emblema con texto convertido a formas; se espera dificultad alta.
5. Imagen con degradados para evaluar los pinceles y el brillo.

## Decisiones pendientes que no bloquean el Cerebro 0.1

- CPM 1 o CPM 2.
- Límites exactos de escala y rotación.
- Precio real de cada figura.
- Resolución y relación de aspecto de cada sección del vehículo.
- Precisión de entrada disponible en el juego.

Estas restricciones se agregarán al optimizador como un `GameProfile` cuando la Fase 0 de observación esté documentada.
