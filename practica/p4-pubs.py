import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="4.2 · PUBs y broadcasting")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.primitives import StatevectorEstimator, StatevectorSampler

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""

    Tres misiones sobre la forma de las entradas y de los resultados. Una sola
    llamada a `run` hace un barrido entero: busca el ✅ en cada misión.
    """)
    return Parameter, QuantumCircuit, SparsePauliOp, StatevectorEstimator, StatevectorSampler, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: dos formas de combinar

    El mismo circuito de la lección, con dos PUBs. Antes de ejecutar, predice la forma
    de `evs` en cada caso.
    """)
    return


@app.cell
def _(Parameter, QuantumCircuit, SparsePauliOp, StatevectorEstimator, np):
    circ = QuantumCircuit(3)
    circ.ry(Parameter("a"), 0)
    circ.cx(0, 1)
    circ.cx(1, 2)
    estimator = StatevectorEstimator()

    obs_uno_a_uno = [SparsePauliOp(p) for p in ["III", "XXX", "YYY", "ZZZ", "XYZ"]]
    uno_a_uno = estimator.run([(circ, obs_uno_a_uno, np.linspace(0, 1, 5)[:, None])]).result()[0].data.evs

    obs_columna = [[SparsePauliOp(p)] for p in ["III", "XXX", "YYY", "ZZZ"]]
    producto = estimator.run([(circ, obs_columna, np.linspace(0, 1, 6)[None, :, None])]).result()[0].data.evs
    print(uno_a_uno.shape, producto.shape)
    return circ, estimator, producto, uno_a_uno


@app.cell(hide_code=True)
def _(producto, uno_a_uno, veredicto):
    veredicto(uno_a_uno.shape == (5,) and producto.shape == (4, 6),
              "(5,) con (5,) se empareja uno a uno; (4, 1) con (1, 6) da el producto exterior (4, 6).",
              "Las formas deberían ser (5,) y (4, 6).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: dale otra forma a los observables

    Hay 10 valores del parámetro `a` y tres observables. Ahora `observables` es un solo
    `SparsePauliOp`, que tiene forma `()`, y `evs` sale con forma `(10,)`. Cambia **solo**
    cómo se arma `observables` para que `evs` tenga forma `(3, 10)`: una fila por
    observable y una columna por valor.
    """)
    return


@app.cell
def _(SparsePauliOp, circ, estimator, np):
    valores = np.linspace(0, np.pi, 10)[:, None]

    # ✏️ lista de listas de un elemento, una por cada Pauli de ["ZZZ", "XXX", "YYY"]
    observables = SparsePauliOp.from_list([("ZZZ", 1), ("XXX", 1), ("YYY", 1)])

    evs_barrido = estimator.run([(circ, observables, valores)]).result()[0].data.evs
    print(evs_barrido.shape)
    return (evs_barrido,)


@app.cell(hide_code=True)
def _(evs_barrido, veredicto):
    veredicto(evs_barrido.shape == (3, 10),
              "Forma (3, 10): `(3, 1)` contra `(10,)` hace broadcasting.",
              f"Ahora `evs` tiene forma {evs_barrido.shape}. Busca (3, 10).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: posprocesar un `BitArray` sin diccionarios

    Con un solo PUB de Sampler barres 5 ángulos de $R_y$ sobre un qubit. `data.meas` es un
    `BitArray` de forma `(5,)`: un arreglo de disparos por ángulo. Calcula en `p1` la
    probabilidad de medir `1` para cada ángulo **sin** llamar a `get_counts`: usa
    `expectation_values("Z")`, que devuelve $\\langle Z\\rangle$ para cada ángulo, y recuerda que
    $P(1) = (1-\\langle Z\\rangle)/2$.
    """)
    return


@app.cell
def _(Parameter, QuantumCircuit, StatevectorSampler, np):
    angulos = np.linspace(0, np.pi, 5)
    barrido = QuantumCircuit(1)
    barrido.ry(Parameter("t"), 0)
    barrido.measure_all()

    datos = StatevectorSampler(seed=2).run([(barrido, angulos[:, None])], shots=4000).result()[0].data
    p1 = np.zeros(5)   # ✏️ probabilidad de medir 1 por ángulo, a partir de datos.meas
    print(datos.meas.array.shape, p1.round(3))
    return angulos, p1


@app.cell(hide_code=True)
def _(angulos, np, p1, veredicto):
    veredicto(np.shape(p1) == (5,) and np.allclose(p1, np.sin(angulos / 2) ** 2, atol=0.03),
              "`p1` sigue a $\\sin^2(\\theta/2)$ en los cinco ángulos, calculada con operaciones sobre el arreglo.",
              "`p1` no coincide con sin²(θ/2). Recuerda P(1) = (1 − ⟨Z⟩) / 2.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** con un barrido de 1000 ángulos, ¿qué forma tendría `datos.meas.array`?
    ¿Qué ventaja tiene un solo PUB con 1000 valores frente a 1000 PUBs de un valor cada uno?
    """)
    return


if __name__ == "__main__":
    app.run()
