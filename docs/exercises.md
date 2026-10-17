# Ejercicios de código

Un ejercicio es código que el alumno escribe y un corrector comprueba. El
corrector, `qgcheck`, corre en el equipo y no necesita red.

## Un ejercicio en disco

Cada ejercicio es una carpeta `exercises/<lección>/<ejercicio>/`. El nombre de
la carpeta de la lección es el `id` de la lección.

| Archivo       | Contenido                                         | Llega a `site/`                        |
| ------------- | ------------------------------------------------- | -------------------------------------- |
| `starter.py`  | El código que el alumno ve al abrir el ejercicio. | Sí                                     |
| `solution.py` | La referencia. Debe pasar todos los casos.        | No                                     |
| `check.py`    | Los casos. Cada función `test_*` es un caso.      | Solo los nombres de los casos visibles |

## Declararlo en la lección

`Exercise()` de [`lib.py`](../lessons_src/lib.py) crea el bloque. Va en la
escena de un paso, junto a la tarjeta `Mission`, y se revela con una acción
`show` como cualquier bloque oculto:

```python
Exercise("p1-quickstart/ghz",
         "Escribe `ghz(n)`: un circuito de `n` qubits, medido con `measure_all()`.",
         level=3, needs="qiskit", id="e3", hidden=True,
         hints=["Empieza con una Hadamard en el qubit 0."])
```

| Campo   | Significado                                                                              |
| ------- | ---------------------------------------------------------------------------------------- |
| `level` | 1 reproducir, 2 modificar, 3 crear.                                                      |
| `needs` | `"qiskit"` si el código corre solo con Qiskit, `"aer"` si también necesita `qiskit-aer`. |
| `hints` | Pistas en orden, de la más vaga a la más concreta.                                       |

[`build.py`](../lessons_src/build.py) completa el bloque con `starter` y con
`cases`, la lista de nombres de los casos visibles, y lo escribe en
`lesson.json`. No publica `solution.py` ni los casos ocultos. Falla si el
ejercicio no está en la carpeta de su lección, si falta un archivo, si ningún
caso es visible, si dos bloques usan el mismo ejercicio o si una carpeta de
`exercises/` no aparece en ninguna lección.

## Escribir `check.py`

```python
from qgcheck import counts, learner, visible


@visible("n = 2, 3 y 4")
def test_small():
    for n in (2, 3, 4):
        got = sorted(counts(learner.ghz(n)))
        assert got == ["0" * n, "1" * n], f"Con n = {n} salen {got}."


def test_larger():          # sin @visible: el caso es oculto
    for n in (5, 7):
        got = sorted(counts(learner.ghz(n)))
        assert got == ["0" * n, "1" * n], f"Con n = {n} salen {got}."
```

