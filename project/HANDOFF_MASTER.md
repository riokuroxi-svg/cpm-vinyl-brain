# CPM Vinyl Brain — Handoff maestro

**Fecha:** 22 de julio de 2026  
**Objetivo:** trasladar todo el proyecto a un chat nuevo sin perder contexto ni repetir trabajo.

---

## 1. Visión del producto

Crear una herramienta que convierta una imagen objetivo en una receta de vinilos reproducible en **Car Parking Multiplayer original**, utilizando únicamente el editor visible del juego.

```text
Imagen → análisis → bloques → figuras/texto → receta → vista previa → aplicación asistida
```

La aplicación futura tendrá:

- Cerebro offline;
- Receta JSON;
- editor/vista previa;
- modo manual asistido;
- posteriormente lector y ejecutor por UI visible;
- sin modificar archivos, memoria, economía o servidor.

## 2. Juego objetivo

```text
Nombre: Car Parking Multiplayer original
Paquete: com.olzhas.carparking.multyplayer
Versión pública localizada: 4.9.10
No objetivo inicial: Car Parking Multiplayer 2
```

Datos observados:

- carrocería: 450 capas en capturas del usuario;
- ventanas: 100 capas según reseña pública, pendiente de confirmar;
- texto, fuentes, Bold, Italic y HEX;
- rotación y escalas X/Y visibles;
- selección múltiple/copia/capas;
- texto Unicode posible pero puede variar Android/iOS.

## 3. Restricción legal

La EULA prohíbe ingeniería inversa, descompilación, modificación y apps que modifiquen contenido. Decisión:

- no extraer APK;
- no GameGuardian/mods;
- no redistribuir assets propietarios;
- usar caja negra: capturas, UI, experimentos y documentación pública;
- los modelos 3D externos solo se registran como referencias; no se incluyen.

## 4. Imágenes oficiales de prueba

### Bocchi / cabello rosa

`test_inputs/Picsart_26-07-20_03-08-30-510.png`

- dominio conocido;
- fondo transparente;
- ojos detallados;
- cabello rosa largo;
- ropa de maid.

### Personaje azul con orejas de gato

`test_inputs/Screenshot_20251204_130831_edit_418573429064023.jpg`

- prueba de generalización;
- fondo opaco claro;
- cabello azul;
- ojos grandes;
- peluche en primer plano.

Regla: una mejora no se aprueba si solo mejora Bocchi y empeora el personaje azul.

## 5. Historia de versiones

### 0.1 — Greedy por color

- Kotlin/JVM y CLI;
- CIELAB/ΔE;
- agregaba una forma cada vez;
- resultado tipo pintura al óleo;
- infraestructura válida, algoritmo visual rechazado.

### 0.2A — Simplificación

- Python/OpenCV;
- fondo, cabello, piel, ropa y blancos;
- niveles base/estructura/rasgos/cuantizado;
- `regions.json`.

### 0.2B — Subpartes

- 30 máscaras;
- ojos, rostro, cabello frontal/posterior, ropa, accesorios;
- `layer_graph.json`.

### 0.2C/0.3 — Solver regional

- figuras sólidas;
- capas por región;
- opacidad 1;
- ojos/rasgos;
- mejor coherencia, pero formas rígidas.

### 0.5 — Optimize & Reduce

- pool virtual 500;
- ADD/CUT;
- recetas 64/128/256/430;
- gana métricas frente a 0.3 en Bocchi;
- falla visualmente cuando el target semántico es erróneo;
- queda como baseline/corrector, no generador final.

### 0.6 — Arquitectura por bloques

Diseñada, no completamente implementada:

- presupuesto 280;
- cabello, rostro, cada ojo, ropa, accesorios;
- máximo 25 correcciones globales;
- bloque inválido detiene pipeline;
- ensamblador mueve grupos completos.

### Brain 1.0 experimental — Diferenciable

- `research/diff_brain/renderer.py`;
- PyTorch `affine_grid/grid_sample`;
- selección suave de figura;
- optimización conjunta X/Y/escala/ángulo/color;
- primera prueba de ojo Bocchi ejecutada con 16 capas/250 pasos;
- todavía no integrado al pipeline completo.

## 6. Hallazgo japonés fundamental

Fuentes:

- https://gamerch.com/cpm/321964
- https://gamerch.com/cpm/294126

Flujo experto:

```text
canvas de seguridad
→ guías temporales
→ line art completo
→ relleno
→ sombras
→ corrección
```

- El line art se dibuja sobre todo con el carácter ASCII `(` estirado y rotado.
- Círculos/gotas/rectángulos rellenan color.
- Completar line art antes de rellenar evita caos Z.
- Colocar rectángulo base evita capas negativas/desaparición online.
- HEX visible necesita ajuste por shader.
- Unicode/guiones/números pueden variar Android/iOS.

## 7. Catálogo actual

### 42 máscaras ejecutables

- 13 originales extraídas de capturas del usuario;
- 29 geometrías genéricas creadas proceduralmente desde cero;
- no se copiaron PNG de Gamerch;
- no se incluyen stamps artísticos/logos/animales/personajes.

