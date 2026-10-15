import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="2.6 · Observables y síntesis")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.primitives import StatevectorSampler, StatevectorEstimator

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    mo.md("""
    # 2.6 · Observables en la base de Pauli: práctica

    Tres misiones: contar los términos de un hamiltoniano, medir $Y$ con un Sampler y
    escribir el observable de magnetización que usarás en el proyecto Ising.
    """)
    return QuantumCircuit, SparsePauliOp, StatevectorEstimator, StatevectorSampler, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: un hamiltoniano de Ising

    Cuatro espines en línea: $H=\\sum_{i}Z_iZ_{i+1}-\\sum_{i}X_i$. Antes de ejecutar,
    escribe en `prediccion` cuántos términos tendrá.
    """)
    return


@app.cell
def _(SparsePauliOp):
    n = 4
    interacciones = [("ZZ", [i, i + 1], 1) for i in range(n - 1)]
    campo = [("X", [i], -1) for i in range(n)]
    hamiltoniano = SparsePauliOp.from_sparse_list(interacciones + campo, num_qubits=n)

    prediccion = None   # ✏️ tu apuesta: ¿cuántos términos?

    hamiltoniano
    return hamiltoniano, prediccion


@app.cell(hide_code=True)
def _(hamiltoniano, prediccion, veredicto):
    veredicto(prediccion == len(hamiltoniano),
              f"Acertaste: {len(hamiltoniano)} términos, 3 de interacción y 4 de campo.",
              f"Tu apuesta ({prediccion}) no coincide con los {len(hamiltoniano)} términos. "
              "Cuenta los pares de vecinos de una línea de 4 y los qubits.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: medir $Y$ con un Sampler

    El circuito prepara $|{+i}\\rangle$, el autoestado de $Y$ con valor $+1$. Un Sampler solo
    mide en la base $Z$, así que antes de medir hay que cambiar de base: $S^\\dagger$ y luego $H$
    (`sdg` y `h`). Añádelas. Si lo haces bien, el bit siempre sale `0` (valor $+1$).
    """)
    return


@app.cell
def _(QuantumCircuit, StatevectorSampler):
    medir_y = QuantumCircuit(1)
    medir_y.h(0)
    medir_y.s(0)       # prepara |+i⟩
    # ✏️ cambio de base para medir Y
    medir_y.measure_all()

    conteos_y = StatevectorSampler(seed=7).run([medir_y], shots=512).result()[0].data.meas.get_counts()
    conteos_y
    return (conteos_y,)


@app.cell(hide_code=True)
def _(conteos_y, veredicto):
    veredicto(set(conteos_y) == {"0"},
              "Siempre `0`: mediste $\\langle Y\\rangle = +1$ con un Sampler.",
              f"Salen {sorted(conteos_y)}. Sin el cambio de base, medir $|{{+i}}\\rangle$ en $Z$ da 0 o 1 al azar.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: el observable de magnetización

    Escribe `magnetizacion(n, eje)` que devuelva el `SparsePauliOp` de $n$ qubits
    $M_\\text{eje}=\\tfrac1n\\sum_i \\sigma_i^\\text{eje}$, donde `eje` es `"Z"` o `"X"`.
    Lo usarás en el hito II para seguir la cadena de espines.

    La comprobación lo evalúa con Estimator sobre tres estados de 4 qubits.
    """)
    return


@app.cell
def _(SparsePauliOp):
    def magnetizacion(n, eje="Z"):
        terminos = []
        # ✏️ una tripleta (eje, [i], 1 / n) por cada qubit
        return SparsePauliOp.from_sparse_list(terminos, num_qubits=n)
    return (magnetizacion,)


@app.cell(hide_code=True)
def _(QuantumCircuit, StatevectorEstimator, magnetizacion, np, veredicto):
    def _valor(qc, obs):
        return float(StatevectorEstimator().run([(qc, obs)]).result()[0].data.evs)

    _todos_cero = QuantumCircuit(4)
    _uno_arriba = QuantumCircuit(4)
    _uno_arriba.x(0)
    _todos_x = QuantumCircuit(4)
    _todos_x.h(range(4))
    _ok = len(magnetizacion(4)) == 4 and np.allclose(
        [_valor(_todos_cero, magnetizacion(4)), _valor(_uno_arriba, magnetizacion(4)),
         _valor(_todos_x, magnetizacion(4, "X")), _valor(_todos_x, magnetizacion(4, "Z"))],
        [1.0, 0.5, 1.0, 0.0])
    veredicto(_ok,
              "$M_Z=1$ con todos en $|0\\rangle$, $0.5$ con un espín volteado, y $M_X=1$ con todos en $|+\\rangle$.",
              "Esperaba $M_Z=1$ en $|0000\\rangle$, $0.5$ con una X en el qubit 0, y $M_X=1$, $M_Z=0$ en $|{+}{+}{+}{+}\\rangle$.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** ¿por qué $M_Z$ vale 0 en $|{+}{+}{+}{+}\\rangle$ aunque cada espín esté
    perfectamente definido en $X$?
    """)
    return


if __name__ == "__main__":
    app.run()
