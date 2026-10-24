# QuantumShot · Del ML al QML

Aprende computación cuántica desde conceptos de estadística y machine learning
que ya conoces. Cada lección conecta una idea clásica con su equivalente
cuántico: escuchas la explicación, predices un resultado, experimentas y
programas con Qiskit.

El curso está en español. Actualmente tiene dos lecciones narradas, dos
ejercicios de código, tres misiones y un reto que combina muestreo y kernels.

| Lección                              | Qué exploras                                                           |
| ------------------------------------ | ---------------------------------------------------------------------- |
| Monte Carlo ↔ shots                  | Regla de Born, frecuencias y error de muestreo.                        |
| SVM con kernel RBF ↔ kernel cuántico | Feature maps, similitud entre estados y comparación de clasificadores. |

Las misiones dejan evidencias en un portafolio compartible y actualizan un mapa
de habilidades. Los experimentos usan un simulador de Qiskit. El progreso de las
misiones y el portafolio se guardan en este navegador.

## Preparar el proyecto

Instala [mise](https://mise.jdx.dev/) y ejecuta desde la raíz:

```sh
mise install
uv sync --locked --all-groups
bun install --cwd editor --frozen-lockfile
bun install --cwd runner/worker --frozen-lockfile
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

Abre <http://localhost:8810/>. Desde la portada puedes entrar a las lecciones,
las [misiones](http://localhost:8810/juego.html) y el portafolio.

El servidor local ejecuta los experimentos. La corrección automática de los
ejercicios necesita Linux o macOS; en Windows, usa WSL. Las misiones pueden
ejecutarse con el servidor local en Windows.

## Editar las lecciones

El contenido está en [`cursos/qml/`](cursos/qml/): `plan.py` define el
recorrido, `parte1.py` y `parte2.py` contienen las lecciones, y `exercises/` sus
ejercicios. El motor que las convierte en páginas está en `lessons_src/`.

Con `QG_CURSO=qml` definido, regenera el contenido:

```sh
uv run python lessons_src/build.py
```

En PowerShell define la variable como en el apartado anterior. En Linux o macOS
puedes anteponer `QG_CURSO=qml` a cada comando.

Para actualizar la narración y sus tiempos, añade `--tts`. La síntesis de voz
necesita conexión a internet.

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

El comando prepara una carpeta nueva con las dos lecciones activas, sus audios,
las tipografías y los archivos de la web. Sube el contenido de esa carpeta a
`gh-pages`. En **Settings → Pages**, elige **Deploy from a branch**, la rama
`gh-pages` y la carpeta `/ (root)`.

GitHub Pages sirve la versión de lectura: lecciones, animaciones, controles
interactivos que no requieren Python y progreso local. Las mediciones con Qiskit
y la corrección de código necesitan el servidor local descrito arriba; las
cuentas no están disponibles en esta publicación. El portafolio se llena cuando
puedes ejecutar y superar las misiones con ese servidor.

## Documentación

- [Misiones, mapa y portafolio](docs/juego.md).
- [Cómo escribir ejercicios](docs/exercises.md).
- [Arquitectura](docs/architecture.md).

QuantumShot utiliza el motor de
[qiskit-guides](https://github.com/PedroRojasF/qiskit-guides-compartido).
