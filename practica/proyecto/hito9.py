import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Proyecto Ising · Hito IX")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    from scipy.linalg import expm
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    def veredicto(ok, si, no):
        return mo.callout(mo.md(("✅ " + si) if ok else ("❌ " + no)), kind="success" if ok else "warn")

    import ising

    mo.md("""
    # Proyecto Ising · Hito IX: migrar a las primitivas del lado del cliente

    Hasta ahora el proyecto usó funciones sueltas y `StatevectorEstimator`. Este hito
    hace dos cosas:

    1. **Migra** la ejecución a `executor_estimator.Estimator` y `executor_sampler.Sampler`,
       las primitivas del lado del cliente de `qiskit-ibm-runtime`. Con un backend falso
       corren en tu equipo; con un backend real, un `Batch` o una `Session`, el mismo código
       envía el trabajo.
    2. **Empaqueta** el código en un módulo que puedes importar: `practica/proyecto/ising.py`.
       El hito X lo usará para el informe final.

    Antes de migrar, **recalculas** lo que hicieron los hitos anteriores (el Hamiltoniano, el
    circuito de $N$ pasos, la magnetización, la curva exacta y la profundidad transpilada),
    para tener contra qué comparar.
    """)
    return (
        FakeManilaV2,
        QuantumCircuit,
        SparsePauliOp,
        StatevectorEstimator,
        expm,
        generate_preset_pass_manager,
        ising,
        mo,
        np,
        veredicto,
    )


@app.cell(hide_code=True)
def _(mo):
    J = mo.ui.slider(0.0, 2.0, step=0.1, value=1.0, label="J (acoplamiento ZZ)", show_value=True)
    h = mo.ui.slider(0.0, 2.0, step=0.1, value=1.0, label="h (campo transversal)", show_value=True)
    dt = mo.ui.slider(0.05, 0.5, step=0.05, value=0.2, label="dt (paso de tiempo)", show_value=True)
    mo.vstack([mo.md("## Parámetros\nCadena de **4 espines** y **8 pasos**. Muévelos cuando termines las misiones."), J, h, dt])
    return J, dt, h


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟢 Reproduce: los hitos II a IV, recalculados

    Mismo código de los hitos anteriores: $H = J\\sum Z_iZ_{i+1} + h\\sum X_i$ como
    `SparsePauliOp`, un circuito de $k$ pasos de Trotter, el observable
    $M=\\tfrac1N\\sum Z_i$, la curva exacta con `expm` y la ejecución ideal con
    `StatevectorEstimator`. Ejecuta y no cambies nada.
    """)
    return


@app.cell
def _(
    FakeManilaV2,
    J,
    QuantumCircuit,
    SparsePauliOp,
    StatevectorEstimator,
    dt,
    expm,
    generate_preset_pass_manager,
    h,
    np,
):
    N, PASOS = 4, 8
    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J.value) for i in range(N - 1)] + [("X", [i], h.value) for i in range(N)],
        num_qubits=N)
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / N) for i in range(N)], num_qubits=N)

    def trotter(k):
        qc = QuantumCircuit(N)
        for _ in range(k):
            for i in range(N - 1):
                qc.rzz(2 * J.value * dt.value, i, i + 1)
            for i in range(N):
                qc.rx(2 * h.value * dt.value, i)
        return qc

    _U = expm(-1j * H.to_matrix() * dt.value)
    _psi = np.zeros(2**N, dtype=complex)
    _psi[0] = 1
    exacta = []
    for _ in range(PASOS + 1):
        exacta.append(float(np.real(np.vdot(_psi, M.to_matrix() @ _psi))))
        _psi = _U @ _psi

    ideal = [float(r.data.evs) for r in StatevectorEstimator().run([(trotter(k), M) for k in range(PASOS + 1)]).result()]
    _pm = generate_preset_pass_manager(1, backend=FakeManilaV2(), seed_transpiler=1)
    profundidad = [_pm.run(trotter(k)).depth() for k in range(PASOS + 1)]
    {"exacta": [round(v, 3) for v in exacta], "ideal": [round(v, 3) for v in ideal], "profundidad": profundidad}
    return M, N, PASOS, exacta, ideal, profundidad, trotter


@app.cell(hide_code=True)
def _(exacta, ideal, np, profundidad, veredicto):
    _err = float(np.max(np.abs(np.array(exacta) - np.array(ideal))))
    veredicto(_err < 0.1 and all(a < b for a, b in zip(profundidad, profundidad[1:])),
              f"Trotter se separa de la curva exacta como mucho {_err:.3f}, y la profundidad crece con cada paso (de {profundidad[0]} a {profundidad[-1]}).",
              "Algo no cuadra: Trotter debería seguir la curva exacta y la profundidad crecer con los pasos.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🟡 Modifica: migra al Estimator del lado del cliente

    La celda de abajo ejecuta la misma curva con el `Estimator` de siempre. Con
    `FakeManilaV2` corre en local, pero Python avisa de que está obsoleto. Cambia **solo la
    importación** por la del lado del cliente: `from qiskit_ibm_runtime.executor_estimator import Estimator`.

    Fíjate en lo que no cambia: `mode`, `run([(circuito, observable)])`, el formato de los
    PUBs y `data.evs`.
    """)
    return


