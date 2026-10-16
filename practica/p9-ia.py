import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="9.4 · IA para programar con Qiskit")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit.quantum_info import Statevector

    def veredicto(ok, si, no):
        """Muestra ✅ o ❌ según la comprobación."""
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 9.4 · IA para programar con Qiskit: práctica

    Qiskit HumanEval mide un modelo así: le da una tarea de programación, ejecuta el
    código que escribe y lo pasa por pruebas unitarias. Aquí construyes un minibanco de
    pruebas con tres tareas y tres «modelos» que son respuestas fijas, sin red ni cuenta.
    Lo que aprendes sirve para revisar el código de cualquier asistente.
    """)
    return Statevector, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: puntuar a tres modelos

    `pasa(codigo, prueba)` ejecuta el código de un modelo y llama a la prueba con lo que
    definió. Cualquier excepción cuenta como fallo. Una tarea es un par: su enunciado y su
    prueba. Ejecuta la celda y mira qué tarea falla en cada modelo, y por qué.
    """)
    return


@app.cell
def _(Statevector, np):
    def pasa(codigo, prueba):
        """True si el código se ejecuta y la prueba da True. Cualquier excepción es un fallo."""
        espacio = {}
        try:
            exec(codigo, espacio)
            return bool(prueba(espacio))
        except Exception:
            return False

    _bell = Statevector(np.array([1, 0, 0, 1]) / np.sqrt(2))

    def _ghz(n):
        v = np.zeros(2**n)
        v[0] = v[-1] = 1 / np.sqrt(2)
        return Statevector(v)

    pruebas = {
        "bell": lambda ns: Statevector(ns["bell"]()).equiv(_bell),
        "ghz": lambda ns: all(Statevector(ns["ghz"](n)).equiv(_ghz(n)) for n in (3, 4)),
        "conteos": lambda ns: set(ns["conteos"](ns["bell"]())) == {"00", "11"},
    }

    BELL = '''
from qiskit import QuantumCircuit

def bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc
'''
    GHZ = '''
from qiskit import QuantumCircuit

def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    return qc
'''
    CONTEOS = '''
from qiskit.primitives import StatevectorSampler

def conteos(qc):
    qc = qc.copy()
    qc.measure_all()
    return StatevectorSampler().run([qc], shots=1000).result()[0].data.meas.get_counts()
'''
    candidatos = {
        "A": {"bell": BELL, "ghz": GHZ, "conteos": BELL + CONTEOS},
        "B": {"bell": BELL.replace("qc.cx(0, 1)", "qc.cx(1, 0)"), "ghz": GHZ, "conteos": BELL + CONTEOS},
        "C": {"bell": BELL, "ghz": GHZ.replace("qc.cx(k, k + 1)", "qc.h(k)"),
              "conteos": BELL + CONTEOS.replace("from qiskit.primitives import StatevectorSampler",
                                                  "from qiskit import execute, Aer")},
    }
    resultados = {modelo: {t: pasa(c[t], pruebas[t]) for t in pruebas} for modelo, c in candidatos.items()}
    puntuacion = {modelo: sum(r.values()) / len(r) for modelo, r in resultados.items()}
    {m: {t: "✅" if ok else "❌" for t, ok in r.items()} | {"pass@1": round(puntuacion[m], 2)} for m, r in resultados.items()}
    return BELL, candidatos, pasa, pruebas, puntuacion, resultados


@app.cell(hide_code=True)
def _(puntuacion, resultados, veredicto):
    veredicto(resultados["B"]["bell"] is False and resultados["C"]["conteos"] is False
              and [round(puntuacion[m], 2) for m in "ABC"] == [1.0, 0.67, 0.33],
              "A 1,00 · B 0,67 · C 0,33. B se equivoca de control en la CNOT; C importa `execute` y `Aer`, que Qiskit 1.0 eliminó.",
              f"Las puntuaciones son {puntuacion}; deberían ser 1,00, 0,67 y 0,33.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: corrige el código del modelo B

    El modelo B escribió una CNOT al revés. Corrige `bell_corregido` para que pase la
    prueba, igual que lo harías con el código de un asistente. Es la parte del trabajo que
    una prueba unitaria no hace por ti: leer el error y entender por qué falla.
    """)
    return


@app.cell
def _():
    bell_corregido = '''
from qiskit import QuantumCircuit

def bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(1, 0)   # ✏️ corrige el error del modelo B
    return qc
'''
    return (bell_corregido,)


@app.cell(hide_code=True)
def _(bell_corregido, pasa, pruebas, veredicto):
    veredicto(pasa(bell_corregido, pruebas["bell"]),
              "Ahora `bell()` pasa la prueba: el modelo B pasaría de 0,67 a 1,00.",
              "`bell()` todavía no prepara $(|00\\rangle+|11\\rangle)/\\sqrt2$. Piensa qué qubit debe ser el control.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: una prueba que no se deja engañar

    Nueva tarea: `anti_bell()` debe preparar $(|01\\rangle+|10\\rangle)/\\sqrt2$. Hay tres
    respuestas posibles: una correcta y dos con errores típicos (olvidar la X, y dar un
    signo menos). Escribe `prueba_anti_bell(ns)` para que **acepte la correcta y rechace
    las otras dos**. Pista: `Statevector.equiv` distingue estados con distinta fase relativa.
    """)
    return


@app.cell
def _(Statevector, np):
    CORRECTA = '''
from qiskit import QuantumCircuit

def anti_bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.x(0)
    return qc
'''
    SIN_X = CORRECTA.replace("    qc.x(0)\n", "")
    CON_SIGNO = CORRECTA.replace("    qc.x(0)\n", "    qc.x(0)\n    qc.z(0)\n")

    def prueba_anti_bell(ns):
        # ✏️ compara Statevector(ns["anti_bell"]()) con el estado esperado
        return True
    return CON_SIGNO, CORRECTA, SIN_X, prueba_anti_bell


@app.cell(hide_code=True)
def _(CON_SIGNO, CORRECTA, SIN_X, pasa, prueba_anti_bell, veredicto):
    _acepta = pasa(CORRECTA, prueba_anti_bell)
    _rechaza = [not pasa(SIN_X, prueba_anti_bell), not pasa(CON_SIGNO, prueba_anti_bell)]
    veredicto(_acepta and all(_rechaza),
              "Tu prueba acepta la respuesta correcta y rechaza las dos con error.",
              f"Acepta la correcta: {_acepta}. Rechaza «sin X»: {_rechaza[0]}. Rechaza «con signo»: {_rechaza[1]}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** una prueba que solo mira los conteos ¿habría detectado el error del
    signo? ¿Qué te dice eso de confiar en el código de un asistente porque «imprime algo
    razonable»?
    """)
    return


if __name__ == "__main__":
    app.run()
