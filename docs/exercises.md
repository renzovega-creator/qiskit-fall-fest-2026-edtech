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
        assert sorted(counts(learner.ghz(n))) == ["0" * n, "1" * n], "Con otros tamaños de n falla."
```

- El mensaje del `assert` es el texto de error que ve el alumno. Un caso oculto
  se muestra como `caso oculto 1`, `caso oculto 2`… con su mensaje, así que ese
  mensaje no debe nombrar los datos del caso.
- `learner.<nombre>` devuelve lo que el código del alumno definió. Si no lo
  definió, el caso falla con «Falta definir `<nombre>` en tu código.». Se lee
  dentro del caso, no al importar `check.py`: `build.py` importa el archivo para
  leer los casos y `learner` aún no tiene el código de ningún alumno.
- Cualquier excepción distinta de `AssertionError` en un caso falla con «Tu
  código lanzó `<Tipo>`: `<mensaje>`».
- Compara estados, no texto de circuitos: `state(circuito).equiv(...)` quita las
  mediciones finales. Para muestreos usa una semilla fija y una tolerancia de al
  menos cuatro desviaciones típicas.

Los ayudantes de [`qgcheck/__init__.py`](../qgcheck/__init__.py) importan Qiskit
solo cuando se llaman:

| Ayudante               | Devuelve                                                                          |
| ---------------------- | --------------------------------------------------------------------------------- |
| `counts(circuito)`     | Conteos del primer registro clásico con `StatevectorSampler`.                     |
| `aer_counts(circuito)` | Lo mismo con el `SamplerV2` de Aer, para circuitos con control de flujo.          |
| `gates(circuito)`      | `Counter` de nombres de operación, con las de dentro de `if_test` y `while_loop`. |
| `state(circuito)`      | `Statevector` del circuito sin sus mediciones finales.                            |

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
      "message": "Con n = 3 salen ['000', '011'], y deberían salir solo 000 y 111."
    },
    {
      "name": "caso oculto 1",
      "visible": false,
      "passed": false,
      "message": "Con otros tamaños de n no salen solo 00…0 y 11…1."
    }
  ]
}
```

- `error` trae el error del código del alumno, con su línea, por ejemplo
  `NameError: name 'y' is not defined (línea 2: print(y))`. Con un error,
  `tests` queda vacío.
- El código no puede pesar más de 20 000 bytes y se detiene a los 10 s. La
  salida se corta a 10 000 caracteres.
- El parámetro `block=("qiskit_aer",)` hace que esos módulos no se puedan
  importar en el proceso del alumno.
- `grade` no aísla al alumno del equipo: no limita memoria, procesos ni red, y
  el código del alumno corre en el mismo intérprete que los casos. Un servicio
  expuesto a internet debe correrlo en un contenedor sin red y con límites:
  [runner.md](runner.md) lo hace.

## Editor en la lección

`B.exercise` de [`blocks.js`](../site/blocks.js) dibuja el ejercicio: el
enunciado, un editor con `starter.py` y los botones **Ejecutar** (solo corre el
código), **Comprobar** (además corre los casos), **Empezar de nuevo** y
**Pista** (una más por pulsación). Muestra la salida, el error con su línea y un
✓ o ✗ por caso; los casos ocultos aparecen como `caso oculto N`. El código se
guarda en el navegador, en `localStorage`, bajo `qiskit:code:<ejercicio>`.

El editor envía `POST /run` con `{"exercise", "code", "mode"}` y recibe el
resultado de `grade()`. Lo responde [`tools/serve.py`](../tools/serve.py):

```sh
uv run python tools/serve.py [puerto]
```

Sirve `site/` en `127.0.0.1` (puerto 8810 por defecto) y rechaza un `POST` que
no sea `application/json` o cuyo `Host` no sea `localhost` o `127.0.0.1`, para
que otra web abierta en tu navegador no ejecute código en tu equipo. Con otro
servidor estático, Ejecutar y Comprobar explican cómo abrir el curso con
`serve.py`.

## Comprobar los ejercicios

```sh
uv run python lessons_src/build.py
uv run python tools/exercises.py [lección/ejercicio ...]
uv run pytest tests/exercises_test.py
uv run --group tools python tests/exercise_ui_test.py
```

[`tools/exercises.py`](../tools/exercises.py) lee de
`site/lessons/*/lesson.json` qué ejercicios existen y su `needs`, por eso va
después de `build.py`. Por cada ejercicio comprueba que:

1. `solution.py` pasa todos los casos.
2. `starter.py` se ejecuta sin error y falla algún caso.
3. `needs` es verdadero: con `"qiskit"`, `solution.py` pasa sin `qiskit_aer`;
   con `"aer"`, no pasa sin él.

[`tests/exercises_test.py`](../tests/exercises_test.py) corre cada ejercicio con
su solución y con una solución equivocada que debe fallar con un mensaje útil, y
prueba el corrector, lo que publica `build.py`, las tres comprobaciones y
`serve.py`. [`tests/exercise_ui_test.py`](../tests/exercise_ui_test.py) abre una
lección en el navegador y usa el editor. `mise run test` ejecuta los tres.
