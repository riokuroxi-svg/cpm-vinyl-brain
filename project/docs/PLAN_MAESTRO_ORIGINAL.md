# Plan Maestro: App de diseño automático de vinilos para Car Parking Multiplayer

**Versión:** 1.0 — Consolidado a partir de 4 propuestas (Claude, Kimi, DeepSeek, Gemini)
**Fecha:** 17 de julio de 2026
**Estado:** Borrador para aprobación del usuario y de las 3 IAs colaboradoras. Ver documento aparte `desacuerdos_y_roles.md` para los puntos donde las propuestas chocan entre sí.

---

## 0. Qué es este documento

Cada IA (Claude, Kimi, DeepSeek, Gemini) entregó un plan por separado. Este documento junta lo mejor y más sólido de los cuatro en una sola versión de trabajo. No repite todo el detalle de cada plan original — esos siguen existiendo como referencia — sino que fija **la versión que vamos a seguir**. Los puntos donde los cuatro planes no coinciden se dejan fuera de aquí y se tratan en `desacuerdos_y_roles.md`.

---

## 1. Objetivo del proyecto

Una app para Android que, a partir de una imagen objetivo (ej. un personaje anime), calcule y aplique una secuencia de vinilos (formas del propio editor de Car Parking Multiplayer) sobre un vehículo, aproximando la imagen lo mejor posible dentro del límite de capas del juego (ej. 280/450 en carrocería, 200 en ventanas — contadores independientes por sección). La app solo simula toques humanos sobre la interfaz real del juego; no modifica memoria, valores de servidor, ni economía del juego.

---

## 2. Decisiones ya tomadas (consenso de las 4 propuestas)

- **Arquitectura de 3 piezas + Receta en medio** (aporte de Kimi, adoptado por todos): en vez de un bucle único capturar→calcular→aplicar, se separa en:
  - **Cerebro**: imagen objetivo → Receta (archivo JSON con la lista exacta de vinilos, posiciones, colores, ángulos).
  - **Receta**: artefacto intermedio, revisable, compartible y reutilizable — permite probar y aprobar el diseño *antes* de gastar una sola moneda o capa real.
  - **Lector + Ejecutor**: leen el estado del juego y aplican la Receta paso a paso, verificando cada acción.
- **Todo el procesamiento de imagen/decisión ocurre en el dispositivo**, sin ninguna API de pago ni clave necesaria.
- **Modo offline / garaje personal**, sin lobbies multijugador, con cuenta secundaria mientras se prueba.
- **Compilación 100% desde Android sin laptop**, vía GitHub (repo + GitHub Actions compilando el APK en la nube; se descarga el resultado directo al teléfono).
- **Modo "manual asistido"** como opción siempre disponible: la app sugiere el próximo paso y el usuario lo aplica con el dedo — reduce riesgo y da valor de producto incluso sin automatización completa.
- **No se toca memoria del proceso ni se usan herramientas tipo GameGuardian.** Es una categoría de herramienta completamente distinta y fuera de alcance.

---

## 3. Arquitectura consolidada

```
Imagen objetivo ──► [CEREBRO] ──► RECETA (JSON) ──► [EJECUTOR] ──► Vehículo en el juego
   (galería)        (algoritmo)      │                (IME + Accesibilidad)
                                     │
                                     ├──► Vista previa renderizada (antes de gastar capas)
                                     ├──► Editor manual de pasos
                                     └──► Archivo compartible / historial
```

### 3.1. Módulos

