import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="5.4 · Estimator en IBM Quantum")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.executor_estimator import Estimator
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    backend = FakeManilaV2()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)

    def estimator_local(shots=1000):
        est = Estimator(mode=backend)
        est.options.default_shots = shots
        est.options.simulator.seed_simulator = 7
        return est

    mo.md("""

    Tres misiones con `Estimator` sobre `FakeManilaV2`, un procesador falso de 5 qubits:
    la forma de los resultados, la precisión y el experimento CHSH. No necesitas cuenta.
    """)
    return (
        Parameter,
        QuantumCircuit,
        SparsePauliOp,
        estimator_local,
        mo,
        np,
        plt,
        pm,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: 300 valores esperados en una llamada

    Un circuito con dos parámetros, **100** juegos de valores y **3** observables en forma
    `(3, 1)`. Antes de ejecutar, predice la forma de `evs`: ¿`(3, 100)`, `(100, 3)` o `(300,)`?
    """)
    return


@app.cell
def _(Parameter, QuantumCircuit, SparsePauliOp, estimator_local, np, pm):
    a, b = Parameter("a"), Parameter("b")
    circuito = QuantumCircuit(2)
    circuito.rx(a, 0)
    circuito.ry(b, 1)
    circuito.cx(0, 1)
    isa = pm.run(circuito)

    parametros = np.vstack([np.linspace(-np.pi, np.pi, 100),
                            np.linspace(-4 * np.pi, 4 * np.pi, 100)]).T          # (100, 2)
    observables = [[SparsePauliOp(["XX", "IY"], [0.5, 0.5])],
                   [SparsePauliOp("XX")],
                   [SparsePauliOp("IY")]]                                         # (3, 1)
    mapeados = [[o.apply_layout(isa.layout) for o in fila] for fila in observables]

    evs = estimator_local(200).run([(isa, mapeados, parametros)]).result()[0].data.evs
    evs.shape
    return (evs,)


@app.cell(hide_code=True)
def _(evs, veredicto):
    veredicto(evs.shape == (3, 100),
              "`evs` tiene forma `(3, 100)`: observables `(3, 1)` y parámetros `(100,)` se combinan por *broadcasting*.",
              f"Salió {evs.shape}; esperábamos (3, 100).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: pide una precisión

    La precisión puede venir de varios sitios, y gana el primero de la lista: el PUB, el
    argumento `precision` de `run`, el twirling, `default_shots`, `default_precision`.
    Aquí `default_precision` y `precision` valen $0{,}05$. Cambia **una** línea para que el
    error estándar de $\\langle ZZ\\rangle$ baje de $0{,}008$. Pista: ¿cuál de las dos gana?
    """)
    return


@app.cell
def _(QuantumCircuit, SparsePauliOp, estimator_local, pm):
    _bell = QuantumCircuit(2)
    _bell.h(0)
    _bell.cx(0, 1)
    _isa = pm.run(_bell)
    _zz = SparsePauliOp("ZZ").apply_layout(_isa.layout)

    _est = estimator_local(None)
    _est.options.default_precision = 0.05
    _datos = _est.run([(_isa, _zz)], precision=0.05).result()[0].data   # ✏️ ¿qué precisión gana?
    error_zz = float(_datos.stds)
    f"⟨ZZ⟩ = {float(_datos.evs):.3f} ± {error_zz:.4f}"
    return (error_zz,)


@app.cell(hide_code=True)
def _(error_zz, veredicto):
    veredicto(error_zz < 0.008,
              f"El error es {error_zz:.4f}. En hardware, esa precisión se paga con tiempo de QPU.",
              f"El error es {error_zz:.4f}; todavía no baja de 0,008.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la desigualdad CHSH

    Un estado de Bell con una rotación $R_Y(\\theta)$ en el qubit 0 se mide con cuatro
    observables. La celda de abajo ya ejecuta el experimento y te da `evs` con forma
    `(4, 21)`: filas `ZZ, ZX, XZ, XX`, columnas los 21 ángulos.

    Escribe `valor_S(evs)`: devuelve el arreglo de 21 valores de
    $S = \\langle ZZ\\rangle - \\langle ZX\\rangle + \\langle XZ\\rangle + \\langle XX\\rangle$.
    Un modelo clásico no pasa de $|S| \\le 2$; con entrelazamiento se llega hasta $2\\sqrt2 \\approx 2{,}83$.
    """)
    return


@app.cell
def _(Parameter, QuantumCircuit, SparsePauliOp, estimator_local, np, pm):
    theta = Parameter("θ")
    chsh = QuantumCircuit(2)
    chsh.h(0)
    chsh.cx(0, 1)
    chsh.ry(theta, 0)
    isa_chsh = pm.run(chsh)

    angulos = np.linspace(0, 2 * np.pi, 21)
    ops = [[SparsePauliOp(p).apply_layout(isa_chsh.layout)] for p in ["ZZ", "ZX", "XZ", "XX"]]
    evs_chsh = estimator_local(1000).run([(isa_chsh, ops, [[t] for t in angulos])]).result()[0].data.evs

    def valor_S(evs):
        return np.zeros(evs.shape[1])   # ✏️ combina las cuatro filas con los signos de S
    return angulos, evs_chsh, valor_S


@app.cell(hide_code=True)
def _(evs_chsh, np, valor_S, veredicto):
    _S = np.asarray(valor_S(evs_chsh))
    _ref = evs_chsh[0] - evs_chsh[1] + evs_chsh[2] + evs_chsh[3]
    veredicto(_S.shape == _ref.shape and np.allclose(_S, _ref) and np.abs(_S).max() > 2,
              f"|S| llega a {np.abs(_S).max():.2f} > 2: el resultado viola la cota clásica.",
              "Todavía no: `valor_S` debe devolver 21 valores `ZZ − ZX + XZ + XX` y alguno debe superar 2 en valor absoluto.")
    return


@app.cell(hide_code=True)
def _(angulos, evs_chsh, np, plt, valor_S):
    _S = np.asarray(valor_S(evs_chsh))
    _fig, _ax = plt.subplots(figsize=(6, 2.8))
    for _y in (2, -2):
        _ax.axhline(_y, color="gray", ls="--", lw=1)
    _ax.plot(angulos, _S, "o-")
    _ax.set_xlabel("θ")
    _ax.set_ylabel("S")
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** la línea punteada marca $|S| = 2$. ¿Qué te dice que la curva la cruce?
    Y si el ruido fuera mucho mayor, ¿qué pasaría con ese cruce?
    """)
    return


if __name__ == "__main__":
    app.run()
