# Arquitectura

El curso es una página estática (`site/`) que reproduce lecciones descritas en
JSON. Las lecciones se escriben en Python, el audio se sintetiza aparte y los
cuadernos de práctica son archivos marimo. Este documento dice qué posee cada
carpeta y por dónde pasa una lección.

## Quién posee qué

| Carpeta        | Contenido                                                                                 |
| -------------- | ----------------------------------------------------------------------------------------- |
| `lessons_src/` | Las lecciones como código Python y el programa que las convierte en JSON.                 |
| `tools/`       | Programas auxiliares: guías originales, narración, comprobaciones y pruebas de navegador. |
| `site/`        | La página estática: portada, reproductor de lecciones y los datos que lee.                |
| `practica/`    | Los cuadernos marimo de las misiones y sus soluciones.                                    |
| `content/`     | La caché de la síntesis de voz.                                                           |

### `lessons_src/`

- `plan.py` define `PARTS`: las diez partes, el orden de las lecciones y qué
  guías originales cubre cada una. Una guía aparece en exactamente una lección.
- `parte1.py` a `parte10.py` definen `LESSONS`, la lista de lecciones de cada
  parte, con las funciones de `lib.py`: `lesson()`, `beat()`, los bloques
  (`Code`, `Out`, `Circ`, `Hist`…), las acciones (`A`) y las preguntas
  (`choice`, `numeric`, `reveal`, `predict`, `reflect`).
- `build.py` une el plan con las lecciones y escribe los JSON de `site/`. Antes
  comprueba que cada guía del índice de Qiskit/documentation esté en el plan,
  que no haya marcas `[[nombre]]` repetidas en una narración y que cada acción
  apunte a una marca y a un objeto que existan. Falla si una lección del plan no
  tiene módulo o si un módulo define una lección que el plan no menciona.

### `tools/`

| Programa                                             | Función                                                                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `fetch_docs.py`                                      | Descarga `docs/guides` de Qiskit/documentation a `.cache/qiskit-docs`, en la versión de `qiskit-docs.commit`. |
| `extract.py`                                         | Convierte esas guías en texto plano en `.cache/qiskit-docs/text`.                                             |
| `tts.py`                                             | Sintetiza la narración de una lección y escribe `timings.json`.                                               |
| `pronunciacion.py`                                   | Diccionario que reescribe siglas y nombres en inglés para que la voz los lea bien.                            |
| `verify.py`                                          | Ejecuta el código Python de las lecciones y compara los `Out(…, check=True)`.                                 |
| `practica.py`                                        | Ejecuta cada cuaderno de `practica/` sin y con sus soluciones.                                                |
| `playtest.py`, `seektest.py`, `shot.py`, `review.py` | Pruebas y capturas con Playwright sobre `site/` servido en el puerto 8810.                                    |

`qiskit-docs.commit` guarda el hash de Qiskit/documentation contra el que se
comprueba la cobertura. Para actualizar las guías se cambia ese hash, se ejecuta
`tools/fetch_docs.py` y se corrige `plan.py` hasta que `build.py` pase.

### `site/`

- `index.html` es la portada. Lee `course.json` y los `lesson.json` de las
  lecciones completadas para armar el repaso.
- `lesson.html` carga `engine.js`, el reproductor. `blocks.js` dibuja los
  bloques propios del curso, `sfx.js` los sonidos y `theme.js` el tema. Las
  fórmulas las dibuja KaTeX, que se descarga de un CDN.
- `lessons/<id>/` contiene `lesson.json`, `timings.json` y `audio/<paso>.mp3`.
- `course.json` es el índice: partes, lecciones, minutos y misiones.

### `practica/`

`p1-quickstart.py`, `p2-circuitos.py` y `proyecto/hito1.py` son cuadernos
marimo. Cada misión de una lección nombra su cuaderno con `Mission(...)`.
`soluciones/<cuaderno>.json` (con `__` en lugar de `/` para los cuadernos de
subcarpetas) guarda los pares (texto, reemplazo) que `tools/practica.py` aplica
para comprobar que todas las verificaciones dan ✅.

### `content/`

`<id>.cache.json` guarda, por cada clip de una lección, el hash de lo que se
dijo y los tiempos de cada palabra. `tts.py` lo consulta para no volver a
sintetizar un clip que no cambió.

## Camino de los datos

```text
plan.py + parte*.py -> build.py -> lesson.json (y course.json)
lesson.json -> tts.py -> audio/<paso>.mp3 + timings.json
lesson.json + timings.json + audio -> engine.js
```

1. `build.py` numera las secciones según el orden de `plan.PARTS`, añade a cada
   lección el enlace a sus guías originales y escribe `lesson.json` con la lista
   de pasos y `next`, la lección siguiente. `course.json` suma los minutos: la
   duración de `timings.json` si existe, o una estimación por palabras si no,
   más 45 segundos por pregunta.
2. `tts.py` lee `lesson.json`. Por cada paso aplica `pronunciacion.py` al texto
   de `say`, sintetiza `audio/<paso>.mp3` con Edge TTS y mide su duración con
   `ffprobe`. `timings.json` guarda por paso `dur` (segundos), `marks` (el
   segundo en que empieza la palabra que sigue a cada `[[marca]]`) y `cues` (los
   subtítulos con su segundo de inicio, con el texto original).
3. `engine.js` carga `lesson.json` y `timings.json`, reproduce el audio de cada
   paso y lanza cada acción de `actions` en el segundo de su marca. Los
   subtítulos salen de `cues`. `?beat=N` muestra el estado final del paso N sin
   audio.
