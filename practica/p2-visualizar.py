import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.9 · Visualizar")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from math import pi
    import matplotlib.pyplot as plt
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.primitives import StatevectorEstimator
    from qiskit.visualization import plot_state_paulivec

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 2.9 · Visualizar: práctica

    Tres misiones: leer un estado en su gráfica, personalizar `draw` y graficar valores
    esperados de Estimator con barras.
    """)
    return (QuantumCircuit, SparsePauliOp, Statevector, StatevectorEstimator, mo, np, pi, plot_state_paulivec,
            plt, veredicto)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: leer un estado

    El estado de la lección es una Hadamard y una RX controlada de $\\pi/2$. Antes de ver la
    gráfica, escribe en `prediccion` la probabilidad de medir `00` (un número entre 0 y 1).
    """)
    return


@app.cell
def _(QuantumCircuit, Statevector, pi, plot_state_paulivec):
    estado = QuantumCircuit(2)
    estado.h(0)
    estado.crx(pi / 2, 0, 1)
    psi = Statevector(estado)

    prediccion = None   # ✏️ tu apuesta: P(00)

    print(psi.probabilities_dict())
    plot_state_paulivec(psi)
    return prediccion, psi


@app.cell(hide_code=True)
def _(prediccion, psi, veredicto):
    _p00 = psi.probabilities_dict()["00"]
    veredicto(prediccion is not None and abs(prediccion - _p00) < 0.01,
              f"Acertaste: P(00) = {_p00:.2f}. La H deja $q_0$ en 0 con peso 1/2, y en esa rama la RX controlada no actúa.",
              f"Tu apuesta ({prediccion}) está lejos de P(00). Piensa qué hace la H sobre q0 y qué hace la RX controlada.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: un dibujo a tu medida

    Quieres el circuito en texto con el qubit 0 **abajo** y **sin barreras**. Añade a
    `draw` las dos opciones que lo consiguen.
    """)
    return


@app.cell
def _(QuantumCircuit):
    circuito = QuantumCircuit(3, 3)
    circuito.x(1)
    circuito.h(range(3))
    circuito.cx(0, 1)
    circuito.barrier()
    circuito.measure(range(3), range(3))

    dibujo = circuito.draw("text")   # ✏️ añade las opciones de draw
    print(dibujo)
    return (dibujo,)


@app.cell(hide_code=True)
def _(dibujo, veredicto):
    _texto = str(dibujo)
    _ok = "░" not in _texto and _texto.index("q_2") < _texto.index("q_0")
    veredicto(_ok,
              "Sin barreras y con $q_2$ arriba y $q_0$ abajo.",
              "Todavía se ven las barreras (`░`) o $q_0$ sigue arriba. Mira `reverse_bits` y `plot_barriers`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: barras de valores esperados

    Escribe `valores_esperados(circuito, etiquetas)` que ejecute un `StatevectorEstimator` con
    un observable `SparsePauliOp` por etiqueta (por ejemplo `"ZZ"` o `"XI"`) y devuelva los
    valores esperados como un arreglo 1D. Recuerda: el arreglo de observables tiene forma
    $(k, 1)$ para pedirlos todos en una sola llamada. Después grafícalos con `plt.bar`.
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, StatevectorEstimator, np):
    def valores_esperados(circuito, etiquetas):
        # ✏️ un SparsePauliOp por etiqueta, forma (k, 1), una sola llamada a run y evs.flatten()
        return np.zeros(len(etiquetas))

    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    return bell, valores_esperados


@app.cell(hide_code=True)
def _(Statevector, SparsePauliOp, bell, mo, np, plt, valores_esperados, veredicto):
    _etiquetas = ["ZZ", "XX", "YY", "ZI", "IZ"]
    _evs = np.asarray(valores_esperados(bell, _etiquetas), dtype=float)
    _esperado = [Statevector(bell).expectation_value(SparsePauliOp(_l)).real for _l in _etiquetas]
    _ok = _evs.shape == (5,) and bool(np.allclose(_evs, _esperado, atol=1e-6))
    _v = veredicto(_ok,
                   "Bell: $\\langle ZZ\\rangle = \\langle XX\\rangle = 1$, $\\langle YY\\rangle = -1$ y los de un solo qubit valen 0.",
                   "Los valores no coinciden con los del estado de Bell. Esperaba ZZ = 1, XX = 1, YY = −1, ZI = IZ = 0.")
    _fig, _ax = plt.subplots(figsize=(5, 2.6))
    _ax.bar(_etiquetas, _evs, color="teal")
    _ax.set_ylim(-1.1, 1.1)
    _ax.axhline(0, color="gray", lw=0.5)
    mo.vstack([_v, _fig])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** en la gráfica, ¿por qué los términos de un solo qubit valen 0 en un
    estado de Bell, y qué te diría eso si solo miraras las esferas de Bloch?
    """)
    return


if __name__ == "__main__":
    app.run()
