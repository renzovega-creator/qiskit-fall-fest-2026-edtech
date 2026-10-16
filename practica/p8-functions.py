import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="8.3 · Qiskit Functions")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import SparsePauliOp

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    # Qiskit Functions necesita un plan de pago. Este catálogo local imita la forma de
    # `QiskitFunctionsCatalog` (list, load, run, job.status…) y calcula con un
    # estimador exacto. Los estados avanzan en cada llamada a `status()`.
    class Trabajo:
        _ESTADOS = ["QUEUED", "INITIALIZING", "RUNNING", "DONE"]

        def __init__(self, job_id, pubs, backend_name):
            self.job_id, self._pubs, self._tick = job_id, pubs, 0
            self.backend, self._error, self._valores = backend_name, None, None
            self._logs = [f"iteration 0: backend {backend_name}"]
            try:
                self._valores = [r.data.evs.tolist() for r in StatevectorEstimator().run(pubs).result()]
                self._logs.append("iteration 1: valores esperados calculados")
            except Exception as e:
                self._error = f"{type(e).__name__}: {e}"
                self._logs.append("error: " + self._error)

        def status(self):
            self._tick = min(self._tick + 1, 4)
            if self._tick == 4:
                return "ERROR" if self._error else "DONE"
            return self._ESTADOS[self._tick - 1]

        def result(self):
            if self._error:
                raise RuntimeError(self._error)
            return self._valores

        def error_message(self):
            return self._error

        def logs(self):
            return "\n".join(self._logs)

        def filtered_logs(self, include):
            return "\n".join(l for l in self._logs if include in l)

        def runtime_jobs(self):
            return [f"runtime-{self.job_id}-0"]

    class Funcion:
        def __init__(self, nombre, tipo, backends):
            self.nombre, self.tipo, self.backends, self._n = nombre, tipo, backends, 0

        def run(self, pubs, backend_name):
            if backend_name not in self.backends:
                raise ValueError(f"tu instancia no tiene acceso al backend {backend_name!r}")
            self._n += 1
            return Trabajo(f"{self.nombre.split('/')[1]}-{self._n}", pubs, backend_name)

        def __repr__(self):
            return f"QiskitFunction({self.nombre})"

    class CatalogoLocal:
        def __init__(self):
            self._f = {"ibm/circuit-function": Funcion("ibm/circuit-function", "circuito", {"fake_fez", "fake_brisbane"}),
                       "qunova/hivqe-chemistry": Funcion("qunova/hivqe-chemistry", "aplicación", {"fake_fez"})}

        def list(self):
            return list(self._f.values())

        def load(self, nombre):
            return self._f[nombre]

    def bell():
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        return qc

    mo.md("""
    # 8.3 · Qiskit Functions: práctica

    Tres misiones sobre cargar, ejecutar y seguir un trabajo de una función. Qiskit Functions
    pide un plan de pago; aquí usas un catálogo local con la misma forma y un estimador
    exacto. Busca el ✅ en cada misión.
    """)
    return CatalogoLocal, QuantumCircuit, SparsePauliOp, bell, mo, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: cargar y ejecutar una función

    Lista el catálogo, carga una función **de circuito** y ejecútala con un PUB:
    el circuito de Bell y el observable $ZZ$. Después consulta el estado del
    trabajo cuatro veces y mira cómo cambia.
    """)
    return


@app.cell
def _(CatalogoLocal, SparsePauliOp, bell):
    catalogo = CatalogoLocal()
    print(catalogo.list())

    funcion = catalogo.load("ibm/circuit-function")
    job = funcion.run(pubs=[(bell(), [SparsePauliOp("ZZ")])], backend_name="fake_fez")
    estados = [job.status() for _ in range(4)]
    print(estados)
    job.result()
    return catalogo, estados, funcion, job


@app.cell(hide_code=True)
def _(estados, funcion, job, veredicto):
    veredicto(funcion.tipo == "circuito" and estados == ["QUEUED", "INITIALIZING", "RUNNING", "DONE"]
              and abs(job.result()[0][0] - 1.0) < 1e-9,
              "Un trabajo pasa por la cola, se inicializa y se ejecuta antes de terminar. El valor de $ZZ$ en Bell es 1.",
              "Revisa que cargas `ibm/circuit-function` y que ejecutas el PUB de Bell con $ZZ$.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un backend al que no tienes acceso

    `run` comprueba el acceso al backend **antes** de enviar el trabajo y falla enseguida.
    La celda de abajo nombra un backend que tu instancia no tiene. Mira el error y cámbialo
    por uno que sí tenga la función (`funcion.backends` los lista).
    """)
    return


@app.cell
def _(SparsePauliOp, bell, funcion):
    BACKEND = "ibm_inexistente"   # ✏️

    try:
        job2 = funcion.run(pubs=[(bell(), [SparsePauliOp("XX")])], backend_name=BACKEND)
        error2 = None
    except ValueError as e:
        job2, error2 = None, str(e)
    error2
    return error2, job2


@app.cell(hide_code=True)
def _(error2, job2, veredicto):
    veredicto(job2 is not None and error2 is None,
              "El trabajo se aceptó: el backend existe y tu instancia tiene acceso.",
              f"`run` falló enseguida: {error2}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: un resumen de trabajo

    Escribe `resumen(job)`. Consulta `job.status()` hasta que el estado sea `DONE` o `ERROR`
    y devuelve un diccionario con:

    - `estados`: los estados distintos que viste, en orden;
    - `runtime_jobs`: lo que devuelve `job.runtime_jobs()`;
    - `iteraciones`: las líneas de `job.filtered_logs(include="iteration")`;
    - `error`: `job.error_message()` (es `None` si terminó bien).
    """)
    return


@app.cell
def _():
    def resumen(job):
        # ✏️ consulta el estado en un bucle y rellena el diccionario
        return {"estados": [], "runtime_jobs": [], "iteraciones": "", "error": None}
    return (resumen,)


@app.cell(hide_code=True)
def _(QuantumCircuit, SparsePauliOp, bell, funcion, resumen, veredicto):
    _bueno = resumen(funcion.run(pubs=[(bell(), [SparsePauliOp("ZZ")])], backend_name="fake_fez"))
    _malo = resumen(funcion.run(pubs=[(QuantumCircuit(3), [SparsePauliOp("ZZ")])], backend_name="fake_fez"))
    _ok = (_bueno["estados"] == ["QUEUED", "INITIALIZING", "RUNNING", "DONE"] and len(_bueno["runtime_jobs"]) == 1
           and "iteration 1" in _bueno["iteraciones"] and _bueno["error"] is None
           and _malo["estados"][-1] == "ERROR" and _malo["error"])
    veredicto(bool(_ok),
              "Tu resumen distingue un trabajo terminado de uno con error y recoge su mensaje.",
              "Para el trabajo bueno espero estados QUEUED → INITIALIZING → RUNNING → DONE, un trabajo de Runtime y "
              "las líneas «iteration»; para uno con observable de otro tamaño, el estado ERROR y su mensaje.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿por qué conviene que `run` falle enseguida, en vez de dejar que el trabajo
    falle en la cola? ¿Qué hace un trabajo en `ERROR` con la capacidad que gastó?
    """)
    return


if __name__ == "__main__":
    app.run()
