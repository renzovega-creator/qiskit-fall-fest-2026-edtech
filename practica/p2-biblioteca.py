import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.4 · La biblioteca de circuitos")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.circuit.library import n_local, FullAdderGate
    from qiskit.primitives import StatevectorSampler

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 2.4 · La biblioteca de circuitos: práctica

    Tres misiones con piezas ya hechas: contar los parámetros de un circuito N-local,
    darle la forma que quieres y usar el sumador para calcular una suma nueva.
    """)
    return (ClassicalRegister, FullAdderGate, QuantumCircuit, QuantumRegister, StatevectorSampler, mo,
            n_local, veredicto)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: contar parámetros

    `n_local(3, "rx", "cz")` alterna capas de rotaciones RX con capas de CZ. Antes de
    ejecutar, escribe en `prediccion` cuántos parámetros tiene.
    """)
    return


@app.cell
def _(n_local):
    ansatz = n_local(3, "rx", "cz")

    prediccion = None   # ✏️ tu apuesta: ¿cuántos parámetros?

    print("parámetros:", ansatz.num_parameters)
    ansatz.decompose().draw("mpl")
    return ansatz, prediccion


@app.cell(hide_code=True)
def _(ansatz, prediccion, veredicto):
    veredicto(prediccion == ansatz.num_parameters,
              f"Acertaste: {ansatz.num_parameters}. Por defecto son 3 repeticiones, o sea 4 capas de rotaciones de 3 ángulos.",
              f"Tu apuesta ({prediccion}) no coincide con {ansatz.num_parameters}. Cuenta las capas de rotaciones, que son una más que las repeticiones.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: más barato

    Este circuito de 4 qubits tiene 16 parámetros y 18 puertas de dos qubits. Cámbialo para
    que tenga **8 parámetros** y **solo 3 puertas de dos qubits**.
    Pista: mira los argumentos `reps` y `entanglement` (`"linear"` conecta solo vecinos).
    """)
    return


@app.cell
def _(n_local):
    barato = n_local(4, "ry", "cz")   # ✏️ añade los argumentos que faltan
    print(barato.num_parameters, "parámetros")
    return (barato,)


@app.cell(hide_code=True)
def _(barato, veredicto):
    _dos = barato.decompose(reps=3).num_nonlocal_gates()
    veredicto(barato.num_parameters == 8 and _dos == 3,
              "8 parámetros y 3 puertas de dos qubits.",
              f"Ahora tiene {barato.num_parameters} parámetros y {_dos} puertas de dos qubits. Busca 8 y 3.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: sumar 5 + 6

    El sumador de la lección trabajaba con 3 bits. Escribe `sumar(x, y)` con registros de
    **4 bits**: prepara `x` en `a` e `y` en `b` con `initialize`, añade `FullAdderGate(4)` y
    mide el registro `b`, que guarda el resultado. Los qubits del sumador van en el orden
    `cin`, `a`, `b`, `cout`.
    """)
    return


@app.cell
def _(ClassicalRegister, FullAdderGate, QuantumCircuit, QuantumRegister):
    def sumar(x, y):
        a = QuantumRegister(4, "a")
        b = QuantumRegister(4, "b")
        qregs = [QuantumRegister(1, "cin"), a, b, QuantumRegister(1, "cout")]
        res = ClassicalRegister(4, "res")
        qc = QuantumCircuit(*qregs, res)
        # ✏️ initialize(x) en a, initialize(y) en b, el sumador sobre todos los qubits y measure de b en res
        return qc
    return (sumar,)


@app.cell(hide_code=True)
def _(StatevectorSampler, sumar, veredicto):
    def _suma(x, y):
        return StatevectorSampler(seed=5).run([sumar(x, y)], shots=64).result()[0].data.res.get_int_counts()

    _casos = [(5, 6), (1, 2), (7, 8), (0, 9)]
    _ok = all(_suma(_x, _y) == {_x + _y: 64} for _x, _y in _casos)
    veredicto(_ok,
              "`sumar` da 5 + 6 = 11, 1 + 2 = 3, 7 + 8 = 15 y 0 + 9 = 9.",
              "Alguna suma no sale. Cada resultado debe ser un solo entero: x + y.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** `sumar(9, 9)` no cabe en 4 bits. ¿Qué qubit del sumador guardaría el
    bit que sobra, y qué tendrías que medir además de `b`?
    """)
    return


if __name__ == "__main__":
    app.run()