| Módulo | Responsabilidad | Notas clave |
| :--- | :--- | :--- |
| **Cerebro** | Imagen → Receta. Algoritmo greedy tipo Geometrize/Primitive, restringido al catálogo real de formas del juego. Compara color en **CIELAB/ΔE**, nunca RGB crudo (aporte de Kimi, sección 5 de su plan) | Kotlin/JVM puro → se prueba entero en la nube (GitHub Actions), sin tocar el teléfono ni el juego |
| **Lector** | Captura de pantalla (sesión única y persistente de `MediaProjection`, Android-14-safe) + lectura de campos (OCR con ML Kit *bundled*, más **template matching de dígitos** para los campos numéricos, que es más preciso que OCR genérico para esos casos) | Ver sección 5 sobre por qué la sesión debe ser única |
| **Ejecutor** | Receta → acciones reales. Interfaz única `InputEngine` con implementaciones intercambiables: (1) IME propio + `commitText()`, (2) gestos calibrados + verificación OCR como plan B | Ver sección 4 — este es el hallazgo técnico más importante del proyecto |
| **Perfiles de calibración** | Coordenadas relativas (no en píxeles absolutos) de cada elemento de UI, versionadas por resolución y versión del juego, actualizables sin recompilar | Formato JSON en el repo |
| **Overlay UI** | Panel flotante, botones tipo píldora, arrastrable, con progreso y control de inicio/pausa | Ver sección 7 |
| **Bitácora** | Log de cada acción + capturas de depuración, exportable en un ZIP | Esencial para depurar sin laptop |

---

## 4. El hallazgo técnico central: cómo escribir valores exactos

Este es el aporte más importante que corrige a los planes anteriores (incluido el mío original): **Unity no expone sus campos de texto a las APIs de accesibilidad de Android.** Un `AccessibilityService` puede tocar la pantalla, pero no puede "pegar" texto ni usar `ACTION_SET_TEXT` en un campo de Unity, porque ese campo no existe como nodo de accesibilidad — es solo píxeles dibujados.

**Solución adoptada:** la app incluye **su propio teclado (IME)**. Cuando se toca un campo numérico, el juego abre el teclado del sistema como de costumbre; si nuestro IME está activo, puede escribir el valor exacto con `commitText("-127.5", 1)` — sin gestos, sin aproximaciones, sin OCR para escribir (el OCR se sigue usando para *leer* y verificar).

**Jerarquía de estrategias de entrada** (de mejor a peor, encapsuladas detrás de la misma interfaz `InputEngine`):
1. IME propio + `commitText()` — precisión perfecta, requiere que los campos sean editables (a confirmar en Fase 0).
2. Gestos calibrados sobre sliders + verificación OCR en bucle — plan B si los campos no son editables.
3. Gestos simples (tap) — para navegación de menús, selección de forma, confirmar.

La pregunta de si los campos aceptan teclado es **la puerta de viabilidad más importante de todo el proyecto** — más que el OCR. Se resuelve jugando, en la Fase 0 (ver checklist, sección 9).

---

## 5. Restricciones de plataforma Android que hay que diseñar desde el día 1

- **Android 14+:** el permiso de captura de pantalla se vuelve a pedir cada vez que se crea una nueva `MediaProjection`, y reutilizar el token guardado lanza `SecurityException`. **Diseño obligatorio:** una sola sesión persistente de `MediaProjection` + `VirtualDisplay` durante toda la automatización, con `FOREGROUND_SERVICE_MEDIA_PROJECTION` declarado en el manifiesto.
- **Android 13+:** las apps instaladas por APK (sideload) tienen la Accesibilidad bloqueada por "configuración restringida" hasta que el usuario la habilita manualmente en Ajustes. **Diseño obligatorio:** pantalla de onboarding ilustrada dentro de la app con los pasos exactos.
- **Distribución:** exclusivamente por GitHub Releases (APK), no por Google Play — el caso de uso no pasaría revisión de forma confiable.
- **Toolchain:** JDK 17 (no 11, el Android Gradle Plugin actual lo exige). Empezar con `assembleDebug` (se instala directo, sin gestionar keystores) y dejar `assembleRelease` para cuando haya algo que distribuir formalmente.
- **ML Kit on-device es gratis e ilimitado** (usar el modelo *bundled*, no el que depende de Play Services, para que funcione offline desde el primer arranque).
- **Fabricantes agresivos con batería (MIUI y similares):** servicio en primer plano + wake lock parcial + guía de "sin restricciones de batería" en el onboarding.

---

## 6. El color en un mundo 3D

El coche es un modelo 3D iluminado: un mismo HEX se ve distinto en sombra que en luz directa, y varía según la hora del día del juego. Comparar píxeles crudos en RGB haría que el algoritmo "corrija" sombras que no son errores de diseño.