- El mensaje del `assert` es el texto de error que ve el alumno. Un caso oculto
  se muestra como `caso oculto 1`, `caso oculto 2`… con su mensaje. Qué debe
  decir lo fijan las [reglas de contenido](#reglas-de-contenido).
- `@hint(n)` enlaza un caso, visible u oculto, con la pista `n` de `hints` (la
  primera es la 1). Si el caso falla, el alumno ve esa pista junto a él.
  `tools/exercises.py` rechaza un `n` mayor que el número de pistas del
  ejercicio.
- `learner.<nombre>` devuelve lo que el código del alumno definió. Si no lo
  definió, el caso falla con «Falta definir `<nombre>` en tu código.». Se lee
  dentro del caso, no al importar `check.py`: `build.py` importa el archivo para
  leer los casos y `learner` aún no tiene el código de ningún alumno.
- Cualquier excepción distinta de `AssertionError` en un caso falla con «Tu
  código lanzó `<Tipo>`: `<mensaje>`».
- Compara estados, no texto de circuitos: `state(circuito).equiv(...)` quita las
  mediciones finales. Para muestreos usa una semilla fija y una tolerancia de al
  menos cuatro desviaciones típicas.
- Un ejercicio de predicción deja `prediccion` sin valor (`None` o `""`) en el
  código inicial. El caso visible compara la apuesta con lo que calcula el
  circuito del alumno, no con una constante, y un caso oculto comprueba que el
  circuito de la lección sigue igual, para que no se pueda acertar cambiando el
  circuito.
- Un ejercicio que dibuja devuelve la figura o los ejes, y el caso lee lo que
  hay detrás (por ejemplo `axes.patches` y las etiquetas del eje), no píxeles.
  El corredor corre con `MPLBACKEND=Agg` y su imagen incluye `matplotlib`.

Los ayudantes de [`qgcheck/__init__.py`](../qgcheck/__init__.py) importan Qiskit
solo cuando se llaman:

| Ayudante                        | Devuelve                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `counts(circuito)`              | Conteos del primer registro clásico con `StatevectorSampler`.                                                 |
| `aer_counts(circuito)`          | Lo mismo con el `SamplerV2` de Aer, para circuitos con control de flujo.                                      |
| `gates(circuito)`               | `Counter` de nombres de operación, con las de dentro de `if_test` y `while_loop`.                             |
| `state(circuito)`               | `Statevector` del circuito sin sus mediciones finales.                                                        |
| `unsupported(circuito, target)` | Lista de las instrucciones que el `Target` no admite donde están, como `['cz en 0-2']`.                       |
| `operator(circuito)`            | `Operator` sobre los qubits virtuales: aplica el layout de un circuito transpilado, aunque sea de 156 qubits. |

## Reglas de contenido

Estas reglas valen para cada ejercicio y para el paso de la lección que lo
contiene.

1. **Una pregunta no adelanta el paso siguiente.** El texto de una pregunta
   (`choice`, `numeric`, `reveal`, `predict`), su `why` y su `after` no dicen
   qué hace el ejercicio que viene después. Si lo dicen, el ejercicio ya está
   resuelto cuando se abre.
2. **Las pistas van en este orden: idea, lugar, forma.** Primero dicen qué idea
   usar, luego en qué parte del código va y por último la forma de la línea, con
   huecos. Ninguna contiene la línea resuelta: eso es `solution.py`.
3. **Un mensaje de caso oculto nombra la entrada que falló y lo que devolvió el
   código del alumno, y nunca el valor esperado.** Por ejemplo,
   `Con n = 7 salen ['0000000', '0000011'].` El alumno reproduce el fallo con
   esa entrada sin leer la respuesta. Un mensaje que enseña el valor esperado
   deja el caso oculto sin efecto.
4. **Un enunciado de nivel 3 nombra cada argumento y la trampa, o sigue un caso
   resuelto.** El alumno que crea código no puede adivinar el orden de los
   argumentos ni lo que el corrector mide. El enunciado dice qué recibe y qué
   devuelve la función, y avisa del error que el caso oculto sí detecta, o
   incluye un ejemplo resuelto con valores.
5. **Un paso con `Exercise` no habla de cuaderno ni de «marca verde».** El
   ejercicio se comprueba con el botón **Comprobar** de la propia página. Esas
   palabras son de `Mission`, que remite a un cuaderno de marimo.

## Corregir código

```python
from qgcheck import grade

grade("p1-quickstart/ghz", codigo, mode="check")
```

[`qgcheck/runner.py`](../qgcheck/runner.py) escribe el código en un directorio
temporal y lo ejecuta con [`qgcheck/worker.py`](../qgcheck/worker.py) en un
proceso aparte. `mode="run"` solo ejecuta el código del alumno; `mode="check"`
además corre los casos. Devuelve:

```json
{
  "passed": false,
  "stdout": "listo\n",
  "error": null,
  "ms": 1180,
  "tests": [
    {
      "name": "n = 2, 3 y 4",
      "visible": true,
      "passed": false,
      "message": "Con n = 3 salen ['000', '011'], y deberían salir solo 000 y 111.",
      "hint": 1
    },
    {
      "name": "caso oculto 1",
      "visible": false,
      "passed": false,
      "message": "Con n = 5 salen ['00000', '00011'].",
      "hint": null
    }
  ]
}
```

`hint` es el número de la pista que nombra el caso con `@hint`, o `null`.

- `error` trae el error del código del alumno, con su línea cuando el error nace
  en una línea, por ejemplo
  `NameError: name 'y' is not defined (línea 2: print(y))`. Un tiempo agotado no
  tiene línea. Con un error, `tests` queda vacío.
- El código no puede pesar más de 20 000 bytes y se detiene a los 10 s. Esos 10
  s cuentan desde que el proceso terminó de importar los módulos de `qiskit`,
  `qiskit_aer`, `qiskit_ibm_runtime`, `numpy`, `scipy`, `matplotlib`,
  `rustworkx` y `sympy` que el código importa (`PRELOAD_ROOTS` en
  `qgcheck/worker.py`); otra biblioteca se importa dentro de los 10 s. El
  arranque tiene su propio tope de 60 s. La salida se corta a 10 000
  caracteres.
- El parámetro `block=("qiskit_aer",)` hace que esos módulos no se puedan
  importar en el proceso del alumno.
- `grade` no aísla al alumno del equipo: no limita memoria, procesos ni red, y
  el código del alumno corre en el mismo intérprete que los casos. Un servicio
  expuesto a internet debe correrlo en un contenedor sin red y con límites:
  [runner.md](runner.md) lo hace.

## Editor en la lección

[`exercise.js`](../site/exercise.js) dibuja cada bloque `Exercise`: el
enunciado, un editor con `starter.py` y los botones **Ejecutar** (solo corre el
código), **Comprobar** (además corre los casos), **Pista** y **Empezar de
nuevo**. Muestra la salida, el error, con su línea marcada en el editor si la
tiene, y un ✓ o ✗ por caso; los casos ocultos aparecen como `caso oculto N`.
Mientras espera al corredor, los botones quedan desactivados; si tarda, lo dice,
y a los 30 s abandona. Cada fallo (timeout, corredor lleno, sin red, respuesta
inválida) tiene su mensaje.

- Tras **Comprobar**, el estado cuenta los casos visibles y los ocultos por
  separado: `Pasan 2 de 2 visibles · 0 de 2 ocultos.` Un ejercicio sin casos
  ocultos solo cuenta los visibles.
- Si el código tiene un error, `tests` viene vacío. El panel muestra el error
  (con su línea, si la tiene) y «No se pudo probar tu código», y no lista ningún
  caso.
- Un caso que falla y nombra una pista con `@hint` muestra esa pista bajo su
  mensaje. No cuenta como pista pedida con el botón **Pista**.
- El editor es CodeMirror 6 con resaltado de Python, con los colores del tema de
  la página ([design.md](design.md)). Lo carga `exercise.js` solo en las
  lecciones que tienen ejercicio.
- **Pista** muestra una pista de `hints` por pulsación. No hay botón para ver la
  solución: `solution.py` no sale de `exercises/`.
- Ctrl+Intro (⌘+Intro) ejecuta, Ctrl+Mayús+Intro comprueba, Tab sangra y Esc
  seguido de Tab sale del editor. Las teclas de la lección (espacio, flechas,
  `c`) no actúan mientras se escribe.
- Un paso con ejercicio no se escala como el resto del escenario: ocupa la
  pantalla y se desplaza, para que el editor se pueda usar en el móvil. No pasa
  solo al paso siguiente al terminar la narración; el botón **Continuar** lo
  hace.
- El código, el número de pistas y de comprobaciones y si quedó resuelto se
  guardan en `localStorage`, bajo `qiskit:exercise:<ejercicio>`.

### Dónde corre el código

El editor envía `POST /run` con `{"exercise", "code", "mode"}` y recibe el
resultado de `grade()`. La ruta es siempre `/run`, la del mismo origen que la
página. El corredor de [runner.md](runner.md) no responde las peticiones
`OPTIONS` ni envía cabeceras CORS, y su cookie de sesión es `SameSite=Strict`:
la página y el corredor deben tener el mismo origen. En producción los sirve un
solo Worker; ver [runner.md](runner.md#cloudflare-containers).

Si el corredor responde 403 con `reason` `turnstile_missing`, la página carga el
widget de Cloudflare Turnstile con la clave del sitio que trae esa respuesta, y
repite la petición con el token en la cabecera `X-Turnstile-Token`. El widget
solo se ve si Cloudflare necesita que el lector haga algo. Con la sesión abierta
no se vuelve a pedir. Si el widget no carga, el panel lo dice y se puede
reintentar.

En tu equipo, [`tools/serve.py`](../tools/serve.py) responde `POST /run` sin
Turnstile:

```sh
uv run python tools/serve.py [puerto]
```

Sirve `site/` en `127.0.0.1` (puerto 8810 por defecto) y rechaza un `POST` que
no sea `application/json` o cuyo `Host` no sea `localhost` o `127.0.0.1`, para
que otra web abierta en tu navegador no ejecute código en tu equipo.

### Reconstruir el editor

`site/editor.js` es el resultado de empaquetar [`editor/`](../editor) con
esbuild; se versiona porque `site/` es estático. Tras cambiar `editor/src/`:

```sh
cd editor && bun install && bun run build
```

## Comprobar los ejercicios

```sh
uv run python lessons_src/build.py
uv run python tools/exercises.py [lección/ejercicio ...]
uv run pytest tests/exercises_test.py
uv run --group tools python tests/exercise_ui_test.py
```

[`tools/exercises.py`](../tools/exercises.py) lee de
`site/lessons/*/lesson.json` qué ejercicios existen, su `needs` y sus `hints`,
por eso va después de `build.py`. Por cada ejercicio comprueba que:

1. `solution.py` pasa todos los casos.
2. `starter.py` se ejecuta sin error y falla algún caso.
3. `needs` es verdadero: con `"qiskit"`, `solution.py` pasa sin `qiskit_aer`;
   con `"aer"`, no pasa sin él.
4. Cada `@hint(n)` nombra una pista que el ejercicio tiene en `hints`.

[`tests/exercises_test.py`](../tests/exercises_test.py) corre cada ejercicio con
su solución y con una solución equivocada que debe fallar con un mensaje útil, y
con los programas equivocados de `tests/mutants/<ejercicio>/` (los que hacen
fallar cada caso oculto; son programas completos, sin depender del texto de
`solution.py`), y prueba el corrector, lo que publica `build.py`, las
comprobaciones y `serve.py`.
[`tests/exercise_ui_test.py`](../tests/exercise_ui_test.py) abre las lecciones
en el navegador contra `serve.py`: escribe código equivocado y ve fallar un
caso, lo corrige y lo ve pasar, recarga y comprueba que el progreso sigue.
También escribe un error de sintaxis y un `ghz` que solo falla casos ocultos, y
comprueba lo que muestra el panel. Lo repite en un móvil, y prueba el teclado,
las pistas, el timeout, los errores y la comprobación de Turnstile, con un
widget de prueba. `mise run test` ejecuta los tres.
