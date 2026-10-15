import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="4.3 · Simulación exacta")


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

    Tres misiones con las primitivas de referencia: valores exactos, ruido de muestreo
    controlado y disparos por PUB. Busca el ✅ en cada una.
    """)
    return Parameter, QuantumCircuit, SparsePauliOp, StatevectorEstimator, StatevectorSampler, mo, np, veredicto


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: valores esperados exactos

    El circuito y el observable de la lección. Ejecuta y compara con los tres números
    que apostaste.
    """)
    return


@app.cell
def _(Parameter, QuantumCircuit, SparsePauliOp, StatevectorEstimator, np):
    circuito = QuantumCircuit(2)
    circuito.ry(Parameter("theta"), 0)
    circuito.h(0)
    circuito.cx(0, 1)
    observable = SparsePauliOp(["II", "XX", "YY", "ZZ"], coeffs=[1, 1, -1, 1])
    valores = [[0], [np.pi / 6], [np.pi / 2]]

    exacto = StatevectorEstimator().run([(circuito, observable, valores)]).result()[0].data.evs
    print(exacto)
    return circuito, exacto, observable, valores


@app.cell(hide_code=True)
def _(exacto, np, veredicto):
    veredicto(np.allclose(exacto, [4, 2 + np.sqrt(3), 2]),
              "Los valores son 4, $2+\\sqrt3\\approx 3.732$ y 2: exactos, sin error de muestreo.",
              "Deberían salir 4, 3.732 y 2. ¿Cambiaste el circuito o el observable?")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: cuánto ruido de muestreo

    `precision` introduce el error estadístico de un experimento real. Ahora vale 0.5 y los
    valores se alejan mucho de los exactos. Cambia **solo** `precision` para que el error
    máximo sea menor que 0.02, pero no cero: sigue siendo una simulación con ruido.
    """)
    return


@app.cell
def _(StatevectorEstimator, circuito, exacto, np, observable, valores):
    precision = 0.5   # ✏️ elige un valor menor

    ruidoso = StatevectorEstimator(seed=1).run([(circuito, observable, valores)], precision=precision).result()[0].data.evs
    error_max = float(np.abs(ruidoso - exacto).max())
    print(ruidoso, f"· error máximo {error_max:.4f}")
    return (error_max,)


@app.cell(hide_code=True)
def _(error_max, veredicto):
    veredicto(0 < error_max < 0.02,
              f"Error máximo {error_max:.4f}: cerca de lo exacto, pero con ruido de muestreo.",
              f"El error máximo es {error_max:.4f}. Busca que quede entre 0 y 0.02.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: cuántos disparos hacen falta

    Estima $P(1)$ de un qubit con $R_y(1)$, cuyo valor exacto es $\\sin^2(0.5)$, con 100,
    1 000, 10 000 y 100 000 disparos **en una sola llamada a `run`**: un PUB por
    cada cantidad, con los disparos como tercer elemento de la tupla. Luego guarda en
    `errores` la diferencia absoluta con el valor exacto de cada PUB.
    """)
    return


@app.cell
def _(QuantumCircuit, StatevectorSampler, np):
    qubit = QuantumCircuit(1)
    qubit.ry(1.0, 0)
    qubit.measure_all()
    disparos = [100, 1000, 10_000, 100_000]
    p1_exacto = np.sin(0.5) ** 2

    pubs = []   # ✏️ un PUB (circuito, None, disparos) por cada cantidad
    resultado = StatevectorSampler(seed=11).run(pubs).result() if pubs else []

    errores = []   # ✏️ |P(1) estimada − p1_exacto| de cada PUB, con get_counts()
    print([round(float(e), 4) for e in errores])
    return disparos, errores, resultado


@app.cell(hide_code=True)
def _(disparos, errores, resultado, veredicto):
    _ok = (len(resultado) == 4 and len(errores) == 4
           and [r.data.meas.num_shots for r in resultado] == disparos and errores[-1] < 0.005)
    veredicto(_ok,
              "Cuatro PUBs en una llamada, con sus disparos propios; con 100 000 el error ya es minúsculo.",
              "Faltan los cuatro PUBs con 100, 1000, 10000 y 100000 disparos, y sus cuatro errores.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** cada error es un solo sorteo, así que con 1 000 disparos puede salir mayor
    que con 100. ¿Cómo medirías que el error baja como $1/\\sqrt{N}$?
    """)
    return


if __name__ == "__main__":
    app.run()
