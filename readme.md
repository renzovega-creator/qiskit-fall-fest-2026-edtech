# Qiskit en español: las guías de IBM Quantum, narradas

Curso en español, narrado y con animaciones, sobre las guías de IBM Quantum y
Qiskit. Son 63 lecciones en diez partes, desde qué es Qiskit hasta
organizaciones y seguridad. Cada lección es una secuencia de pasos con voz,
subtítulos, código que se ejecuta y preguntas. Algunas traen una misión en un
cuaderno de práctica.

El curso corre en tu equipo: las lecciones son una página estática y los
cuadernos usan el entorno de Python del proyecto.

## Instalar

Necesitas [uv](https://docs.astral.sh/uv/). `mise.toml` fija las versiones de
Python y de uv; con [mise](https://mise.jdx.dev/) se instalan solas.

```sh
uv sync
```

## Ver el curso

```sh
uv run python tools/serve.py
```

Abre <http://localhost:8810/>. La portada muestra las lecciones por parte y tu
progreso. Una lección se abre en `lesson.html?l=<id>`, por ejemplo
<http://localhost:8810/lesson.html?l=p1-quickstart>. Las fórmulas se cargan de
un CDN, así que la página necesita conexión a internet. `tools/serve.py` sirve
`site/` y además corrige los ejercicios de código de las lecciones; ver
[docs/exercises.md](docs/exercises.md).

## Abrir un cuaderno de práctica

```sh
uv run marimo edit practica/p1-quickstart.py
```

Es el comando que muestra la misión de la lección 1.4. Los cuadernos están en
[`practica/`](practica/) y sus soluciones, para `tools/practica.py`, en
`practica/soluciones/`.

## Reconstruir las lecciones y la narración

Las lecciones se escriben en [`lessons_src/`](lessons_src/). Después de
editarlas:

```sh
uv run python tools/fetch_docs.py
uv run python lessons_src/build.py
```

El primer comando descarga las guías originales de Qiskit a `.cache/` (solo la
primera vez). El segundo regenera `site/lessons/<id>/lesson.json` y
`site/course.json`, y comprueba que cada guía original tenga lección.

Para generar también el audio y los tiempos:

```sh
uv run python lessons_src/build.py --tts
```

Necesita red (Edge TTS) y `ffprobe` (viene con ffmpeg). Solo se sintetizan los
clips cuyo texto cambió.

## Comprobar

```sh
mise run check
```

Descarga las guías si faltan, comprueba que los JSON de `site/` coincidan con lo
que genera `build.py` (si están desactualizados, falla y `mise run build` los
regenera), ejecuta los cuadernos con y sin sus soluciones, corrige los
ejercicios de código y ejecuta el código Python que muestran las lecciones. La
definición de cada paso está en [`mise.toml`](mise.toml).

## Más

[`docs/architecture.md`](docs/architecture.md) explica qué contiene cada carpeta
y cómo llega una lección desde su código fuente hasta el navegador.
[`docs/exercises.md`](docs/exercises.md) describe cómo se escribe y se corrige
un ejercicio de código.