Archivo: `src/main/resources/catalog.json` versión 2.

Vista: `previews/Nuevo_Catalogo_Geometrico_42.png`.

Metadatos públicos adicionales:

`research/analyzer_v02/catalog_cpm_public_metadata.json`.

## 8. Estado de tests

Pruebas Python: 9 aprobadas antes de ampliar catálogo; después de ampliar a 42, las pruebas Python siguen aprobando.

Prueba diferenciable de ojo:

- target: `research/diff_brain/test_eye_bocchi/target.png`;
- salida: `research/diff_brain/test_eye_bocchi/result/preview.png`;
- receta suave: `recipe_soft.json`;
- pérdida bajó aproximadamente de 0.93 a 0.21 en 250 pasos CPU;
- usa paréntesis sintético DejaVu solo como prueba, no glifo real CPM.

## 9. Problemas conocidos

### Parser

- favorece cabello rosa/rojo;
- falla en cabello azul;
- fondo opaco claro se confunde;
- blue target perdió partes de ojos/hair;
- debe detenerse con `NEEDS_MASK_CORRECTION`.

### Solver

- 0.5 puede mejorar métricas con mosaicos;
- no usar SSIM global como única verdad;
- contornos y landmarks mandan;
- 430 no es objetivo principal; diseño objetivo 280.

### Texto

- falta captura real de `(` por fuente/plataforma;
- Unicode raro no portable;
- ASCII medio ancho preferido.

### 3D

- no hay perfil de vehículo calibrado;
- modelo BMW Sketchfab está registrado pero no incluido;
- proveniencia subyacente incierta;
- usar solo mediante descarga oficial/atribución y localmente.

## 10. Estructura de carpetas

```text
project/
├── README.md
├── HANDOFF_MASTER.md
├── requirements-brain.txt
├── requirements-diff.txt
├── docs/
├── research/
│   ├── analyzer_v02/
│   ├── cpm_capture/
│   ├── diff_brain/
│   └── generate_public_geometric_shapes.py
├── src/main/resources/
│   ├── catalog.json
│   └── shapes/ (42 PNG)
└── src/main/kotlin/ (legacy 0.1)
```

## 11. Comandos

### Brain 0.5 baseline

```bash
pip install -r requirements-brain.txt
./run_brain.sh imagen.png resultado quality
```

### Tests

```bash
cd research/analyzer_v02
python3 -m unittest -v \
  test_analyzer.py test_subparts.py test_solver_v02c.py \
  test_solver_final.py test_solver_v05.py
```

### Regenerar 29 figuras

```bash
python3 research/generate_public_geometric_shapes.py
```

### Diferenciable

```bash
pip install -r requirements-diff.txt
python3 research/diff_brain/optimize_block.py \
  --shapes src/main/resources/shapes \
  --target target.png \
  --allowed-mask allowed.png \
  --out result --layers 25 --steps 1200
```

### Capture Toolkit

Ver `research/cpm_capture/README.md`.

## 12. Qué debe hacer el siguiente desarrollador/agente

### Prioridad 1 — Parser robusto

- fondo opaco/transparente;
- cabello independiente de hue;
- dos ojos obligatorios;
- corrección por puntos;
- confidence gates.

### Prioridad 2 — LineArtSolver

- capturar glifo real `(` en Android;
- target = bordes;
- optimización diferenciable por bloque;
- continuidad/grosor/intersección;
- discretizar a opacidad 1.

### Prioridad 3 — EyeTemplateSolver

- blanco, iris, pupila, pestañas, reflejo, CUT piel;
- landmarks y dirección de mirada;
- validar ambas imágenes.

### Prioridad 4 — FillSolver

- círculos/gotas/rectángulos dentro de line art;
- color calibrado;
- sombras después.

### Prioridad 5 — Ensamblar 280

- bloques aprobados;
- no más de 25 correcciones globales;
- mover bloque completo;
- evaluar tamaño real.

### Prioridad 6 — Editor CPM

- catálogo completo visible;
- campos numéricos/IME;
- body 450/window confirmar;
- copy/mirror/grupos;
- perfil de un coche;
- carta de color.

## 13. Criterios de “listo para test”

No marcar listo hasta:

1. ambos ojos Bocchi aprobados;
2. ambos ojos azul aprobados;
3. cabello rosa y azul correctos;
4. fondo opaco/transparente correcto;
5. bloques independientes exportados;
6. receta ≤280;
7. global corrections ≤25;
8. preview comparable al original a tamaño real;
9. ninguna regresión entre las dos imágenes.

## 14. Mensaje para el nuevo chat

Leer primero:

1. `HANDOFF_MASTER.md`;
2. `docs/HALLAZGOS_WIKI_JAPONESA_CPM.md`;
3. `docs/BRAIN_0_6_ARQUITECTURA_POR_BLOQUES.md`;
4. `docs/REESCRITURA_DIFERENCIABLE_BRAIN_1_0.md`;
5. `docs/INVESTIGACION_CPM_ORIGINAL_2026.md`.

No reiniciar desde Primitive/greedy. No declarar finalizado sin cumplir las puertas. Mantener CPM original y presupuesto 280.
