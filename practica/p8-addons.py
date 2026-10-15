import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="8.2 · Qiskit addons")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit_addon_obp import backpropagate
    from qiskit_addon_obp.utils.simplify import OperatorBudget
    from qiskit_addon_utils.slicing import combine_slices, slice_by_gate_types

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 8.2 · Qiskit addons: práctica

    Tres misiones con la retropropagación de operadores (OBP), el addon que acorta el
    circuito a cambio de un observable más grande. Usas una cadena de 6 espines de Ising con
    4 pasos de Trotter, que se simula exacta en tu equipo. Busca el ✅ en cada misión.
    """)
    return (OperatorBudget, QuantumCircuit, SparsePauliOp, Statevector, backpropagate,
            combine_slices, mo, np, slice_by_gate_types, veredicto)


@app.cell
def _(QuantumCircuit, SparsePauliOp, Statevector, combine_slices, np, slice_by_gate_types):
    n, pasos, J, h, dt = 6, 4, 1.0, 0.5, 0.2

    circuito = QuantumCircuit(n)
    for _ in range(pasos):
        for k in range(0, n - 1, 2):
            circuito.rzz(2 * J * dt, k, k + 1)
        for k in range(1, n - 1, 2):
            circuito.rzz(2 * J * dt, k, k + 1)
        for k in range(n):
            circuito.rx(2 * h * dt, k)

    magnetizacion = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    capas = slice_by_gate_types(circuito)   # cada capa es una columna de puertas del mismo tipo

    def valor(circ, obs):
        return float(np.real(Statevector(circ).expectation_value(obs)))

    def reducido(obs, resto):
        """El circuito que queda tras la retropropagación y su valor esperado con el observable nuevo."""
        circ = combine_slices(resto, include_barriers=False) if resto else QuantumCircuit(n)
        return circ, valor(circ, obs)

    print(f"{len(capas)} capas · profundidad {circuito.depth()} · valor {valor(circuito, magnetizacion):.6f}")
    return capas, circuito, magnetizacion, n, reducido, valor


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: absorber 4 capas en el observable

    `backpropagate` recibe el observable y las capas que quieres absorber, y las pasa de
    la última a la primera. Devuelve el observable nuevo y las capas que **no** absorbió. Antes
    de ejecutar, apuesta: ¿cuántos términos tendrá el observable?
    """)
    return


@app.cell
def _(backpropagate, capas, circuito, magnetizacion, reducido):
    obs4, resto4, _meta = backpropagate(magnetizacion, capas[-4:])
    circ4, valor4 = reducido(obs4, capas[:-4] + list(resto4))

    print(f"términos: {len(magnetizacion)} → {len(obs4)}")
    print(f"profundidad: {circuito.depth()} → {circ4.depth()}")
    print(f"valor con el circuito corto: {valor4:.6f}")
    return circ4, obs4, valor4


@app.cell(hide_code=True)
def _(circ4, circuito, magnetizacion, obs4, valor, valor4, veredicto):
    veredicto(len(obs4) == 64 and circ4.depth() == circuito.depth() - 4
              and abs(valor4 - valor(circuito, magnetizacion)) < 1e-6,
              "Un circuito 4 capas más corto, un observable con 64 términos y el mismo valor.",
              "Deberían salir 64 términos, profundidad 8 y el mismo valor esperado que el circuito completo.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: que OBP se detenga solo

    Elegir cuántas capas absorber a mano es incómodo. `OperatorBudget` fija un límite al tamaño del
    observable, y `backpropagate` se detiene antes de pasarlo. La celda de abajo le pasa
    **todas** las capas sin límite, y el observable explota. Pon un presupuesto de **100
    términos** (`max_paulis=100`).
    """)
    return


@app.cell
def _(OperatorBudget, backpropagate, capas, magnetizacion, reducido):
    presupuesto = None   # ✏️ un OperatorBudget con max_paulis=100

    obs_b, resto_b, _meta_b = backpropagate(magnetizacion, capas, operator_budget=presupuesto)
    circ_b, valor_b = reducido(obs_b, list(resto_b))
    print(f"términos: {len(obs_b)} · profundidad restante: {circ_b.depth()} · valor: {valor_b:.6f}")
    return circ_b, obs_b, valor_b


@app.cell(hide_code=True)
def _(circ_b, circuito, magnetizacion, obs_b, valor, valor_b, veredicto):
    veredicto(len(obs_b) <= 100 and circ_b.depth() < circuito.depth() - 3
              and abs(valor_b - valor(circuito, magnetizacion)) < 1e-6,
              f"OBP absorbió {circuito.depth() - circ_b.depth()} capas y paró con {len(obs_b)} términos, sin perder exactitud.",
              f"El observable tiene {len(obs_b)} términos. Necesito como máximo 100 y el mismo valor esperado.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la mejor cantidad de capas

    Escribe `mejor_k(limite)`: el mayor número de capas finales que se pueden absorber sin
    que el observable pase de `limite` términos. Prueba con `backpropagate(magnetizacion,
    capas[-k:])` para cada `k`. Si ni siquiera una capa cabe, devuelve 0.
    """)
    return


@app.cell
def _(backpropagate, capas, magnetizacion):
    def mejor_k(limite):
        # ✏️ recorre k = 1, 2, … y quédate con el último que no supera `limite`
        return 0
    return (mejor_k,)


@app.cell(hide_code=True)
def _(mejor_k, veredicto):
    _r = {limite: mejor_k(limite) for limite in (10, 30, 100)}
    veredicto(_r == {10: 0, 30: 3, 100: 5},
              "Con 30 términos caben 3 capas; con 100, 5. Es la curva «profundidad frente a términos».",
              f"Tu función da {_r}. Con límite 10 espero 0; con 30, 3; con 100, 5.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** cada capa absorbida acorta el circuito, pero el observable crece y hay
    que medir más términos. ¿Cuándo deja de compensar? En el hito VIII del proyecto Ising
    medirás el ahorro en un backend real simulado.
    """)
    return


if __name__ == "__main__":
    app.run()