**Mitigación adoptada:**
1. Comparar color en **espacio CIELAB con ΔE** (nunca distancia euclídea en RGB).
2. Construir una **tabla de calibración** color aplicado → color percibido, aplicando vinilos de colores conocidos en zonas conocidas al inicio.
3. Documentar y fijar una condición de luz constante (hora/escenario del garaje) para calibración y ejecución.
4. La verificación de cada paso individual se hace leyendo el estado (X/Y/ángulo/HEX) por OCR/template matching, no comparando píxeles — la comparación de imagen se reserva para evaluar el resultado global.

---

## 7. Diseño de la app (overlay + lienzo virtual)

Combinando la propuesta de panel flotante (Claude/Kimi/DeepSeek) con el espacio de trabajo independiente que propone Gemini:

- **Lienzo virtual (fuera del juego):** espacio de diseño donde se carga la imagen objetivo, se ve la vista previa generada por el Cerebro, se revisan/editan capas manualmente, y se aprueba la Receta antes de tocar el juego. Esto evita diseñar "a ciegas" directamente sobre la pantalla del juego y ahorra batería/recursos.
- **Overlay flotante (durante la ejecución en el juego):** panel compacto, botones tipo píldora, semi-transparente, arrastrable — inspirado en widgets de reproductores multimedia. Controles: iniciar/pausar, progreso (capa actual/total), configuración, minimizar a burbuja.
- **Navegación vertical (scroll)** para recorrer categorías de vinilos, más rápido que las flechas horizontales nativas del juego.
- **Dos modos de operación siempre disponibles:** automático (IME + accesibilidad aplican la Receta solos) y manual asistido (el overlay muestra "coloca la forma X en posición Y, ángulo Z, color W" y el usuario lo hace con el dedo).

---

## 8. Matriz de riesgos (consolidada)

| Riesgo | Prob. | Impacto | Mitigación |
| :--- | :--- | :--- | :--- |
| Campos X/Y/ángulo no editables por teclado | Media | Alto | Fase 0 lo confirma primero; plan B de gestos+OCR ya diseñado |
| Actualización del juego reubica la UI | Alta (con el tiempo) | Alto | Perfiles de calibración versionados y actualizables sin recompilar |
| Android 14 re-pide permiso de captura | Certeza si se diseña mal | Medio | Sesión única persistente (sección 5) |
| Accesibilidad bloqueada por "configuración restringida" | Certeza en sideload | Medio | Onboarding ilustrado (sección 5) |
| Iluminación 3D distorsiona la comparación de color | Alta | Alto | CIELAB/ΔE + tabla de calibración (sección 6) |
| Detección/suspensión de cuenta por el desarrollador | Baja en offline | Alto | Cuenta secundaria, solo garaje offline, modo manual asistido disponible siempre |
| Sin monedas suficientes a mitad del diseño | Media | Medio | Estimación de costo en la Receta + verificación de saldo antes de empezar |
| OCR confunde caracteres del HEX | Alta | Bajo | Template matching de dígitos + validación por patrón `[0-9A-F]{6}` |
| El sistema mata el servicio en segundo plano (MIUI, etc.) | Media | Medio | Servicio en primer plano + guía por fabricante |
| Algoritmo lento en gama baja | Media | Medio | Cálculo sobre imagen reducida, mutaciones limitadas por iteración |
| Calibración inválida tras cambiar resolución/DPI | Media | Medio | Coordenadas relativas + recalibración rápida |

---

## 9. Roadmap con puertas de decisión

