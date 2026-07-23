# Registro de decisiones

## 2026-07-20 — Comenzar por el Cerebro

Se acuerda implementar y validar primero el módulo aislado:

```text
imagen → receta → vista previa
```

Quedan aplazados hasta aprobar la Puerta B:

- app Android;
- overlay;
- captura de pantalla;
- OCR;
- IME;
- accesibilidad y ejecución automática.

## Catálogo inicial

Se adoptan las 13 figuras blancas con transparencia creadas a partir de las capturas del usuario. Son el catálogo v1 y se distribuyen como recursos del módulo JVM.

## Métrica inicial

La versión 0.1 utiliza CIELAB y ΔE76. Es una decisión provisional de ingeniería para validar la arquitectura y podrá migrar a ΔE2000 sin cambiar el formato de Receta.

## Formato intermedio

La Receta JSON es el contrato principal. El optimizador y el futuro ejecutor Android no dependerán directamente uno del otro.

## 2026-07-20 — Rechazo visual del optimizador 0.1

La prueba con una ilustración anime demostró que el ciclo técnico funciona, pero el resultado se percibe como pintura al óleo. Se decide no considerar aprobada la Puerta B.

El greedy basado solamente en ΔE deja de ser el algoritmo principal. La versión 0.2 usará regiones, contornos, capas sólidas, orden de oclusión y refinamiento global. Ver `REDISENO_CEREBRO_0_2.md`.

## 2026-07-20 — Analizador 0.2A implementado

Se implementa primero un backend reproducible de color y conectividad para validar máscaras, niveles progresivos y `regions.json`. La integración de un parser neuronal se mantiene intercambiable y no bloquea la prueba estructural.

La primera salida ya produce una base sin ojos ni boca y conserva cabello, rostro, ropa, cofia y delantal.

## 2026-07-20 — Analizador 0.2B implementado

Se separan 30 subpartes y se crea un grafo validado de 30 relaciones detrás→delante. El solucionador de vinilos podrá trabajar por región y respetar el orden de oclusión.

La siguiente puerta es el Solucionador 0.2C: ajustar figuras sólidas solamente al Nivel 0, sin ojos ni texturas.

## 2026-07-20 — Solucionador regional 0.2C implementado

Se genera una primera receta de 40 capas, todas opacas y asociadas a regiones. La cobertura regional media alcanza 81.4%. El resultado elimina el aspecto de pintura, pero la silueta aún necesita refinamiento.

Se decide no añadir ojos todavía. La versión 0.2D optimizará globalmente la base, reasignará presupuesto y mejorará contornos.

## 2026-07-20 — Brain 0.3 integrado y congelado para pruebas

Se completan estructura, rasgos faciales, accesorios, políticas de forma, múltiples inicializaciones, refinamiento regional y orquestador de un comando.

La demostración `quality` produce 127 capas sólidas, cobertura regional media 84.40% y SSIM semántico 0.8608. El código se congela como versión de pruebas 0.3.0; los siguientes cambios dependerán de resultados sobre cinco imágenes variadas.

No se iniciará Android antes de evaluar la generalización, especialmente cabello no rosado y fondos sin transparencia.

## 2026-07-21 — Texto como catálogo geométrico

Las capturas confirman que el editor ofrece texto con fuentes, Bold, Italic, color y transformaciones. Se decide tratar glifos como primitivas geométricas y no solo como contenido textual.

La versión 0.4 añadirá, tras capturar las fuentes reales, familias de líneas, curvas, anillos y ángulos, además de un pase final para rellenar huecos residuales. Antes de programar el catálogo se verificará que cadenas repetidas sigan contando como una sola capa.

## 2026-07-21 — Brain 0.5 Optimize & Reduce implementado

Se reemplaza el límite interno por un pool virtual de 500 capas, correcciones ADD/CUT y reducción progresiva a 64/128/256/430.

Comparación al mismo presupuesto: Brain 0.5 con 128 capas obtiene puntuación 0.8653 frente a 0.8125 de Brain 0.3 con 127. La versión 0.5 pasa a ser el baseline oficial; 0.3 queda como fallback.

La receta 430 reserva 20 capas del límite 450 para calibración real.

## 2026-07-21 — La prueba de cabello azul rechaza el generador global

La segunda imagen demuestra que un buen ajuste al objetivo semántico no sirve cuando el parser y el ensamblaje pierden ojos o jerarquía. Las capturas de diseños humanos muestran coherencia con aproximadamente 280 capas.

Se retira Brain 0.5 como generador visual oficial; queda como herramienta de corrección/benchmark. Brain 0.6 adopta bloques independientes, presupuesto total 280, templates especializados para ojos y máximo 25 correcciones globales. Un fallo de percepción detendrá el pipeline en vez de generar una receta engañosa.

## 2026-07-21 — Objetivo exclusivo CPM original

Se fija `com.olzhas.carparking.multyplayer` como único objetivo inicial. CPM 2 queda fuera del alcance de calibración y ejecución.

Las capturas del usuario confirman 450 capas de carrocería. Una reseña reciente en Google Play sugiere 100 capas de ventanas; se marca como pendiente de verificación.

La investigación pública confirma que texto y símbolos Unicode pueden pegarse como vinilos no presentes en el catálogo básico. El catálogo del Brain se ampliará mediante capturas públicas de la UI, sin extraer el APK.

## 2026-07-22 — Catálogo geométrico v2

A partir de descripciones públicas y capturas propias se recrean proceduralmente 29 formas geométricas genéricas adicionales, sin copiar píxeles de la wiki. El catálogo ejecutable pasa de 13 a 42 máscaras. No se incluyen stamps artísticos, animales, logos o personajes de terceros.

## 2026-07-21 — Reescritura diferenciable

La respuesta anterior quedó interrumpida sin ejecutar una reconstrucción. Se confirma que hill climbing/greedy no basta para máxima fidelidad.

Se inicia un renderizador diferenciable PyTorch por bloques, con optimización conjunta de X/Y/escala/rotación/color y selección suave de figura. La validación comenzará por ojos en las dos imágenes. La ingeniería inversa permitida será únicamente de caja negra sobre entradas/salidas visibles; no se descompilará ni extraerá el APK.
