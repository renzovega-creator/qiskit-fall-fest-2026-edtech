import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.3 · El orden de los bits")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from qiskit.primitives import StatevectorSampler

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 2.3 · El orden de los bits: práctica

    Tres misiones con la convención *little-endian* de Qiskit: el qubit 0 es el bit menos
    significativo y va a la **derecha** de la cadena.
    """)
    return QuantumCircuit, StatevectorSampler, Statevector, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: de qubits a cadena

    Este circuito pone una X en los qubits 0 y 2. Antes de ejecutar, escribe en `prediccion`
    la cadena de bits que Qiskit devolverá (por ejemplo `"011"`).
    """)
    return


@app.cell
def _(QuantumCircuit, StatevectorSampler):
    circuito = QuantumCircuit(3)
    circuito.x([0, 2])
    circuito.measure_all()

    prediccion = ""   # ✏️ tu apuesta, entre comillas

    medido = StatevectorSampler(seed=7).run([circuito], shots=128).result()[0].data.meas.get_counts()
    print("Qiskit devuelve:", medido)
    return medido, prediccion


@app.cell(hide_code=True)
def _(medido, prediccion, veredicto):
    veredicto(set(medido) == {prediccion},
              f"Acertaste: `{prediccion}`. Los bits 0 y 2 valen 1, y el bit 0 va a la derecha.",
              f"Tu apuesta {prediccion!r} no coincide con {sorted(medido)}. Escribe el bit del qubit 2 primero y el del qubit 0 al final.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: prepara $|q_2q_1q_0\\rangle = |011\\rangle$

    El circuito pone la X en el qubit equivocado. Cámbialo para que el estado sea `011`,
    es decir, $q_0 = 1$, $q_1 = 1$ y $q_2 = 0$. La comprobación mira el vector de estado:
    la amplitud del índice 3 debe ser 1.
    """)
    return


@app.cell
def _(QuantumCircuit):
    preparado = QuantumCircuit(3)
    preparado.x(2)   # ✏️ ¿en qué qubits va la X?
    preparado.draw("mpl")
    return (preparado,)


@app.cell(hide_code=True)
def _(Statevector, preparado, veredicto):
    _probs = Statevector(preparado).probabilities_dict()
    veredicto(_probs == {"011": 1.0},
              "Estado `011`: el índice 3 del vector de estado, porque $3 = 011_2$.",
              f"Ahora el estado es {list(_probs)[0]!r}. Busca `011`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: `preparar(k, n)`

    Escribe una función `preparar(k, n)` que devuelva un circuito de `n` qubits (sin mediciones)
    cuyo vector de estado sea el estado de la base con **índice** `k`. Por ejemplo,
    `preparar(5, 4)` debe dejar toda la amplitud en el índice 5, que es $0101_2$.
    Usa las potencias de 2: el qubit $j$ lleva una X si el bit $j$ de `k` vale 1.
    """)
    return


@app.cell
def _(QuantumCircuit):
    def preparar(k, n):
        qc = QuantumCircuit(n)
        # ✏️ añade las X que correspondan a los bits de k
        return qc
    return (preparar,)


@app.cell(hide_code=True)
def _(Statevector, np, preparar, veredicto):
    _n = 4
    _ok = all(np.isclose(abs(Statevector(preparar(_k, _n)).data[_k]), 1) for _k in range(2**_n))
    veredicto(_ok,
              "`preparar(k, 4)` funciona para los 16 valores de k.",
              "Para algún k entre 0 y 15 la amplitud no está en el índice k. Prueba `preparar(5, 4)` a mano.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** `qc.draw(reverse_bits=True)` cambia el dibujo, pero no el circuito.
    ¿Por qué ayuda a veces dibujarlo así cuando lees cadenas de bits?
    """)
    return


if __name__ == "__main__":
    app.run()
