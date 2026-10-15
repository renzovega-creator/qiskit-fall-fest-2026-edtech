import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="8.1 · Qiskit Serverless")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from concurrent.futures import ThreadPoolExecutor

    from qiskit import QuantumCircuit
    from qiskit.circuit.random import random_circuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeFez

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    # Qiskit Serverless corre en la nube y necesita una cuenta. Este cuaderno reproduce en tu
    # equipo las dos reglas de su contrato: las entradas deben ser serializables y la
    # función decorada devuelve una referencia, no el resultado.
    _ESCALARES = (type(None), bool, int, float, str, QuantumCircuit)

    def serializable(valor):
        if isinstance(valor, _ESCALARES):
            return valor
        if isinstance(valor, (list, tuple)):
            return [serializable(v) for v in valor]
        if isinstance(valor, dict):
            return {k: serializable(v) for k, v in valor.items()}
        raise TypeError(f"{type(valor).__name__} no es serializable: pasa su nombre, no el objeto")

    def ejecutar_remoto(programa, **argumentos):
        """Equivale a `programa.run(**argumentos)` y `job.result()`."""
        return programa(serializable(argumentos))

    _EXECUTOR = ThreadPoolExecutor(max_workers=4)

    def distribute_task(target):
        def decorador(f):
            return lambda *a, **k: _EXECUTOR.submit(f, *a, **k)
        return decorador

    def get(refs):
        return [r.result() for r in refs]

    FAKES = {"fake_fez": FakeFez}

    def programa(arguments):
        """El archivo remoto: `get_arguments()` → trabajo → `save_result(...)`."""
        backend = FAKES[arguments["backend_name"]]()
        pm = generate_preset_pass_manager(optimization_level=arguments["optimization_level"],
                                          backend=backend, seed_transpiler=1)
        return {"profundidades": [pm.run(c).depth() for c in arguments["circuits"]]}

    circuitos = [random_circuit(5, 4, measure=False, seed=s) for s in range(4)]

    mo.md("""
    # 8.1 · Qiskit Serverless: práctica

    Tres misiones sobre el contrato de un programa de Serverless. Serverless corre en la
    nube y pide una cuenta; aquí reproduces su contrato en tu equipo, con el backend
    simulado `FakeFez`. Busca el ✅ en cada misión.
    """)
    return (FakeFez, circuitos, distribute_task, ejecutar_remoto, generate_preset_pass_manager,
            get, mo, programa, veredicto)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: ejecutar un programa

    `programa` hace lo que el archivo remoto de la lección: lee los argumentos, transpila
    cada circuito para el backend que se nombra y devuelve un diccionario.
    `ejecutar_remoto` lo llama como lo haría `program.run(...)`. Ejecuta la celda y lee las
    profundidades.
    """)
    return


@app.cell
def _(circuitos, ejecutar_remoto, programa):
    resultado = ejecutar_remoto(programa, circuits=circuitos, backend_name="fake_fez",
                                optimization_level=1)
    resultado
    return (resultado,)


@app.cell(hide_code=True)
def _(circuitos, resultado, veredicto):
    _p = resultado["profundidades"]
    veredicto(len(_p) == len(circuitos) and all(isinstance(d, int) and d > 0 for d in _p),
              f"Una profundidad por circuito: {_p}.",
              "Debería haber una profundidad entera por circuito.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: una entrada que no viaja

    La llamada de abajo falla: Serverless solo acepta entradas serializables, y un objeto
    `backend` no lo es. Cambia **una** entrada para que el programa reciba lo que necesita
    (mira qué clave lee `programa`).
    """)
    return


@app.cell
def _(FakeFez, circuitos):
    argumentos = dict(circuits=circuitos, backend=FakeFez(), optimization_level=3)   # ✏️
    return (argumentos,)


@app.cell(hide_code=True)
def _(argumentos, ejecutar_remoto, mo, programa, veredicto):
    try:
        _salida = ejecutar_remoto(programa, **argumentos)
        _ok, _msg = len(_salida["profundidades"]) == 4, ""
    except Exception as e:
        _ok, _msg = False, f"{type(e).__name__}: {e}"
    veredicto(_ok, "El programa recibió solo entradas serializables y devolvió sus resultados.",
              f"La llamada falla → {_msg}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: paralelizar con `distribute_task`

    Completa `transpilar_profundidad` para que transpile un circuito con `FakeFez` y devuelva su
    profundidad. Después crea la lista `refs` con **una llamada por circuito** (con
    `optimization_level=1`) y reúne los resultados con `get`. Recuerda: cada llamada
    devuelve una referencia, no el valor.

    `distribute_task` y `get` aquí usan hilos de tu equipo; en Serverless cada tarea corre
    en su propio trabajador.
    """)
    return


@app.cell
def _(FakeFez, circuitos, distribute_task, generate_preset_pass_manager, get):
    backend = FakeFez()

    @distribute_task(target={"cpu": 1})
    def transpilar_profundidad(circuito, nivel):
        # ✏️ transpila con generate_preset_pass_manager(..., seed_transpiler=1) y devuelve la profundidad
        return None

    refs = []   # ✏️ una referencia por circuito
    profundidades = get(refs)
    profundidades
    return profundidades, refs


@app.cell(hide_code=True)
def _(ejecutar_remoto, circuitos, profundidades, programa, refs, veredicto):
    _esperado = ejecutar_remoto(programa, circuits=circuitos, backend_name="fake_fez",
                                optimization_level=1)["profundidades"]
    _refs = len(refs) == len(circuitos) and all(hasattr(r, "result") for r in refs)
    veredicto(_refs and profundidades == _esperado,
              "Cuatro tareas en paralelo y `get` reunió el mismo resultado que el programa.",
              "Necesito una referencia por circuito (llama a la función, no uses su valor) y que `get(refs)` "
              f"dé {_esperado}.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** si el trabajo clásico de cada tarea dura segundos pero tu lista tiene
    miles de circuitos, ¿cuántos núcleos pedirías en `target={"cpu": ...}`? ¿Qué pasa
    con las tareas que no caben a la vez?
    """)
    return


if __name__ == "__main__":
    app.run()