@app.cell
def _(FakeManilaV2, M, N, PASOS, generate_preset_pass_manager, trotter):
    from qiskit_ibm_runtime import EstimatorV2 as Estimator   # ✏️ importa el Estimator del lado del cliente

    backend = FakeManilaV2()
    estimador = Estimator(mode=backend)
    _pm = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1)
    _isas = [_pm.run(trotter(k)) for k in range(PASOS + 1)]
    medida = [float(r.data.evs) for r in estimador.run([(isa, M.apply_layout(isa.layout)) for isa in _isas]).result()]
    [round(v, 3) for v in medida]
    return backend, estimador, medida


@app.cell(hide_code=True)
def _(estimador, ideal, medida, np, veredicto):
    _err = float(np.max(np.abs(np.array(medida) - np.array(ideal))))
    veredicto(type(estimador).__module__.startswith("qiskit_ibm_runtime.executor_estimator") and _err < 0.15,
              f"Usas `executor_estimator.Estimator`. Con el ruido del backend falso, la curva se separa de la ideal como mucho {_err:.3f}.",
              f"El Estimator viene de `{type(estimador).__module__}`; debe venir de `qiskit_ibm_runtime.executor_estimator`.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 🔴 Crea: la magnetización desde un Sampler

    El `Sampler` del lado del cliente devuelve conteos de bits, no valores esperados. Escribe
    `magnetizacion_conteos(conteos, n)`: cada bit `0` aporta $+1$ (espín arriba) y cada bit
    `1` aporta $-1$; devuelve la media sobre los $n$ espines y los disparos. Para
    `{"00": 3, "11": 1}` con $n=2$ da $0{,}5$.

    Luego se ejecuta con `executor_sampler.Sampler` (el módulo `ising` lo crea con
    `ising.sampler`) sobre el mismo backend falso y se compara con tu Estimator.
    """)
    return


@app.cell
def _():
    def magnetizacion_conteos(conteos, n):
        # ✏️ tu código aquí
        return 0.0
    return (magnetizacion_conteos,)


@app.cell
def _(N, PASOS, backend, generate_preset_pass_manager, ising, magnetizacion_conteos, trotter):
    _qc = trotter(PASOS)
    _qc.measure_all()
    _isa = generate_preset_pass_manager(1, backend=backend, seed_transpiler=1).run(_qc)
    conteos = ising.sampler(backend).run([_isa], shots=4000).result()[0].data.meas.get_counts()
    desde_sampler = magnetizacion_conteos(conteos, N)
    desde_sampler
    return conteos, desde_sampler


@app.cell(hide_code=True)
def _(desde_sampler, magnetizacion_conteos, medida, veredicto):
    _casos = [({"00": 3, "11": 1}, 2, 0.5), ({"000": 5, "111": 5}, 3, 0.0), ({"0100": 1, "0000": 1, "1110": 2}, 4, 0.125)]
    _ok = all(abs(magnetizacion_conteos(c, n) - esperado) < 1e-12 for c, n, esperado in _casos)
    veredicto(_ok and abs(desde_sampler - medida[-1]) < 0.15,
              f"Tu función da los valores esperados. El Sampler da {desde_sampler:.3f} y el Estimator {medida[-1]:.3f} en el último paso.",
              "`magnetizacion_conteos` no da los valores esperados (0,5 · 0 · 0,125), o el Sampler y el Estimator se separan demasiado.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 📦 El módulo `ising`

    Todo lo anterior vive ahora en `practica/proyecto/ising.py`: `hamiltoniano`, `circuito`,
    `magnetizacion`, `exacta`, `estimador`, `sampler` y `curva`. La celda siguiente lo
    usa y compara su resultado con lo que calculaste arriba. Tu `magnetizacion_conteos`
    aún vive en el cuaderno: súbela a `ising.py` cuando quieras reutilizarla en el informe.
    """)
    return


@app.cell
def _(J, N, PASOS, backend, dt, h, ising):
    modulo_exacta = ising.exacta(N, J.value, h.value, dt.value, PASOS)
    modulo_curva = ising.curva(ising.estimador(backend), backend, N, PASOS, J.value, h.value, dt.value)
    [round(v, 3) for v in modulo_curva]
    return modulo_curva, modulo_exacta


@app.cell(hide_code=True)
def _(exacta, ideal, medida, modulo_curva, modulo_exacta, np, veredicto):
    veredicto(np.allclose(modulo_exacta, exacta) and float(np.max(np.abs(np.array(modulo_curva) - np.array(ideal)))) < 0.15
              and float(np.max(np.abs(np.array(modulo_curva) - np.array(medida)))) < 0.15,
              "El módulo reproduce tus resultados: misma curva exacta y la misma curva medida con el Estimator del lado del cliente.",
              "El módulo `ising` no coincide con tus resultados.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    **Para pensar:** este hito no cambió la física, solo el código que la ejecuta. ¿Qué
    ventaja tiene que `ising.curva` reciba el estimador como argumento en lugar de crearlo
    dentro? Piensa en el hito VII, con modo `Batch`, y en el X, con el informe.
    """)
    return


if __name__ == "__main__":
    app.run()
