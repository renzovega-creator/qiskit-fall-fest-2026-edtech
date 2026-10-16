# Arquitectura

El curso es una página estática (`site/`) que reproduce lecciones descritas en
JSON. Las lecciones se escriben en Python, el audio se sintetiza aparte y los
cuadernos de práctica son archivos marimo. Este documento dice qué posee cada
carpeta y por dónde pasa una lección.

## Quién posee qué

| Carpeta        | Contenido                                                                                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lessons_src/` | Las lecciones como código Python y el programa que las convierte en JSON.                                                                                |
| `tools/`       | Programas auxiliares: guías originales, narración, comprobaciones y pruebas de navegador.                                                                |
| `site/`        | La página estática: portada, reproductor de lecciones y los datos que lee.                                                                               |
| `tests/`       | Pruebas de navegador (`theme_test.py`, `proyecto_test.py`, `exercise_ui_test.py`) de ejercicios (`exercises_test.py`) y del corredor (`runner_test.py`). |
| `practica/`    | Los cuadernos marimo de las misiones y sus soluciones.                                                                                                   |
| `exercises/`   | Los ejercicios de código: código inicial, solución y casos de cada uno.                                                                                  |
| `editor/`      | El paquete que compila `site/editor.js`, el editor de los ejercicios.                                                                                    |
| `qgcheck/`     | El corrector de ejercicios: lee `exercises/`, ejecuta el código de un alumno y devuelve el resultado de cada caso.                                       |
| `content/`     | La caché de la síntesis de voz.                                                                                                                          |
| `runner/`      | El corredor de código del alumno: imagen, servidor `/run` y Worker. [runner.md](runner.md)                                                               |

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
  También completa cada bloque `Exercise` con lo que el sitio puede mostrar de
  `exercises/` (ver [exercises.md](exercises.md)).

### `tools/`

| Programa                                             | Función                                                                                                                             |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `fetch_docs.py`                                      | Descarga `docs/guides` de Qiskit/documentation a `.cache/qiskit-docs`, en la versión de `qiskit-docs.commit`.                       |
| `extract.py`                                         | Convierte esas guías en texto plano en `.cache/qiskit-docs/text`.                                                                   |
| `tts.py`                                             | Sintetiza la narración de una lección y escribe `timings.json`.                                                                     |
| `pronunciacion.py`                                   | Diccionario que reescribe siglas y nombres en inglés para que la voz los lea bien.                                                  |
| `verify.py`                                          | Ejecuta el Python de las lecciones, salvo `norun`, y compara los `Out(…, check=True)`.                                              |
| `practica.py`                                        | Ejecuta cada cuaderno con y sin soluciones. También prueba `mo.ui.slider`/`number` en mínimo y máximo. Un error de ejecución falla. |
| `exercises.py`                                       | Corre la solución y el código inicial de cada ejercicio con `qgcheck` y comprueba su `needs`.                                       |
| `serve.py`                                           | Sirve `site/` en 127.0.0.1:8810 y añade `POST /run`, que corrige un ejercicio con `qgcheck`, y `/config.json`.                      |
| `playtest.py`, `seektest.py`, `shot.py`, `review.py` | Pruebas y capturas con Playwright sobre `site/` servido en el puerto 8810.                                                          |

`qiskit-docs.commit` guarda el hash de Qiskit/documentation contra el que se
comprueba la cobertura. Para actualizar las guías se cambia ese hash, se ejecuta
`tools/fetch_docs.py` y se corrige `plan.py` hasta que `build.py` pase.

### `site/`

- `index.html` es la portada, con los estilos de `index.css`. Lee `course.json`
  y pide en paralelo los `lesson.json` de las lecciones completadas para armar
  el repaso.
- `lesson.html` carga `engine.js`, el reproductor, con los estilos de `app.css`.
  `blocks.js` dibuja los bloques propios del curso, `exercise.js` el bloque de
  ejercicio y `sfx.js` los sonidos. Las fórmulas las dibuja KaTeX, que se
  descarga de un CDN.
- `editor.js` es el editor CodeMirror 6 de los ejercicios, empaquetado desde
  `editor/`. `config.json` trae la URL del corredor que escribe `build.py`.
  Ambos se describen en [exercises.md](exercises.md#editor-en-la-lección).
- `theme.css` y `theme.js` son el tema de las dos páginas: colores, fuentes, y
  la paleta y el modo que elige el lector. [design.md](design.md) los describe.
  `notebooks.js` escribe la línea «cómo ejecutar los cuadernos» que acompaña a
  cada comando de `marimo`.
- `lessons/<id>/` contiene `lesson.json`, `timings.json` y `audio/<paso>.mp3`.
- `course.json` es el índice: partes, lecciones, minutos y misiones.

### `practica/`

Los cuadernos marimo son los `.py` de estas carpetas que contienen
`marimo.App(`. Un cuaderno puede importar un módulo de su carpeta
(`proyecto/ising.py`), porque `tools/practica.py` pone esa carpeta en
`sys.path`. Cada misión de una lección nombra su cuaderno con `Mission(...)`.
`soluciones/<cuaderno>.json` (con `__` en lugar de `/` para los cuadernos de
subcarpetas) guarda los pares (texto, reemplazo) que `tools/practica.py` aplica
para comprobar que todas las verificaciones dan ✅.

### `exercises/` y `qgcheck/`

`exercises/<lección>/<ejercicio>/` guarda `starter.py`, `solution.py` y
`check.py`. `qgcheck/spec.py` los localiza, `qgcheck/runner.py` lanza
`qgcheck/worker.py` en un proceso aparte con el código del alumno, y
`qgcheck/__init__.py` ofrece a `check.py` sus ayudantes. El formato, el
resultado de `grade()` y las comprobaciones están en
[exercises.md](exercises.md). `site/exercise.js` dibuja el editor de cada
ejercicio y llama a `POST /run` en la URL de `site/config.json`.

### `content/`

`<id>.cache.json` guarda, por cada clip de una lección, el hash de lo que se
dijo y los tiempos de cada palabra. `tts.py` lo consulta para no volver a
sintetizar un clip que no cambió.

### `runner/`

El servidor del corredor ([runner.md](runner.md)) ejecuta los trabajos en
_ranuras_. Hay `QG_JOBS` ranuras, numeradas desde 0, y la ranura `n` usa siempre
el uid `20000 + n`. El estado compartido es la cola `FREE_SLOTS` de ranuras
libres, en `server.py`.

| Estado  | Significa                                     | Quién lo deja y cuándo                                                                                            |
| ------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| libre   | Su número está en `FREE_SLOTS`.               | El hilo de una petición, en el `finally` de `do_POST`, cuando `run_job` ya volvió.                                |
| ocupada | Un hilo de petición tiene su número y la usa. | El mismo hilo, tras validar la petición, con `get_nowait()`. Si la cola está vacía responde 503 y no espera nada. |

- Solo el hilo que tomó una ranura la devuelve, y solo después de que `run_job`
  matara los procesos de ese uid y borrara su directorio y sus archivos de
  `/scratch`, `/tmp`, `/var/tmp` y `/dev/shm`. Ese borrado es lo que aísla a un
  trabajo del anterior, porque el uid se reutiliza.
- `run_job` lanza un hilo (`_Scan`) que mide memoria y disco. Solo ese hilo
  escribe `peak` y `killed` (`killed` antes de `tripped`); `run_job` los lee
  tras `tripped` o tras unir el hilo.
- Las instancias de Cloudflare no comparten nada: cada una tiene su cola. El
  Worker elige una de tres y, si responde 503, repite la petición una vez, que
  puede llegar a la misma instancia.

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
