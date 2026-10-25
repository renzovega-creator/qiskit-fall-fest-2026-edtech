# Desarrollo

Cómo correr QuantumShot en tu equipo, editar las lecciones y publicar la web.
Para usar la web, mira el [README](../readme.md).

## Preparar el proyecto

Instala [mise](https://mise.jdx.dev/) y ejecuta desde la raíz:

```sh
mise install
uv sync --locked --all-groups
bun install --cwd editor --frozen-lockfile
mise run generate:vendor
```

`mise.toml` fija las versiones de las herramientas. El último paso copia las
tipografías y KaTeX a `site/vendor/`, para servirlos desde el propio sitio.

## Abrir la web

En PowerShell:

```powershell
$env:QG_CURSO = "qml"
uv run python tools/serve.py
```

En Linux o macOS:

```sh
QG_CURSO=qml uv run python tools/serve.py
```

Abre <http://localhost:8810/>. El servidor local sirve la web y ejecuta el
código del editor en tu equipo. En Windows funciona **Ejecutar**; la corrección
automática por casos de prueba requiere Linux o macOS. El servidor escucha solo
en `127.0.0.1`; el progreso se guarda en el navegador y no se sincroniza con una
cuenta.

## Editar las lecciones

El contenido está en [`cursos/qml/`](../cursos/qml/): `plan.py` define el
recorrido, `parte1.py` y `parte2.py` las lecciones y `exercises/` sus
ejercicios. El motor que las convierte en páginas está en `lessons_src/`, y las
actividades con clic (taller de circuitos, muestreo, mapas de kernels) en
`site/labs.js`.

Con `QG_CURSO=qml` definido, regenera el contenido:

```sh
uv run python lessons_src/build.py
```

Para regenerar también la narración y sus tiempos, añade `--tts` (necesita
conexión a internet).

## Comprobar

Con `QG_CURSO=qml`, comprueba que los archivos publicados coincidan con las
lecciones:

```sh
uv run python lessons_src/build.py --check
```

En Linux o macOS puedes comprobar también las soluciones de los ejercicios:

```sh
QG_CURSO=qml uv run python tools/exercises.py
```

## Publicar en GitHub Pages

La versión pública se publica desde la raíz de la rama `gh-pages`:

```sh
python tools/pages.py shots/pages
```

El comando prepara una carpeta con las lecciones, sus audios, las tipografías y
los archivos de la web. Sube su contenido a `gh-pages` y, en **Settings →
Pages**, elige **Deploy from a branch**, la rama `gh-pages` y la carpeta
`/ (root)`.

GitHub Pages sirve una demo estática: lecciones, animaciones, actividades con
clic, progreso local y el perfil de ejemplo (`juego.html#ejemplo`) con resultados
precalculados de Qiskit. No ofrece cuentas ni ejecuta Python. El editor se puede
leer, pero sus botones quedan desactivados y el código no se envía. Para usarlo,
inicia la versión local con `tools/serve.py`. La demo pública no usa un Worker;
consulta [Privacidad](../site/privacidad.html) para ver qué se guarda en cada
versión.