| Fase | Contenido | Puerta de salida | Estimación |
| :--- | :--- | :--- | :--- |
| **-1. Decisiones previas** | ¿CPM 1 o CPM 2? Alcance del MVP (solo carrocería primero). Nombre y repo. | Decisiones escritas en el README | 1 día |
| **0. Checklist jugando** | Responder las preguntas de la sección 10, con capturas/video | **Puerta A:** ¿campos editables por teclado? Define la estrategia de entrada | 2-3 sesiones de juego |
| **1. Cerebro aislado** | Algoritmo greedy en Kotlin/JVM, probado con imágenes de prueba, sin el juego | **Puerta B:** aproximación reconocible a ojo con el número de capas real | 1-2 semanas |
| **2. Lector** | Captura persistente + template matching/OCR sobre capturas reales | **Puerta C:** ≥98% de acierto leyendo los 4 campos en 50 capturas variadas | 1 semana |
| **3. Ejecutor mínimo** | IME propio + accesibilidad; aplicar un vinilo de prueba con valores exactos | **Puerta D:** un vinilo en posición exacta, verificado, 10 de 10 veces | 1-2 semanas |
| **4. MVP integrado** | Receta de ≤30 capas end-to-end, cuenta secundaria, offline | Diseño simple completo sin intervención | 1 semana |
| **5. Productización** | Overlay final, presupuestos por sección, duplicar/espejar, onboarding de permisos | Uso cómodo durante una semana | 2 semanas |
| **6. Compartir** | Exportar/importar Recetas | Primer intercambio de receta | 1 semana |

**Total estimado hasta MVP: 5-7 semanas** de trabajo en tardes. Ninguna fase empieza sin que la anterior esté documentada en el repo (para que cualquier IA retome el contexto).

---

## 10. Checklist de Fase 0 — solo tú puedes responder esto jugando

1. ¿Los campos X, Y y ángulo abren teclado al tocarlos? ¿Aceptan decimales/negativos? ¿Y el HEX?
2. ¿Cuáles son los límites exactos de capas por sección, y varían por vehículo?
3. ¿Cuántas formas base hay en el catálogo? ¿Todas desbloqueadas o hay que comprarlas?
4. ¿Cuánto cuesta cada vinilo en monedas? ¿Precio fijo o depende de forma/tamaño?
5. ¿Existen funciones de duplicar / espejar / reordenar / deshacer capas? ¿Dónde están?
6. ¿La cámara del editor es fija por vista? ¿Se puede ocultar la UI para una captura limpia?
7. ¿Cómo se navega entre carrocería y ventanas? ¿El contador de capas siempre visible?
8. ¿Dónde se guardan los diseños? ¿Sobreviven a reinstalar la app?
9. ¿El editor funciona igual sin internet?
10. ¿La iluminación del garaje cambia con la hora del día del juego? ¿Hay una condición de luz neutra?
11. Versión exacta del juego instalada.

---

## 11. Lo que este plan NO adopta de las propuestas originales (resumen)

Hay dos ideas de los planes de Gemini y DeepSeek que quedan fuera de este plan maestro por razones de legalidad/seguridad de cuenta. Se explican con detalle, y se pide confirmación explícita de cada IA, en el documento `desacuerdos_y_roles.md`. En resumen:

- **No vamos a extraer assets internos del APK de Unity** (texturas/IDs de stickers) para ampliar el catálogo del Cerebro más allá de las formas geométricas genéricas visibles en el editor.
- **No vamos a diseñar la ejecución de gestos con el objetivo explícito de "evadir" un sistema de detección/anti-cheat.** El ritmo humano y las pausas se hacen por buena ingeniería (que la app no se sienta robótica de usar), no como una técnica de evasión.

---

## 12. Roles propuestos (pendiente de confirmación — ver documento de desacuerdos)

| IA | Rol propuesto |
| :--- | :--- |
| Kimi | Plataforma Android profunda: captura persistente, IME, accesibilidad, CI/CD, calibración |
| DeepSeek | El Cerebro: algoritmo de aproximación por primitivas y su rendimiento |
| Claude | Arquitectura general, formato de Receta, revisión de código, documentación del repo |
| Gemini | Lienzo virtual, UI/UX, análisis multimodal de capturas para calibración (con los ajustes de la sección 11) |
| Tú | Producto y QA: checklist de Fase 0, decisiones, pruebas, cuenta secundaria |

---

## Fuentes consultadas

Ver la lista completa de fuentes en el plan original de Kimi (documentación de Android sobre MediaProjection/Android 14, ML Kit on-device, Geometrize/Primitive como algoritmo de referencia, Shizuku, comparativas CPM1 vs CPM2) y en la investigación previa de Claude sobre el desarrollador Olzhass y sus términos de uso.
